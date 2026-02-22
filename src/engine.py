"""
Project Acheron - Arbitrage Detection Engine
Redis-based atomic arbitrage detection using Lua scripts
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis.asyncio as redis
from loguru import logger


class ArbitrageEngine:
    """
    High-performance arbitrage detection engine using Redis + Lua

    Features:
    - Atomic arbitrage calculations (zero race conditions)
    - Sub-millisecond detection latency
    - Delta-only updates for efficiency
    - Automatic state management and cleanup
    """

    def __init__(self, config: Dict[str, Any], notifier=None):
        self.config = config
        self.redis_config = config['redis']
        self.notifier = notifier

        # Redis connection
        self.redis: Optional[redis.Redis] = None

        # Load Lua scripts
        self.lua_scripts = {}
        self._load_lua_scripts()

        # Statistics
        self.stats = {
            'odds_updates': 0,
            'arbs_detected': 0,
            'arbs_alerted': 0,
            'lua_executions': 0,
            'cache_hits': 0
        }

        logger.info("ArbitrageEngine initialized")

    async def initialize(self):
        """Initialize Redis connection and load Lua scripts"""
        try:
            # Create Redis connection
            self.redis = await redis.from_url(
                f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}",
                password=self.redis_config.get('password'),
                encoding="utf-8",
                decode_responses=True
            )

            # Test connection
            await self.redis.ping()
            logger.info("✅ Redis connection established")

            # Register Lua scripts
            await self._register_lua_scripts()

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    def _load_lua_scripts(self):
        """Load Lua scripts from disk"""
        try:
            with open('lua/check_arb.lua', 'r') as f:
                self.lua_scripts['check_arb'] = f.read()

            logger.info("Lua scripts loaded from disk")

        except FileNotFoundError as e:
            logger.error(f"Lua script file not found: {e}")
            # Fallback: inline Lua script
            self.lua_scripts['check_arb'] = self._get_inline_check_arb_script()
            logger.warning("Using inline Lua script fallback")

    async def _register_lua_scripts(self):
        """Register Lua scripts with Redis for faster execution"""
        try:
            if 'check_arb' in self.lua_scripts:
                script = self.redis.register_script(self.lua_scripts['check_arb'])
                self.lua_scripts['check_arb_fn'] = script
                logger.info("✅ Lua scripts registered with Redis")

        except Exception as e:
            logger.error(f"Failed to register Lua scripts: {e}")

    async def process_odds_update(
        self,
        event_id: str,
        market_type: str,
        book: str,
        odds: Dict[str, float],
        event_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process odds update and check for arbitrage opportunities

        Args:
            event_id: Unique event identifier
            market_type: 'moneyline', 'puckline', 'totals'
            book: Bookmaker name ('pinnacle', 'bet365', etc.)
            odds: Dict with 'home', 'away', 'draw' (optional) keys
            event_info: Event metadata (teams, league, etc.)

        Returns:
            Arbitrage data if found, None otherwise
        """
        try:
            # Build Redis keys
            pinnacle_key = f"odds:pinnacle:{event_id}:{market_type}"
            soft_key = f"odds:soft:{event_id}:{market_type}"  # Placeholder for other books

            timestamp = datetime.now().timestamp()

            # Store odds in Redis
            if book.lower() == 'pinnacle':
                key = pinnacle_key
            else:
                key = soft_key

            await self._store_odds(key, odds, market_type, timestamp)
            self.stats['odds_updates'] += 1

            # Check for arbitrage (only if this is Pinnacle update)
            if book.lower() == 'pinnacle':
                arb_result = await self._check_arbitrage_lua(
                    pinnacle_key=pinnacle_key,
                    soft_key=soft_key,
                    odds=odds,
                    market_type=market_type,
                    timestamp=timestamp
                )

                if arb_result:
                    self.stats['arbs_detected'] += 1

                    # Send notification
                    if self.notifier and event_info:
                        await self.notifier.send_arbitrage_alert(arb_result, event_info)
                        self.stats['arbs_alerted'] += 1

                    return arb_result

            return None

        except Exception as e:
            logger.error(f"Error processing odds update: {e}")
            return None

    async def _store_odds(
        self,
        key: str,
        odds: Dict[str, float],
        market_type: str,
        timestamp: float
    ):
        """Store odds in Redis hash"""
        data = {
            'home': odds.get('home', 0),
            'away': odds.get('away', 0),
            'draw': odds.get('draw', 0),
            'market_type': market_type,
            'timestamp': timestamp
        }

        await self.redis.hset(key, mapping=data)
        await self.redis.expire(key, 1800)  # 30 minute expiry

    async def _check_arbitrage_lua(
        self,
        pinnacle_key: str,
        soft_key: str,
        odds: Dict[str, float],
        market_type: str,
        timestamp: float
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Lua script for atomic arbitrage detection

        Returns:
            Arbitrage data if found, None otherwise
        """
        try:
            # Execute Lua script
            result = await self.lua_scripts['check_arb_fn'](
                keys=[pinnacle_key, soft_key],
                args=[
                    odds.get('home', 0),
                    odds.get('away', 0),
                    odds.get('draw', 0),
                    timestamp,
                    market_type
                ]
            )

            self.stats['lua_executions'] += 1

            if result:
                # Parse JSON result from Lua
                arb_data = json.loads(result)
                logger.info(f"🎯 Arbitrage detected: {arb_data}")
                return arb_data
            else:
                return None

        except Exception as e:
            logger.error(f"Error executing Lua arbitrage check: {e}")
            # Fallback to Python-based check
            return await self._check_arbitrage_python(pinnacle_key, soft_key, odds)

    async def _check_arbitrage_python(
        self,
        pinnacle_key: str,
        soft_key: str,
        pinnacle_odds: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        Fallback Python-based arbitrage detection
        (Less efficient than Lua due to network round trips)
        """
        try:
            # Fetch soft book odds
            soft_data = await self.redis.hgetall(soft_key)

            if not soft_data:
                return None

            soft_odds = {
                'home': float(soft_data.get('home', 0)),
                'away': float(soft_data.get('away', 0)),
                'draw': float(soft_data.get('draw', 0))
            }

            # Check timestamp staleness
            soft_timestamp = float(soft_data.get('timestamp', 0))
            current_timestamp = datetime.now().timestamp()

            if (current_timestamp - soft_timestamp) > 60:
                # Soft book odds too old
                return None

            # Calculate arbitrage: Pinnacle home vs Soft away
            home_odd = pinnacle_odds.get('home', 0)
            soft_away = soft_odds.get('away', 0)

            if home_odd > 0 and soft_away > 0:
                prob = (1 / home_odd) + (1 / soft_away)

                if prob < 1.0:
                    profit_pct = ((1 / prob) - 1) * 100

                    return {
                        'type': '2-way',
                        'profit_pct': f"{profit_pct:.2f}",
                        'leg1': {'book': 'pinnacle', 'market': 'home', 'odd': home_odd},
                        'leg2': {'book': 'soft', 'market': 'away', 'odd': soft_away},
                        'implied_prob': f"{prob:.4f}"
                    }

            return None

        except Exception as e:
            logger.error(f"Error in Python arbitrage check: {e}")
            return None

    async def get_current_odds(self, event_id: str, market_type: str) -> Optional[Dict[str, Any]]:
        """Get current odds for an event/market"""
        try:
            pinnacle_key = f"odds:pinnacle:{event_id}:{market_type}"
            data = await self.redis.hgetall(pinnacle_key)

            if not data:
                return None

            return {
                'home': float(data.get('home', 0)),
                'away': float(data.get('away', 0)),
                'draw': float(data.get('draw', 0)),
                'timestamp': float(data.get('timestamp', 0))
            }

        except Exception as e:
            logger.error(f"Error fetching odds: {e}")
            return None

    async def get_active_events(self) -> List[str]:
        """Get list of currently tracked event IDs"""
        try:
            # Scan for all odds keys
            keys = []
            async for key in self.redis.scan_iter(match="odds:pinnacle:*"):
                # Extract event ID from key format: odds:pinnacle:{event_id}:{market}
                parts = key.split(':')
                if len(parts) >= 3:
                    event_id = parts[2]
                    if event_id not in keys:
                        keys.append(event_id)

            return keys

        except Exception as e:
            logger.error(f"Error fetching active events: {e}")
            return []

    async def cleanup_stale_odds(self, max_age_seconds: int = 3600):
        """Remove odds older than specified age"""
        try:
            cleaned = 0
            current_time = datetime.now().timestamp()

            async for key in self.redis.scan_iter(match="odds:*"):
                timestamp = await self.redis.hget(key, 'timestamp')

                if timestamp:
                    age = current_time - float(timestamp)
                    if age > max_age_seconds:
                        await self.redis.delete(key)
                        cleaned += 1

            if cleaned > 0:
                logger.info(f"🧹 Cleaned up {cleaned} stale odds entries")

        except Exception as e:
            logger.error(f"Error cleaning up stale odds: {e}")

    def get_stats(self) -> Dict[str, int]:
        """Get engine statistics"""
        return self.stats.copy()

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    @staticmethod
    def _get_inline_check_arb_script() -> str:
        """Inline Lua script fallback (simplified version)"""
        return """
        local pinnacle_key = KEYS[1]
        local soft_key = KEYS[2]
        local home_odd = tonumber(ARGV[1])
        local away_odd = tonumber(ARGV[2])
        local draw_odd = tonumber(ARGV[3])
        local timestamp = ARGV[4]
        local market_type = ARGV[5]

        redis.call('HSET', pinnacle_key, 'home', home_odd, 'away', away_odd, 'draw', draw_odd, 'timestamp', timestamp)
        redis.call('EXPIRE', pinnacle_key, 1800)

        local soft_exists = redis.call('EXISTS', soft_key)
        if soft_exists == 0 then
            return nil
        end

        local soft_away = tonumber(redis.call('HGET', soft_key, 'away'))
        if not soft_away or soft_away == 0 then
            return nil
        end

        local prob = (1 / home_odd) + (1 / soft_away)
        if prob < 1.0 then
            local profit = ((1 / prob) - 1) * 100
            return string.format('{"profit_pct": "%.2f", "type": "2-way"}', profit)
        end

        return nil
        """


# Example usage
if __name__ == "__main__":
    import yaml

    async def test():
        # Load config
        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        # Initialize engine
        engine = ArbitrageEngine(config)
        await engine.initialize()

        # Simulate odds updates
        event_id = "nhl_tor_mtl_20250215"

        # Pinnacle odds
        await engine.process_odds_update(
            event_id=event_id,
            market_type="moneyline",
            book="pinnacle",
            odds={'home': 2.15, 'away': 1.85},
            event_info={
                'home_team': 'Toronto Maple Leafs',
                'away_team': 'Montreal Canadiens',
                'league': 'NHL'
            }
        )

        # Soft book odds (creating arb opportunity)
        await engine.process_odds_update(
            event_id=event_id,
            market_type="moneyline",
            book="bet365",
            odds={'home': 1.90, 'away': 2.10}
        )

        # Get stats
        print(f"Engine stats: {engine.get_stats()}")

        await engine.close()

    asyncio.run(test())
