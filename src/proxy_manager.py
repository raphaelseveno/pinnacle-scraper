"""
Project Acheron - Proxy Manager
Handles residential proxy rotation and routing logic for stealth authentication
"""

import random
from typing import Optional, Dict, Any, List
import httpx
from loguru import logger


class ProxyManager:
    """
    Manages proxy connections for authentication and WebSocket traffic

    Supports:
    - PacketStream residential proxies
    - Webshare proxies
    - Custom proxy lists
    - Intelligent routing (proxy for auth, direct for WebSocket)
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config['proxy']
        self.provider = self.config.get('provider', 'packetstream')
        self.api_key = self.config.get('api_key')
        self.use_proxy_for = self.config.get('use_proxy_for', ['authentication'])
        self.rotation_enabled = self.config.get('rotation_enabled', True)

        # Proxy pool
        self.proxy_pool: List[str] = []
        self.current_proxy_index = 0

        # PacketStream API endpoints
        self.packetstream_api = "https://proxy.packetstream.io/api/v1"

        # Statistics
        self.stats = {
            'requests_via_proxy': 0,
            'requests_direct': 0,
            'proxy_failures': 0,
            'rotations': 0
        }

        logger.info(f"ProxyManager initialized. Provider: {self.provider}")

    async def initialize(self):
        """Initialize proxy pool from provider"""
        try:
            if self.provider == 'packetstream':
                await self._init_packetstream()
            elif self.provider == 'webshare':
                await self._init_webshare()
            elif self.provider == 'custom':
                await self._init_custom()
            else:
                logger.warning(f"Unknown proxy provider: {self.provider}, using direct connection")

            logger.info(f"Proxy pool initialized with {len(self.proxy_pool)} proxies")

        except Exception as e:
            logger.error(f"Failed to initialize proxy pool: {e}")
            logger.warning("Continuing without proxies - authentication may fail")

    async def _init_packetstream(self):
        """Initialize PacketStream residential proxies"""
        # PacketStream format:
        # http://username:password@proxy.packetstream.io:31112

        if not self.api_key:
            logger.error("PacketStream API key not configured")
            return

        # PacketStream uses a single endpoint with authentication
        # The proxy will automatically rotate residential IPs
        proxy_url = f"http://{self.api_key}@proxy.packetstream.io:31112"

        self.proxy_pool = [proxy_url]
        logger.info("PacketStream proxy configured (auto-rotating residential IPs)")

    async def _init_webshare(self):
        """Initialize Webshare proxies"""
        # Webshare format:
        # http://username:password@proxy_address:port

        if not self.api_key:
            logger.error("Webshare API key not configured")
            return

        # Fetch proxy list from Webshare API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://proxy.webshare.io/api/v2/proxy/list/",
                    headers={"Authorization": f"Token {self.api_key}"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])

                    for proxy in results:
                        proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['proxy_address']}:{proxy['port']}"
                        self.proxy_pool.append(proxy_url)

                    logger.info(f"Loaded {len(self.proxy_pool)} Webshare proxies")
                else:
                    logger.error(f"Failed to fetch Webshare proxies: {response.status_code}")

            except Exception as e:
                logger.error(f"Error fetching Webshare proxies: {e}")

    async def _init_custom(self):
        """Initialize custom proxy list from config"""
        custom_proxies = self.config.get('custom_proxy_list', [])

        if not custom_proxies:
            logger.warning("No custom proxies configured")
            return

        self.proxy_pool = custom_proxies
        logger.info(f"Loaded {len(self.proxy_pool)} custom proxies")

    def get_proxy(self, purpose: str = 'authentication') -> Optional[str]:
        """
        Get proxy URL for specified purpose

        Args:
            purpose: 'authentication' or 'websocket'

        Returns:
            Proxy URL or None if direct connection should be used
        """
        # Check if proxy should be used for this purpose
        if purpose not in self.use_proxy_for:
            self.stats['requests_direct'] += 1
            return None

        # If no proxies available, use direct connection
        if not self.proxy_pool:
            logger.warning(f"No proxies available for {purpose}, using direct connection")
            self.stats['requests_direct'] += 1
            return None

        # Get current proxy
        proxy = self.proxy_pool[self.current_proxy_index]
        self.stats['requests_via_proxy'] += 1

        # Rotate if enabled
        if self.rotation_enabled and purpose == 'authentication':
            self._rotate_proxy()

        logger.debug(f"Using proxy for {purpose}: {self._mask_proxy_url(proxy)}")
        return proxy

    def _rotate_proxy(self):
        """Rotate to next proxy in pool"""
        if len(self.proxy_pool) <= 1:
            return  # No rotation needed for single proxy

        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_pool)
        self.stats['rotations'] += 1
        logger.debug(f"Rotated to proxy index {self.current_proxy_index}")

    def mark_proxy_failed(self, proxy_url: str):
        """
        Mark proxy as failed and remove from pool

        Args:
            proxy_url: The failed proxy URL
        """
        try:
            if proxy_url in self.proxy_pool:
                self.proxy_pool.remove(proxy_url)
                self.stats['proxy_failures'] += 1
                logger.warning(f"Removed failed proxy: {self._mask_proxy_url(proxy_url)}")

                # Reset index if needed
                if self.current_proxy_index >= len(self.proxy_pool) and self.proxy_pool:
                    self.current_proxy_index = 0

        except Exception as e:
            logger.error(f"Error marking proxy as failed: {e}")

    def get_random_proxy(self) -> Optional[str]:
        """Get a random proxy from the pool"""
        if not self.proxy_pool:
            return None

        proxy = random.choice(self.proxy_pool)
        self.stats['requests_via_proxy'] += 1
        return proxy

    @staticmethod
    def _mask_proxy_url(proxy_url: str) -> str:
        """Mask proxy URL for logging (hide credentials)"""
        try:
            # Format: http://user:pass@host:port
            if '@' in proxy_url:
                protocol_auth, host_port = proxy_url.split('@')
                protocol = protocol_auth.split('://')[0]
                return f"{protocol}://***:***@{host_port}"
            else:
                return proxy_url
        except:
            return "***masked***"

    def get_proxy_dict(self, purpose: str = 'authentication') -> Optional[Dict[str, str]]:
        """
        Get proxy configuration as dict for HTTP clients

        Args:
            purpose: 'authentication' or 'websocket'

        Returns:
            Dict with 'http' and 'https' proxy URLs, or None for direct connection
        """
        proxy = self.get_proxy(purpose)

        if not proxy:
            return None

        return {
            'http://': proxy,
            'https://': proxy
        }

    def get_stats(self) -> Dict[str, int]:
        """Get proxy usage statistics"""
        return self.stats.copy()

    def should_use_proxy(self, purpose: str) -> bool:
        """Check if proxy should be used for given purpose"""
        return purpose in self.use_proxy_for and len(self.proxy_pool) > 0


# Example usage
if __name__ == "__main__":
    import asyncio
    import yaml

    async def test():
        # Load config
        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        # Initialize proxy manager
        manager = ProxyManager(config)
        await manager.initialize()

        # Get proxy for authentication
        auth_proxy = manager.get_proxy('authentication')
        print(f"Auth proxy: {manager._mask_proxy_url(auth_proxy) if auth_proxy else 'Direct'}")

        # Get proxy for WebSocket
        ws_proxy = manager.get_proxy('websocket')
        print(f"WebSocket proxy: {manager._mask_proxy_url(ws_proxy) if ws_proxy else 'Direct'}")

        # Get stats
        print(f"Stats: {manager.get_stats()}")

    asyncio.run(test())
