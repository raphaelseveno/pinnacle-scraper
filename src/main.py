"""
Project Acheron - Main Orchestrator
Coordinates all components for autonomous operation
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional
import yaml
from loguru import logger

# Import our modules
from proxy_manager import ProxyManager
from scout import Scout
from interceptor import Interceptor
from engine import ArbitrageEngine
from notifier import Notifier
from health_monitor import HealthMonitor


class Acheron:
    """
    Main orchestrator for Project Acheron

    Coordinates:
    - Scout (authentication)
    - Interceptor (WebSocket)
    - Engine (arbitrage detection)
    - Notifier (alerts)
    - HealthMonitor (self-healing)
    """

    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        self.config = self._load_config(config_path)

        # Configure logging
        self._configure_logging()

        # Initialize components
        self.proxy_manager: Optional[ProxyManager] = None
        self.notifier: Optional[Notifier] = None
        self.engine: Optional[ArbitrageEngine] = None
        self.scout: Optional[Scout] = None
        self.interceptor: Optional[Interceptor] = None
        self.health_monitor: Optional[HealthMonitor] = None

        # Application state
        self.is_running = False
        self.shutdown_event = asyncio.Event()

        logger.info("🚀 Project Acheron initialized")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            logger.info(f"✅ Configuration loaded from {config_path}")
            return config

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration: {e}")
            sys.exit(1)

    def _configure_logging(self):
        """Configure loguru logger"""
        log_config = self.config['monitoring']['logging']

        # Remove default logger
        logger.remove()

        # Add console logger
        logger.add(
            sys.stderr,
            level=log_config.get('level', 'INFO'),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>"
        )

        # Add file logger
        log_file = log_config.get('file', 'logs/acheron.log')
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            level=log_config.get('level', 'INFO'),
            rotation=f"{log_config.get('max_size_mb', 100)} MB",
            retention=f"{log_config.get('backup_count', 5)} files",
            compression="zip"
        )

        logger.info("Logging configured")

    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing components...")

            # 1. Proxy Manager
            self.proxy_manager = ProxyManager(self.config)
            await self.proxy_manager.initialize()

            # 2. Notifier
            self.notifier = Notifier(self.config)

            # Send test notification
            logger.info("Sending test notification...")
            test_sent = await self.notifier.send_test_notification()
            if test_sent:
                logger.info("✅ Test notification sent successfully")
            else:
                logger.warning("⚠️  Test notification failed (check ntfy.sh topic)")

            # 3. Arbitrage Engine
            self.engine = ArbitrageEngine(self.config, notifier=self.notifier)
            await self.engine.initialize()

            # 4. Scout
            self.scout = Scout(self.config, proxy_manager=self.proxy_manager)
            await self.scout.initialize()

            # 5. Interceptor
            self.interceptor = Interceptor(
                self.config,
                proxy_manager=self.proxy_manager,
                engine=self.engine
            )

            # 6. Health Monitor
            self.health_monitor = HealthMonitor(self.config, notifier=self.notifier)

            # Register components for monitoring
            self.health_monitor.register_component(
                'scout',
                self.scout,
                recovery_callback=self._recover_scout
            )

            self.health_monitor.register_component(
                'interceptor',
                self.interceptor,
                recovery_callback=self._recover_interceptor
            )

            self.health_monitor.register_component(
                'engine',
                self.engine,
                recovery_callback=self._recover_engine
            )

            self.health_monitor.register_component('proxy_manager', self.proxy_manager)
            self.health_monitor.register_component('notifier', self.notifier)

            logger.info("✅ All components initialized")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    async def start(self):
        """Start the application"""
        try:
            self.is_running = True

            logger.info("=" * 60)
            logger.info("🎯 PROJECT ACHERON STARTING")
            logger.info("=" * 60)

            # Step 1: Authenticate
            logger.info("Step 1/4: Authenticating to Pinnacle...")
            auth_success = await self.scout.authenticate()

            if not auth_success:
                logger.error("❌ Authentication failed. Cannot proceed.")
                await self.notifier.send_system_alert(
                    title="🚨 Acheron Startup Failed",
                    message="Failed to authenticate to Pinnacle. Check credentials and proxy settings.",
                    priority=5
                )
                return

            logger.info("✅ Authentication successful")

            # Step 2: Set session data for Interceptor
            logger.info("Step 2/4: Configuring WebSocket connection...")
            session_data = self.scout.get_session_data()
            self.interceptor.set_session_data(session_data)

            logger.info(f"WebSocket URL: {session_data.get('websocket_url')}")
            logger.info(f"Session expires in: {self.scout.time_until_expiry():.0f}s")

            # Step 3: Start Health Monitor
            logger.info("Step 3/4: Starting health monitoring...")
            monitor_task = asyncio.create_task(self.health_monitor.start_monitoring())

            # Step 4: Start Interceptor (WebSocket listener)
            logger.info("Step 4/4: Starting real-time odds feed...")
            interceptor_task = asyncio.create_task(self.interceptor.listen())

            # Start session refresh task
            refresh_task = asyncio.create_task(self._session_refresh_loop())

            # Start periodic status logging
            status_task = asyncio.create_task(self._status_logging_loop())

            logger.info("=" * 60)
            logger.info("✅ PROJECT ACHERON IS RUNNING")
            logger.info("=" * 60)
            logger.info(f"Monitoring: {self.config['sports']['leagues']} | {self.config['sports']['markets']}")
            logger.info(f"Alerts: ntfy.sh/{self.config['notifications']['ntfy']['topic']}")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)

            # Send startup notification
            await self.notifier.send_system_alert(
                title="🚀 Acheron Started",
                message=f"Project Acheron is now running and monitoring {' '.join(self.config['sports']['leagues'])} odds in real-time.",
                priority=3
            )

            # Wait for shutdown signal
            await self.shutdown_event.wait()

            # Cleanup tasks
            logger.info("Shutting down...")
            monitor_task.cancel()
            interceptor_task.cancel()
            refresh_task.cancel()
            status_task.cancel()

            await asyncio.gather(
                monitor_task,
                interceptor_task,
                refresh_task,
                status_task,
                return_exceptions=True
            )

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise

    async def _session_refresh_loop(self):
        """Periodically check and refresh authentication session"""
        try:
            while self.is_running:
                # Check every 5 minutes
                await asyncio.sleep(300)

                if self.scout:
                    logger.info("Checking session status...")
                    refreshed = await self.scout.refresh_session_if_needed()

                    if refreshed and not self.scout.is_session_valid():
                        # Session was refreshed
                        logger.info("Session refreshed, updating Interceptor...")
                        session_data = self.scout.get_session_data()
                        self.interceptor.set_session_data(session_data)

        except asyncio.CancelledError:
            logger.debug("Session refresh loop cancelled")

    async def _status_logging_loop(self):
        """Periodically log system status"""
        try:
            while self.is_running:
                # Log every 30 minutes
                await asyncio.sleep(1800)

                if self.health_monitor:
                    await self.health_monitor.log_system_status()

                # Log component stats
                if self.engine:
                    engine_stats = self.engine.get_stats()
                    logger.info(f"Engine: {engine_stats}")

                if self.interceptor:
                    interceptor_stats = self.interceptor.get_stats()
                    logger.info(f"Interceptor: {interceptor_stats}")

        except asyncio.CancelledError:
            logger.debug("Status logging loop cancelled")

    async def _recover_scout(self):
        """Recovery action for Scout (re-authenticate)"""
        logger.info("Recovering Scout: re-authenticating...")

        try:
            # Close existing browser
            await self.scout.close()

            # Reinitialize
            await self.scout.initialize()

            # Re-authenticate
            success = await self.scout.authenticate()

            if success:
                # Update Interceptor with new session
                session_data = self.scout.get_session_data()
                self.interceptor.set_session_data(session_data)
                logger.info("✅ Scout recovered successfully")
            else:
                logger.error("❌ Scout recovery failed")

        except Exception as e:
            logger.error(f"Error during Scout recovery: {e}")

    async def _recover_interceptor(self):
        """Recovery action for Interceptor (reconnect)"""
        logger.info("Recovering Interceptor: reconnecting...")

        try:
            # Close existing connection
            await self.interceptor.close()

            # Wait a bit
            await asyncio.sleep(5)

            # Try to reconnect
            success = await self.interceptor.connect()

            if success:
                logger.info("✅ Interceptor recovered successfully")
            else:
                logger.error("❌ Interceptor recovery failed")

        except Exception as e:
            logger.error(f"Error during Interceptor recovery: {e}")

    async def _recover_engine(self):
        """Recovery action for Engine (reconnect Redis)"""
        logger.info("Recovering Engine: reconnecting to Redis...")

        try:
            # Close existing connection
            await self.engine.close()

            # Wait a bit
            await asyncio.sleep(2)

            # Reinitialize
            await self.engine.initialize()

            logger.info("✅ Engine recovered successfully")

        except Exception as e:
            logger.error(f"Error during Engine recovery: {e}")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Initiating graceful shutdown...")

        self.is_running = False
        self.shutdown_event.set()

        # Close all components
        if self.interceptor:
            await self.interceptor.close()

        if self.scout:
            await self.scout.close()

        if self.engine:
            await self.engine.close()

        if self.notifier:
            await self.notifier.close()

        if self.health_monitor:
            await self.health_monitor.stop()

        logger.info("✅ Shutdown complete")

        # Send shutdown notification
        if self.notifier:
            await self.notifier.send_system_alert(
                title="🛑 Acheron Stopped",
                message="Project Acheron has shut down.",
                priority=3
            )


def signal_handler(acheron_instance):
    """Handle shutdown signals"""
    def handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(acheron_instance.shutdown())

    return handler


async def main():
    """Main entry point"""
    # Create Acheron instance
    acheron = Acheron()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler(acheron))
    signal.signal(signal.SIGTERM, signal_handler(acheron))

    try:
        # Initialize
        await acheron.initialize()

        # Start
        await acheron.start()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")

    except Exception as e:
        logger.error(f"Fatal error: {e}")

    finally:
        await acheron.shutdown()


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())
