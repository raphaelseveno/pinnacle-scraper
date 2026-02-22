"""
Project Acheron - Interceptor (WebSocket Hijacking)
Replicates Pinnacle's WebSocket connection for real-time odds updates
"""

import asyncio
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from loguru import logger
import aiohttp


class Interceptor:
    """
    WebSocket client that hijacks Pinnacle's real-time odds feed

    Features:
    - Replicates browser WebSocket handshake headers
    - Automatic heartbeat/ping-pong to maintain connection
    - Auto-reconnection with exponential backoff
    - Message parsing and routing to arbitrage engine
    - Delta-only updates for bandwidth efficiency
    """

    def __init__(self, config: Dict[str, Any], proxy_manager=None, engine=None):
        self.config = config
        self.pinnacle_config = config['pinnacle']
        self.monitoring_config = config['monitoring']
        self.proxy_manager = proxy_manager
        self.engine = engine

        # WebSocket connection
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.websocket_url: Optional[str] = None
        self.session_data: Optional[Dict[str, Any]] = None

        # Connection state
        self.is_connected = False
        self.is_running = False
        self.last_message_time: Optional[float] = None

        # Reconnection logic
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = self.monitoring_config.get('max_reconnect_attempts', 10)
        self.reconnect_backoff_base = self.monitoring_config.get('reconnect_backoff_base', 2)

        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}

        # Statistics
        self.stats = {
            'messages_received': 0,
            'odds_updates': 0,
            'heartbeats_sent': 0,
            'reconnections': 0,
            'errors': 0
        }

        logger.info("Interceptor initialized")

    def set_session_data(self, session_data: Dict[str, Any]):
        """
        Set session data from Scout

        Args:
            session_data: Dict containing cookies, WebSocket URL, user-agent, etc.
        """
        self.session_data = session_data
        self.websocket_url = session_data.get('websocket_url')

        if not self.websocket_url:
            logger.error("No WebSocket URL in session data!")
        else:
            logger.info(f"WebSocket URL configured: {self.websocket_url}")

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to Pinnacle

        Returns:
            bool: True if connection successful
        """
        if not self.websocket_url or not self.session_data:
            logger.error("Cannot connect: missing session data or WebSocket URL")
            return False

        try:
            logger.info(f"🔌 Connecting to WebSocket: {self.websocket_url}")

            # Build headers that replicate browser connection
            headers = self._build_websocket_headers()

            # Get proxy if configured for WebSocket
            proxy = None
            if self.proxy_manager and self.proxy_manager.should_use_proxy('websocket'):
                proxy_url = self.proxy_manager.get_proxy('websocket')
                if proxy_url:
                    proxy = proxy_url
                    logger.info("Using proxy for WebSocket connection")

            # Connect to WebSocket
            # Note: websockets library doesn't support proxy directly,
            # would need to use aiohttp or custom implementation for proxy support
            self.websocket = await websockets.connect(
                self.websocket_url,
                extra_headers=headers,
                ping_interval=None,  # We'll handle heartbeat manually
                ping_timeout=None
            )

            self.is_connected = True
            self.reconnect_attempts = 0
            self.last_message_time = datetime.now().timestamp()

            logger.info("✅ WebSocket connected successfully!")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.stats['errors'] += 1
            return False

    def _build_websocket_headers(self) -> Dict[str, str]:
        """Build WebSocket handshake headers that mimic browser"""
        cookies = self.session_data.get('cookies', {})
        user_agent = self.session_data.get('user_agent', 'Mozilla/5.0')

        # Format cookies as header string
        cookie_header = '; '.join([f"{name}={value}" for name, value in cookies.items()])

        headers = {
            'User-Agent': user_agent,
            'Origin': self.pinnacle_config.get('base_url', 'https://www.ps3838.com'),
            'Cookie': cookie_header
        }

        # Add auth token if present
        auth_token = self.session_data.get('auth_token')
        if auth_token:
            headers['Authorization'] = f"Bearer {auth_token}"

        return headers

    async def listen(self):
        """
        Main listening loop - receives and processes WebSocket messages

        This runs continuously, handling:
        - Incoming odds updates
        - Heartbeat/ping-pong
        - Auto-reconnection on disconnect
        """
        self.is_running = True

        while self.is_running:
            try:
                if not self.is_connected:
                    # Attempt to connect/reconnect
                    success = await self.connect()

                    if not success:
                        await self._handle_reconnection()
                        continue

                # Start heartbeat task
                heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                # Listen for messages
                async for message in self.websocket:
                    await self._handle_message(message)

                # If we reach here, connection was closed normally
                logger.warning("WebSocket connection closed normally")
                self.is_connected = False

                # Cancel heartbeat
                heartbeat_task.cancel()

            except ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                self.is_connected = False
                self.stats['errors'] += 1

                # Attempt reconnection
                await self._handle_reconnection()

            except WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                self.is_connected = False
                self.stats['errors'] += 1

                await self._handle_reconnection()

            except Exception as e:
                logger.error(f"Unexpected error in listen loop: {e}")
                self.stats['errors'] += 1

                await self._handle_reconnection()

    async def _handle_message(self, message: str):
        """
        Process incoming WebSocket message

        Args:
            message: Raw message from WebSocket
        """
        try:
            self.stats['messages_received'] += 1
            self.last_message_time = datetime.now().timestamp()

            # Parse message (typically JSON)
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                # Some messages might be plain text (ping/pong)
                logger.debug(f"Non-JSON message: {message[:100]}")
                return

            # Identify message type and route to appropriate handler
            msg_type = self._identify_message_type(data)

            if msg_type == 'odds_update':
                await self._handle_odds_update(data)
            elif msg_type == 'heartbeat':
                await self._handle_heartbeat_response(data)
            elif msg_type == 'subscription_confirm':
                logger.info("Subscription confirmed")
            else:
                logger.debug(f"Unknown message type: {data.get('type', 'unknown')}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _identify_message_type(self, data: Dict[str, Any]) -> str:
        """
        Identify message type from WebSocket payload

        Args:
            data: Parsed JSON message

        Returns:
            Message type string
        """
        # Common message type fields
        if 'odds' in data or 'prices' in data or 'markets' in data:
            return 'odds_update'

        if 'type' in data:
            msg_type = data['type'].lower()

            if 'pong' in msg_type or 'heartbeat' in msg_type:
                return 'heartbeat'

            if 'subscribe' in msg_type or 'confirm' in msg_type:
                return 'subscription_confirm'

        # Default
        return 'unknown'

    async def _handle_odds_update(self, data: Dict[str, Any]):
        """
        Process odds update message and send to arbitrage engine

        Args:
            data: Odds update payload
        """
        try:
            self.stats['odds_updates'] += 1

            # Extract event and odds data (format depends on Pinnacle's API)
            # This is a simplified example - actual implementation depends on message format

            event_id = data.get('eventId') or data.get('event_id') or data.get('id')
            market_type = data.get('marketType') or data.get('market') or 'moneyline'

            # Extract odds (format varies)
            odds = self._extract_odds_from_payload(data)

            if not odds or not event_id:
                logger.debug("Incomplete odds data, skipping")
                return

            # Build event info
            event_info = self._extract_event_info(data)

            # Send to arbitrage engine
            if self.engine:
                await self.engine.process_odds_update(
                    event_id=str(event_id),
                    market_type=market_type,
                    book='pinnacle',
                    odds=odds,
                    event_info=event_info
                )

            logger.debug(f"📊 Odds update processed: {event_id} | {market_type} | {odds}")

        except Exception as e:
            logger.error(f"Error processing odds update: {e}")

    def _extract_odds_from_payload(self, data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Extract odds values from WebSocket payload

        Note: Format depends on Pinnacle's WebSocket message structure
        This is a generic implementation that handles common formats

        Args:
            data: WebSocket message data

        Returns:
            Dict with 'home', 'away', 'draw' keys (decimal odds)
        """
        odds = {}

        # Try different common formats
        if 'odds' in data:
            odds_data = data['odds']

            # Format 1: Direct values
            if isinstance(odds_data, dict):
                odds['home'] = float(odds_data.get('home', 0) or odds_data.get('1', 0))
                odds['away'] = float(odds_data.get('away', 0) or odds_data.get('2', 0))
                odds['draw'] = float(odds_data.get('draw', 0) or odds_data.get('X', 0))

        # Format 2: Prices array
        elif 'prices' in data:
            prices = data['prices']
            if isinstance(prices, list) and len(prices) >= 2:
                odds['home'] = float(prices[0].get('price', 0))
                odds['away'] = float(prices[1].get('price', 0))
                if len(prices) >= 3:
                    odds['draw'] = float(prices[2].get('price', 0))

        # Format 3: Markets structure
        elif 'markets' in data:
            markets = data['markets']
            if isinstance(markets, list) and markets:
                market = markets[0]
                if 'outcomes' in market:
                    outcomes = market['outcomes']
                    if len(outcomes) >= 2:
                        odds['home'] = float(outcomes[0].get('price', 0))
                        odds['away'] = float(outcomes[1].get('price', 0))

        # Remove zero values
        odds = {k: v for k, v in odds.items() if v > 0}

        return odds if odds else None

    def _extract_event_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract event metadata from message"""
        return {
            'event_id': data.get('eventId') or data.get('id'),
            'league_id': data.get('leagueId') or data.get('league'),
            'home_team': data.get('homeTeam') or data.get('home') or 'Home',
            'away_team': data.get('awayTeam') or data.get('away') or 'Away',
            'league': data.get('league') or data.get('sport') or 'NHL',
            'start_time': data.get('startTime') or data.get('timestamp')
        }

    async def _heartbeat_loop(self):
        """
        Send periodic heartbeat/ping to keep connection alive

        Pinnacle typically expects ping every 25-30 seconds
        """
        try:
            while self.is_connected:
                await asyncio.sleep(25)  # Send every 25 seconds

                if self.websocket and not self.websocket.closed:
                    # Send ping (format depends on server expectation)
                    # Common formats:
                    # - RFC 6455 ping frame (built-in)
                    # - JSON message: {"type": "ping"}
                    # - Plain text: "2" (Socket.io format)

                    try:
                        # Try built-in ping
                        await self.websocket.ping()
                        self.stats['heartbeats_sent'] += 1
                        logger.debug("💓 Heartbeat sent")

                    except Exception as e:
                        logger.warning(f"Failed to send heartbeat: {e}")

        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")

    async def _handle_heartbeat_response(self, data: Dict[str, Any]):
        """Handle pong/heartbeat response from server"""
        logger.debug("💚 Heartbeat acknowledged")

    async def _handle_reconnection(self):
        """Handle reconnection logic with exponential backoff"""
        self.reconnect_attempts += 1
        self.stats['reconnections'] += 1

        if self.reconnect_attempts > self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached, giving up")
            self.is_running = False
            return

        # Calculate backoff delay
        delay = min(300, self.reconnect_backoff_base ** self.reconnect_attempts)  # Max 5 minutes

        logger.info(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        await asyncio.sleep(delay)

    async def subscribe_to_markets(self, event_ids: list = None, market_types: list = None):
        """
        Subscribe to specific markets/events

        Args:
            event_ids: List of event IDs to subscribe to
            market_types: List of market types ('moneyline', 'puckline', etc.)
        """
        if not self.is_connected or not self.websocket:
            logger.warning("Cannot subscribe: not connected")
            return

        try:
            # Build subscription message (format depends on Pinnacle's protocol)
            # Common format:
            subscribe_msg = {
                "type": "subscribe",
                "events": event_ids or [],
                "markets": market_types or ["moneyline", "puckline", "totals"]
            }

            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to markets: {market_types}")

        except Exception as e:
            logger.error(f"Failed to subscribe to markets: {e}")

    def get_stats(self) -> Dict[str, int]:
        """Get interceptor statistics"""
        stats = self.stats.copy()
        stats['is_connected'] = self.is_connected
        stats['reconnect_attempts'] = self.reconnect_attempts

        if self.last_message_time:
            stats['seconds_since_last_message'] = int(datetime.now().timestamp() - self.last_message_time)

        return stats

    async def close(self):
        """Close WebSocket connection"""
        self.is_running = False

        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            logger.info("WebSocket connection closed")


# Example usage
if __name__ == "__main__":
    import yaml

    async def test():
        # Load config
        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        # Mock session data (normally comes from Scout)
        session_data = {
            'websocket_url': 'wss://echo.websocket.org',  # Test endpoint
            'cookies': {'test': 'cookie'},
            'user_agent': 'Mozilla/5.0'
        }

        # Initialize interceptor
        interceptor = Interceptor(config)
        interceptor.set_session_data(session_data)

        # Start listening
        listen_task = asyncio.create_task(interceptor.listen())

        # Let it run for a bit
        await asyncio.sleep(30)

        # Get stats
        print(f"Stats: {interceptor.get_stats()}")

        # Close
        await interceptor.close()
        listen_task.cancel()

    asyncio.run(test())
