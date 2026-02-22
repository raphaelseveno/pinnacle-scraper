"""
Project Acheron - Health Monitor
Self-healing system that monitors component health and triggers recovery actions
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from loguru import logger


class HealthMonitor:
    """
    Monitors system health and triggers recovery actions

    Features:
    - Periodic health checks for all components
    - Dead man's switch (alert if no activity)
    - Automatic component restart on failure
    - System statistics collection and logging
    - Alert notifications for critical failures
    """

    def __init__(self, config: Dict[str, Any], notifier=None):
        self.config = config
        self.monitoring_config = config['monitoring']
        self.notifier = notifier

        # Health check interval
        self.check_interval = self.monitoring_config.get('health_check_interval', 60)
        self.websocket_timeout = self.monitoring_config.get('websocket_timeout', 300)

        # Component references (set via register_component)
        self.components: Dict[str, Any] = {}

        # Health status
        self.component_health: Dict[str, Dict[str, Any]] = {}

        # Recovery callbacks
        self.recovery_callbacks: Dict[str, Callable] = {}

        # Monitor state
        self.is_running = False
        self.last_check_time: Optional[float] = None

        # System stats
        self.system_stats = {
            'uptime_start': datetime.now(),
            'total_health_checks': 0,
            'component_failures': 0,
            'recoveries_triggered': 0,
            'alerts_sent': 0
        }

        logger.info("HealthMonitor initialized")

    def register_component(
        self,
        name: str,
        component: Any,
        recovery_callback: Optional[Callable] = None
    ):
        """
        Register a component for health monitoring

        Args:
            name: Component name ('scout', 'interceptor', 'engine', etc.)
            component: Component instance
            recovery_callback: Async function to call for recovery
        """
        self.components[name] = component
        self.component_health[name] = {
            'status': 'unknown',
            'last_check': None,
            'last_healthy': None,
            'consecutive_failures': 0
        }

        if recovery_callback:
            self.recovery_callbacks[name] = recovery_callback

        logger.info(f"Registered component for monitoring: {name}")

    async def start_monitoring(self):
        """Start the health monitoring loop"""
        self.is_running = True
        logger.info(f"🏥 Starting health monitoring (interval: {self.check_interval}s)")

        while self.is_running:
            try:
                await self._perform_health_checks()
                self.system_stats['total_health_checks'] += 1
                self.last_check_time = datetime.now().timestamp()

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _perform_health_checks(self):
        """Perform health checks on all registered components"""
        logger.debug("Performing health checks...")

        for name, component in self.components.items():
            try:
                is_healthy = await self._check_component_health(name, component)

                if is_healthy:
                    await self._mark_component_healthy(name)
                else:
                    await self._mark_component_unhealthy(name)

            except Exception as e:
                logger.error(f"Error checking health of {name}: {e}")
                await self._mark_component_unhealthy(name)

        # Log summary
        healthy_count = sum(1 for h in self.component_health.values() if h['status'] == 'healthy')
        total_count = len(self.component_health)

        logger.debug(f"Health check complete: {healthy_count}/{total_count} components healthy")

    async def _check_component_health(self, name: str, component: Any) -> bool:
        """
        Check if a component is healthy

        Args:
            name: Component name
            component: Component instance

        Returns:
            bool: True if healthy
        """
        # Scout health check
        if name == 'scout':
            return self._check_scout_health(component)

        # Interceptor health check
        elif name == 'interceptor':
            return self._check_interceptor_health(component)

        # Engine health check
        elif name == 'engine':
            return await self._check_engine_health(component)

        # Notifier health check
        elif name == 'notifier':
            return True  # Notifier failures are non-critical

        # Proxy manager health check
        elif name == 'proxy_manager':
            return self._check_proxy_manager_health(component)

        # Unknown component
        else:
            logger.warning(f"Unknown component type for health check: {name}")
            return True

    def _check_scout_health(self, scout) -> bool:
        """Check Scout health"""
        try:
            # Check if session is valid
            if not hasattr(scout, 'is_session_valid'):
                return False

            is_valid = scout.is_session_valid()

            if not is_valid:
                logger.warning("Scout session is invalid or expired")

            return is_valid

        except Exception as e:
            logger.error(f"Error checking Scout health: {e}")
            return False

    def _check_interceptor_health(self, interceptor) -> bool:
        """Check Interceptor health"""
        try:
            # Check if connected
            if not hasattr(interceptor, 'is_connected'):
                return False

            is_connected = interceptor.is_connected

            # Check if messages are being received
            if hasattr(interceptor, 'last_message_time'):
                last_msg_time = interceptor.last_message_time

                if last_msg_time:
                    time_since_msg = datetime.now().timestamp() - last_msg_time

                    if time_since_msg > self.websocket_timeout:
                        logger.warning(f"No WebSocket messages for {time_since_msg:.0f}s (timeout: {self.websocket_timeout}s)")
                        return False

            return is_connected

        except Exception as e:
            logger.error(f"Error checking Interceptor health: {e}")
            return False

    async def _check_engine_health(self, engine) -> bool:
        """Check Engine health"""
        try:
            # Check if Redis is connected
            if not hasattr(engine, 'redis') or not engine.redis:
                return False

            # Try a simple Redis ping
            try:
                await engine.redis.ping()
                return True
            except:
                logger.warning("Redis connection lost")
                return False

        except Exception as e:
            logger.error(f"Error checking Engine health: {e}")
            return False

    def _check_proxy_manager_health(self, proxy_mgr) -> bool:
        """Check Proxy Manager health"""
        try:
            # Check if proxy pool is available
            if hasattr(proxy_mgr, 'proxy_pool'):
                return len(proxy_mgr.proxy_pool) > 0 or not proxy_mgr.should_use_proxy('authentication')

            return True

        except Exception as e:
            logger.error(f"Error checking Proxy Manager health: {e}")
            return False

    async def _mark_component_healthy(self, name: str):
        """Mark component as healthy"""
        health = self.component_health[name]
        previous_status = health['status']

        health['status'] = 'healthy'
        health['last_check'] = datetime.now().timestamp()
        health['last_healthy'] = datetime.now().timestamp()
        health['consecutive_failures'] = 0

        # If component recovered, log it
        if previous_status == 'unhealthy':
            logger.info(f"✅ {name} recovered and is now healthy")

            if self.notifier:
                await self.notifier.send_system_alert(
                    title=f"{name.capitalize()} Recovered",
                    message=f"Component {name} has recovered and is now healthy",
                    priority=3
                )

    async def _mark_component_unhealthy(self, name: str):
        """Mark component as unhealthy and trigger recovery"""
        health = self.component_health[name]
        previous_status = health['status']

        health['status'] = 'unhealthy'
        health['last_check'] = datetime.now().timestamp()
        health['consecutive_failures'] += 1

        self.system_stats['component_failures'] += 1

        # Log failure
        failures = health['consecutive_failures']
        logger.warning(f"⚠️  {name} is unhealthy (consecutive failures: {failures})")

        # Trigger recovery if callback exists
        if name in self.recovery_callbacks:
            logger.info(f"🔧 Triggering recovery for {name}...")

            try:
                recovery_fn = self.recovery_callbacks[name]
                await recovery_fn()
                self.system_stats['recoveries_triggered'] += 1

            except Exception as e:
                logger.error(f"Recovery failed for {name}: {e}")

        # Send alert if failure persists
        if failures >= 3 and previous_status != 'unhealthy':
            await self._send_failure_alert(name, failures)

    async def _send_failure_alert(self, component_name: str, failure_count: int):
        """Send notification about component failure"""
        if not self.notifier:
            return

        try:
            await self.notifier.send_system_alert(
                title=f"🚨 {component_name.capitalize()} Failure",
                message=f"Component {component_name} has failed {failure_count} consecutive health checks. Manual intervention may be required.",
                priority=4  # High priority
            )

            self.system_stats['alerts_sent'] += 1

        except Exception as e:
            logger.error(f"Failed to send failure alert: {e}")

    def get_component_status(self, name: str) -> Dict[str, Any]:
        """Get health status for a specific component"""
        return self.component_health.get(name, {'status': 'unknown'}).copy()

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all components"""
        return self.component_health.copy()

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        stats = self.system_stats.copy()

        # Calculate uptime
        uptime = datetime.now() - stats['uptime_start']
        stats['uptime_seconds'] = int(uptime.total_seconds())
        stats['uptime_human'] = str(uptime).split('.')[0]  # Remove microseconds

        # Add component summary
        stats['components'] = {
            'total': len(self.component_health),
            'healthy': sum(1 for h in self.component_health.values() if h['status'] == 'healthy'),
            'unhealthy': sum(1 for h in self.component_health.values() if h['status'] == 'unhealthy')
        }

        return stats

    async def log_system_status(self):
        """Log comprehensive system status"""
        stats = self.get_system_stats()

        logger.info(f"📊 System Status:")
        logger.info(f"  Uptime: {stats['uptime_human']}")
        logger.info(f"  Components: {stats['components']['healthy']}/{stats['components']['total']} healthy")
        logger.info(f"  Health checks: {stats['total_health_checks']}")
        logger.info(f"  Failures: {stats['component_failures']}")
        logger.info(f"  Recoveries: {stats['recoveries_triggered']}")

        # Log individual component status
        for name, health in self.component_health.items():
            status_emoji = "✅" if health['status'] == 'healthy' else "❌"
            logger.info(f"  {status_emoji} {name}: {health['status']}")

    async def stop(self):
        """Stop health monitoring"""
        self.is_running = False
        logger.info("Health monitoring stopped")


# Example usage
if __name__ == "__main__":
    import yaml

    async def test():
        # Load config
        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        # Create health monitor
        monitor = HealthMonitor(config)

        # Mock components
        class MockComponent:
            is_connected = True

        # Register mock components
        monitor.register_component('mock1', MockComponent())
        monitor.register_component('mock2', MockComponent())

        # Run monitoring for a bit
        monitor_task = asyncio.create_task(monitor.start_monitoring())

        await asyncio.sleep(10)

        # Log status
        await monitor.log_system_status()

        # Stop
        await monitor.stop()
        monitor_task.cancel()

    asyncio.run(test())
