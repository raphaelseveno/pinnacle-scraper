"""
FastMCP Management Server for Project Acheron
Provides remote management tools via Model Context Protocol
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

import redis.asyncio as redis
import yaml
from fastmcp import FastMCP
from loguru import logger

# Initialize FastMCP server
mcp = FastMCP("Acheron Manager")

# Global state
_config: Optional[Dict] = None
_redis_client: Optional[redis.Redis] = None
_scraper_process: Optional[subprocess.Popen] = None


async def get_config() -> Dict:
    """Load configuration from YAML"""
    global _config
    if _config is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, 'r') as f:
            _config = yaml.safe_load(f)
    return _config


async def get_redis() -> redis.Redis:
    """Get Redis client connection"""
    global _redis_client
    if _redis_client is None:
        config = await get_config()
        redis_config = config['redis']
        _redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', redis_config['host']),
            port=int(os.getenv('REDIS_PORT', redis_config['port'])),
            db=redis_config['db'],
            password=redis_config.get('password'),
            decode_responses=True
        )
    return _redis_client


def is_scraper_running() -> bool:
    """Check if scraper process is running"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'src/main.py'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


@mcp.tool()
async def scraper_status() -> Dict[str, Any]:
    """
    Check the current status of the Acheron scraper

    Returns:
        Dictionary containing:
        - running: bool - Whether scraper is running
        - uptime_hours: float - How long it's been running
        - odds_updates: int - Number of odds processed
        - alerts_today: int - Arbitrage alerts sent today
        - websocket_connected: bool - WebSocket connection status
        - redis_connected: bool - Redis connection status
        - last_update: str - Timestamp of last odds update
    """
    try:
        status = {
            "running": is_scraper_running(),
            "uptime_hours": 0.0,
            "odds_updates": 0,
            "alerts_today": 0,
            "websocket_connected": False,
            "redis_connected": False,
            "last_update": None
        }

        # Try to get stats from Redis
        try:
            r = await get_redis()
            await r.ping()
            status["redis_connected"] = True

            # Get scraper stats from Redis
            stats_key = "acheron:stats"
            stats = await r.hgetall(stats_key)

            if stats:
                status["odds_updates"] = int(stats.get('total_odds_updates', 0))
                status["websocket_connected"] = stats.get('websocket_status') == 'connected'
                status["last_update"] = stats.get('last_update_time')

                # Calculate uptime
                start_time = stats.get('start_time')
                if start_time:
                    start_dt = datetime.fromisoformat(start_time)
                    uptime = datetime.now() - start_dt
                    status["uptime_hours"] = uptime.total_seconds() / 3600

            # Count today's alerts
            alerts_key = "acheron:alerts:*"
            today = datetime.now().strftime('%Y-%m-%d')
            alert_keys = await r.keys(f"acheron:alerts:{today}:*")
            status["alerts_today"] = len(alert_keys)

        except Exception as e:
            logger.warning(f"Could not fetch Redis stats: {e}")

        return status

    except Exception as e:
        return {
            "error": str(e),
            "running": False
        }


@mcp.tool()
async def scraper_start() -> str:
    """
    Start the Acheron scraper

    Returns:
        Success/failure message
    """
    try:
        if is_scraper_running():
            return "❌ Scraper is already running"

        # Start the scraper as a background process
        log_file = Path(__file__).parent.parent / "logs" / "acheron.log"
        log_file.parent.mkdir(exist_ok=True)

        process = subprocess.Popen(
            [sys.executable, "src/main.py"],
            cwd=Path(__file__).parent.parent,
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        # Wait a bit to check if it started successfully
        await asyncio.sleep(3)

        if is_scraper_running():
            return "✅ Acheron scraper started successfully\n📊 Monitoring NHL odds on Pinnacle\n🔔 Notifications enabled"
        else:
            return "❌ Failed to start scraper. Check logs for details."

    except Exception as e:
        return f"❌ Error starting scraper: {str(e)}"


@mcp.tool()
async def scraper_stop() -> str:
    """
    Stop the Acheron scraper gracefully

    Returns:
        Success/failure message
    """
    try:
        if not is_scraper_running():
            return "⚠️  Scraper is not running"

        # Send SIGTERM for graceful shutdown
        subprocess.run(['pkill', '-TERM', '-f', 'src/main.py'])

        # Wait for shutdown
        await asyncio.sleep(5)

        if not is_scraper_running():
            return "✅ Acheron scraper stopped successfully"
        else:
            # Force kill if still running
            subprocess.run(['pkill', '-KILL', '-f', 'src/main.py'])
            return "⚠️  Scraper force-stopped (was unresponsive to graceful shutdown)"

    except Exception as e:
        return f"❌ Error stopping scraper: {str(e)}"


@mcp.tool()
async def scraper_restart() -> str:
    """
    Restart the Acheron scraper (useful after config changes)

    Returns:
        Success/failure message
    """
    stop_msg = await scraper_stop()
    await asyncio.sleep(2)
    start_msg = await scraper_start()
    return f"{stop_msg}\n{start_msg}"


@mcp.tool()
async def view_alerts(date: str = "today", limit: int = 10) -> List[Dict[str, Any]]:
    """
    View recent arbitrage alerts

    Args:
        date: Date to view alerts for (format: YYYY-MM-DD or "today")
        limit: Maximum number of alerts to return

    Returns:
        List of arbitrage opportunities with details
    """
    try:
        r = await get_redis()

        if date == "today":
            date = datetime.now().strftime('%Y-%m-%d')

        # Get alerts from Redis sorted set
        alerts_key = f"acheron:alerts:{date}"
        alert_data = await r.zrevrange(alerts_key, 0, limit - 1, withscores=True)

        alerts = []
        for alert_json, timestamp in alert_data:
            try:
                alert = json.loads(alert_json)
                alert['timestamp'] = datetime.fromtimestamp(timestamp).isoformat()
                alerts.append(alert)
            except json.JSONDecodeError:
                continue

        if not alerts:
            return [{"message": f"No arbitrage alerts found for {date}"}]

        return alerts

    except Exception as e:
        return [{"error": f"Failed to retrieve alerts: {str(e)}"}]


@mcp.tool()
async def update_config(setting: str, value: Any) -> str:
    """
    Update configuration setting

    Args:
        setting: Setting path (e.g., "notifications.thresholds.min_profit_percent")
        value: New value for the setting

    Returns:
        Success/failure message
    """
    try:
        config_path = Path(__file__).parent.parent / "config.yaml"

        # Load current config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Navigate to nested setting
        keys = setting.split('.')
        current = config
        for key in keys[:-1]:
            if key not in current:
                return f"❌ Invalid setting path: {setting}"
            current = current[key]

        # Update value
        old_value = current.get(keys[-1])
        current[keys[-1]] = value

        # Save config
        with open(config_path, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False)

        # Invalidate cached config
        global _config
        _config = None

        return f"✅ Updated {setting}: {old_value} → {value}\n⚠️  Restart scraper for changes to take effect"

    except Exception as e:
        return f"❌ Error updating config: {str(e)}"


@mcp.tool()
async def view_logs(lines: int = 50, level: str = "all") -> str:
    """
    View recent log entries

    Args:
        lines: Number of log lines to return
        level: Filter by log level (all, info, warning, error)

    Returns:
        Recent log entries as formatted string
    """
    try:
        log_file = Path(__file__).parent.parent / "logs" / "acheron.log"

        if not log_file.exists():
            return "⚠️  No log file found. Scraper may not have been started yet."

        # Read last N lines
        result = subprocess.run(
            ['tail', '-n', str(lines), str(log_file)],
            capture_output=True,
            text=True
        )

        logs = result.stdout

        # Filter by level if requested
        if level != "all":
            filtered_lines = []
            for line in logs.split('\n'):
                if level.upper() in line:
                    filtered_lines.append(line)
            logs = '\n'.join(filtered_lines)

        return logs if logs else f"No {level} logs found in last {lines} lines"

    except Exception as e:
        return f"❌ Error reading logs: {str(e)}"


@mcp.tool()
async def proxy_status() -> Dict[str, Any]:
    """
    Check proxy provider status and credit balance

    Returns:
        Dictionary with proxy provider info and balance
    """
    try:
        config = await get_config()
        proxy_config = config.get('proxy', {})

        provider = proxy_config.get('provider', 'unknown')

        if provider == 'packetstream':
            # Query PacketStream API for balance
            import httpx

            api_key = os.getenv('PACKETSTREAM_API_KEY') or proxy_config.get('api_key')

            if not api_key or api_key == 'YOUR_PACKETSTREAM_API_KEY':
                return {
                    "provider": "packetstream",
                    "status": "not_configured",
                    "message": "⚠️  PacketStream API key not set"
                }

            # Note: PacketStream doesn't have a public balance API
            # We estimate based on usage tracking in Redis
            r = await get_redis()
            usage_mb = float(await r.get('acheron:proxy_usage_mb') or 0)

            # Estimate: $10 for ~5GB = $0.002/MB
            estimated_cost = usage_mb * 0.002
            estimated_remaining = 10.0 - estimated_cost

            return {
                "provider": "packetstream",
                "status": "active",
                "usage_mb": round(usage_mb, 2),
                "estimated_cost_usd": round(estimated_cost, 2),
                "estimated_balance_usd": round(estimated_remaining, 2),
                "note": "Balance is estimated based on usage tracking"
            }
        else:
            return {
                "provider": provider,
                "status": "unknown",
                "message": f"Provider {provider} monitoring not implemented"
            }

    except Exception as e:
        return {
            "error": str(e),
            "provider": "unknown"
        }


@mcp.tool()
async def redis_query(command: str) -> Any:
    """
    Execute a Redis command for debugging

    Args:
        command: Redis command (e.g., "KEYS acheron:*", "GET key_name")

    Returns:
        Command result
    """
    try:
        r = await get_redis()

        # Parse command
        parts = command.split()
        cmd = parts[0].upper()
        args = parts[1:]

        # Execute common commands
        if cmd == 'KEYS':
            result = await r.keys(args[0] if args else '*')
        elif cmd == 'GET':
            result = await r.get(args[0])
        elif cmd == 'HGETALL':
            result = await r.hgetall(args[0])
        elif cmd == 'ZRANGE':
            result = await r.zrange(args[0], 0, -1, withscores=True)
        elif cmd == 'INFO':
            result = await r.info()
        else:
            return f"❌ Command '{cmd}' not supported. Allowed: KEYS, GET, HGETALL, ZRANGE, INFO"

        return result

    except Exception as e:
        return f"❌ Error executing command: {str(e)}"


@mcp.tool()
async def deploy_update() -> str:
    """
    Pull latest code from git and redeploy (for Railway auto-deploy)

    Returns:
        Deployment status message
    """
    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            cwd=Path(__file__).parent.parent
        )

        if result.returncode != 0:
            return "⚠️  Not a git repository. Updates must be deployed manually."

        # Get current commit
        current = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        ).stdout.strip()

        # Pull latest
        pull_result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        if pull_result.returncode != 0:
            return f"❌ Git pull failed: {pull_result.stderr}"

        # Get new commit
        new = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        ).stdout.strip()

        if current == new:
            return f"✅ Already up to date (commit: {current})"

        # Restart scraper to apply changes
        restart_msg = await scraper_restart()

        return f"✅ Updated from {current} to {new}\n{restart_msg}"

    except Exception as e:
        return f"❌ Error deploying update: {str(e)}"


@mcp.tool()
async def system_info() -> Dict[str, Any]:
    """
    Get system information and resource usage

    Returns:
        Dictionary with system stats
    """
    try:
        import psutil

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()

        # Disk usage
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent
            },
            "platform": sys.platform
        }

    except Exception as e:
        return {"error": f"Failed to get system info: {str(e)}"}


# Expose resources for browsing
@mcp.resource("config://acheron/current")
async def get_current_config() -> str:
    """Get current configuration as YAML"""
    config = await get_config()
    return yaml.safe_dump(config, default_flow_style=False)


if __name__ == "__main__":
    # Run the MCP server
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    logger.info("Starting Acheron MCP Management Server...")

    # Get port from environment (Railway sets this)
    port = int(os.getenv('PORT', 8080))

    # Create FastAPI app for HTTP transport
    app = FastAPI(title="Acheron MCP Server")

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for Railway"""
        return JSONResponse({
            "status": "healthy",
            "service": "acheron-mcp-server",
            "timestamp": datetime.now().isoformat()
        })

    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with server info"""
        return JSONResponse({
            "name": "Acheron MCP Management Server",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "mcp": "/mcp"
            }
        })

    # Mount MCP server
    try:
        # Include MCP routes
        mcp_app = mcp.get_app()
        app.mount("/mcp", mcp_app)
    except Exception as e:
        logger.warning(f"Could not mount MCP app: {e}. Running standalone.")

    # Run server
    logger.info(f"Starting server on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
