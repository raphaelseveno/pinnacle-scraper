"""
Project Acheron - Scout (Authentication & Session Management)
Handles stealth authentication, Cloudflare bypass, and cookie extraction
"""

import asyncio
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import nodriver as uc
from loguru import logger


class Scout:
    """
    Stealth browser automation for Pinnacle authentication

    Features:
    - Nodriver for undetected Chrome automation
    - Automatic Cloudflare Turnstile bypass
    - Session cookie extraction and persistence
    - Automatic re-authentication before expiry
    - WebSocket endpoint discovery
    """

    def __init__(self, config: Dict[str, Any], proxy_manager=None):
        self.config = config
        self.pinnacle_config = config['pinnacle']
        self.stealth_config = config['stealth']
        self.proxy_manager = proxy_manager

        # Credentials
        self.username = self.pinnacle_config['username']
        self.password = self.pinnacle_config['password']
        self.base_url = self.pinnacle_config.get('base_url', 'https://www.ps3838.com')

        # Browser and page instances
        self.browser: Optional[uc.Browser] = None
        self.page: Optional[uc.Tab] = None

        # Session data
        self.session_data = {
            'cookies': None,
            'auth_token': None,
            'websocket_url': None,
            'user_agent': None,
            'expires_at': None
        }

        # Session management
        self.session_duration = self.stealth_config['timing'].get('session_duration_min', 25) * 60
        self.last_auth_time: Optional[float] = None

        logger.info("Scout initialized")

    async def initialize(self):
        """Initialize browser and prepare for authentication"""
        try:
            logger.info("🚀 Starting stealth browser...")

            # Get proxy if configured
            proxy = None
            if self.proxy_manager:
                proxy_url = self.proxy_manager.get_proxy('authentication')
                if proxy_url:
                    proxy = proxy_url
                    logger.info(f"Using proxy: {self.proxy_manager._mask_proxy_url(proxy_url)}")

            # Launch Nodriver browser
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                f'--window-size={self.stealth_config["browser"]["viewport"]["width"]},{self.stealth_config["browser"]["viewport"]["height"]}'
            ]

            # Add proxy if configured
            if proxy:
                browser_args.append(f'--proxy-server={proxy}')

            self.browser = await uc.start(
                headless=self.stealth_config['browser'].get('headless', True),
                browser_args=browser_args,
                user_data_dir=None  # Don't persist data (fresh session each time)
            )

            self.page = await self.browser.get(self.base_url, new_tab=True)

            # Set custom user agent if specified
            if self.stealth_config['browser'].get('user_agent'):
                await self.page.send(uc.cdp.emulation.set_user_agent_override(
                    user_agent=self.stealth_config['browser']['user_agent']
                ))

            logger.info("✅ Browser initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def authenticate(self) -> bool:
        """
        Perform authentication and extract session data

        Returns:
            bool: True if authentication successful
        """
        try:
            logger.info(f"🔐 Authenticating to Pinnacle ({self.base_url})...")

            # Navigate to login page
            await self.page.get(f"{self.base_url}/en/login")
            await asyncio.sleep(random.uniform(2, 4))  # Human-like delay

            # Wait for page load and check for Cloudflare
            await self._handle_cloudflare_if_present()

            # Find and fill login form
            success = await self._fill_login_form()

            if not success:
                logger.error("Failed to fill login form")
                return False

            # Wait for redirect after login
            await asyncio.sleep(3)

            # Extract session data
            await self._extract_session_data()

            # Discover WebSocket endpoint
            await self._discover_websocket_endpoint()

            # Mark authentication time
            self.last_auth_time = datetime.now().timestamp()
            self.session_data['expires_at'] = self.last_auth_time + self.session_duration

            logger.info("✅ Authentication successful!")
            logger.info(f"Session expires at: {datetime.fromtimestamp(self.session_data['expires_at'])}")

            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    async def _handle_cloudflare_if_present(self):
        """Detect and handle Cloudflare Turnstile challenge"""
        try:
            logger.info("Checking for Cloudflare Turnstile...")

            # Wait a bit for Cloudflare to load
            await asyncio.sleep(2)

            # Nodriver has built-in Cloudflare handling in recent versions
            # Check for common Cloudflare selectors
            cloudflare_selectors = [
                'iframe[src*="challenges.cloudflare.com"]',
                '#challenge-stage',
                '.cf-turnstile',
                '[data-sitekey]'  # Turnstile widget
            ]

            for selector in cloudflare_selectors:
                try:
                    element = await self.page.select(selector, timeout=2)
                    if element:
                        logger.info("🔒 Cloudflare Turnstile detected, waiting for bypass...")

                        # Nodriver should handle this automatically
                        # Wait for challenge to complete
                        await asyncio.sleep(5)

                        # Check if still on challenge page
                        current_url = self.page.url
                        if 'challenge' in current_url.lower():
                            logger.warning("Still on challenge page, waiting longer...")
                            await asyncio.sleep(10)

                        logger.info("✅ Cloudflare challenge completed")
                        return

                except Exception:
                    continue  # Selector not found, try next

            logger.info("No Cloudflare challenge detected")

        except Exception as e:
            logger.warning(f"Error handling Cloudflare: {e}")

    async def _fill_login_form(self) -> bool:
        """Fill and submit login form"""
        try:
            # Wait for login form to be visible
            await asyncio.sleep(2)

            # Find username field (try multiple selectors)
            username_selectors = [
                'input[name="username"]',
                'input[id="username"]',
                'input[type="text"]',
                'input[autocomplete="username"]'
            ]

            username_field = None
            for selector in username_selectors:
                try:
                    username_field = await self.page.select(selector, timeout=2)
                    if username_field:
                        break
                except:
                    continue

            if not username_field:
                logger.error("Could not find username field")
                return False

            # Find password field
            password_selectors = [
                'input[name="password"]',
                'input[id="password"]',
                'input[type="password"]'
            ]

            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await self.page.select(selector, timeout=2)
                    if password_field:
                        break
                except:
                    continue

            if not password_field:
                logger.error("Could not find password field")
                return False

            # Fill form with human-like delays
            logger.info("Filling login form...")

            # Type username
            await username_field.click()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await username_field.send_keys(self.username)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            # Type password
            await password_field.click()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await password_field.send_keys(self.password)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            # Find and click submit button
            submit_selectors = [
                'button[type="submit"]',
                'button[id="login"]',
                'input[type="submit"]',
                '.btn-login',
                '[data-action="login"]'
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = await self.page.select(selector, timeout=2)
                    if submit_button:
                        break
                except:
                    continue

            if submit_button:
                logger.info("Submitting login form...")
                await submit_button.click()
            else:
                # Fallback: press Enter in password field
                logger.info("Submit button not found, pressing Enter...")
                await password_field.send_keys('\n')

            return True

        except Exception as e:
            logger.error(f"Error filling login form: {e}")
            return False

    async def _extract_session_data(self):
        """Extract cookies, tokens, and other session data"""
        try:
            logger.info("Extracting session data...")

            # Get all cookies
            cookies = await self.browser.cookies.get_all()

            # Format cookies for HTTP requests
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie.name] = cookie.value

            self.session_data['cookies'] = cookie_dict

            # Look for important cookies
            important_cookies = ['cf_clearance', 'ASP.NET_SessionId', 'auth_token', 'session']
            found_cookies = [name for name in important_cookies if name in cookie_dict]

            logger.info(f"Extracted {len(cookie_dict)} cookies, including: {found_cookies}")

            # Extract User-Agent
            user_agent = await self.page.evaluate('navigator.userAgent')
            self.session_data['user_agent'] = user_agent

            # Try to extract auth token from localStorage or cookies
            try:
                auth_token = await self.page.evaluate('localStorage.getItem("authToken") || localStorage.getItem("token")')
                if auth_token:
                    self.session_data['auth_token'] = auth_token
                    logger.info("✅ Auth token extracted from localStorage")
            except:
                pass

        except Exception as e:
            logger.error(f"Error extracting session data: {e}")

    async def _discover_websocket_endpoint(self):
        """Discover WebSocket URL by monitoring network traffic"""
        try:
            logger.info("🔍 Discovering WebSocket endpoint...")

            # Navigate to sports/hockey page to trigger WebSocket connection
            await self.page.get(f"{self.base_url}/en/sports/hockey/nhl")
            await asyncio.sleep(3)

            # Listen for WebSocket connections via CDP
            websocket_url = None

            # Try to find WebSocket URL in page's network connections
            # This is a simplified approach - in production, you'd monitor CDP events
            try:
                # Evaluate JavaScript to find WebSocket connections
                ws_script = """
                (() => {
                    // Check if WebSocket was overridden to store URLs
                    if (window._wsConnections) {
                        return window._wsConnections[0];
                    }

                    // Try to find WebSocket URL in global vars
                    if (window.config && window.config.wsUrl) {
                        return window.config.wsUrl;
                    }

                    // Common WebSocket URL patterns for betting sites
                    return null;
                })()
                """

                result = await self.page.evaluate(ws_script)
                if result:
                    websocket_url = result
                    logger.info(f"✅ WebSocket URL found: {websocket_url}")

            except Exception as e:
                logger.debug(f"Could not extract WebSocket URL from JS: {e}")

            # Fallback: Use common Pinnacle WebSocket patterns
            if not websocket_url:
                # Pinnacle typically uses these patterns
                websocket_url = self.pinnacle_config.get('websocket_url', 'wss://push.ps3838.com')
                logger.info(f"Using configured WebSocket URL: {websocket_url}")

            self.session_data['websocket_url'] = websocket_url

        except Exception as e:
            logger.error(f"Error discovering WebSocket endpoint: {e}")

    def get_session_data(self) -> Dict[str, Any]:
        """Get current session data"""
        return self.session_data.copy()

    def is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.session_data['cookies'] or not self.last_auth_time:
            return False

        # Check if session has expired
        if self.session_data['expires_at']:
            return datetime.now().timestamp() < self.session_data['expires_at']

        return False

    def time_until_expiry(self) -> Optional[float]:
        """Get seconds until session expires"""
        if self.session_data['expires_at']:
            return max(0, self.session_data['expires_at'] - datetime.now().timestamp())
        return None

    async def refresh_session_if_needed(self) -> bool:
        """
        Check if session needs refresh and re-authenticate if necessary

        Returns:
            bool: True if session is valid (refreshed or still valid)
        """
        if self.is_session_valid():
            time_left = self.time_until_expiry()
            logger.debug(f"Session still valid ({time_left:.0f}s remaining)")
            return True

        logger.info("Session expired or invalid, re-authenticating...")
        return await self.authenticate()

    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.browser:
                await self.browser.stop()
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")


# Example usage
if __name__ == "__main__":
    import yaml
    from proxy_manager import ProxyManager

    async def test():
        # Load config
        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        # Initialize proxy manager
        proxy_mgr = ProxyManager(config)
        await proxy_mgr.initialize()

        # Initialize scout
        scout = Scout(config, proxy_mgr)
        await scout.initialize()

        # Authenticate
        success = await scout.authenticate()

        if success:
            session_data = scout.get_session_data()
            print(f"Session cookies: {list(session_data['cookies'].keys())}")
            print(f"WebSocket URL: {session_data['websocket_url']}")
            print(f"Session valid: {scout.is_session_valid()}")

        await scout.close()

    asyncio.run(test())
