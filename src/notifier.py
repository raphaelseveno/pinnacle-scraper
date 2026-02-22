"""
Project Acheron - Notification System
Sends push notifications via ntfy.sh for arbitrage alerts
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from loguru import logger


class Notifier:
    """
    Handles push notifications to mobile devices via ntfy.sh

    Features:
    - Priority 5 (critical) alerts that bypass silent mode
    - Deep links to Pinnacle bet slip
    - Cooldown to prevent alert spam
    - Retry logic with exponential backoff
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config['notifications']
        self.ntfy_config = self.config['ntfy']
        self.thresholds = self.config['thresholds']

        self.server = self.ntfy_config['server']
        self.topic = self.ntfy_config['topic']
        self.priority = self.ntfy_config.get('priority', 5)
        self.tags = self.ntfy_config.get('tags', 'moneybag,warning')

        # Cooldown tracking
        self.last_alert_time: Dict[str, float] = {}
        self.cooldown = self.thresholds.get('cooldown_seconds', 10)

        # HTTP client
        self.client = httpx.AsyncClient(timeout=10.0)

        logger.info(f"Notifier initialized. Topic: {self.topic}")

    async def send_arbitrage_alert(
        self,
        arb_data: Dict[str, Any],
        event_info: Dict[str, Any]
    ) -> bool:
        """
        Send arbitrage alert notification

        Args:
            arb_data: Arbitrage details (profit %, odds, etc.)
            event_info: Event metadata (teams, league, etc.)

        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Check if alert meets minimum thresholds
            profit_pct = float(arb_data.get('profit_pct', 0))

            if profit_pct < self.thresholds['min_profit_percent']:
                logger.debug(f"Arb profit {profit_pct}% below threshold, skipping alert")
                return False

            # Check cooldown to prevent spam
            event_key = event_info.get('event_id', 'unknown')
            if self._is_cooldown_active(event_key):
                logger.debug(f"Cooldown active for {event_key}, skipping alert")
                return False

            # Build alert message
            message = self._build_message(arb_data, event_info)
            title = self._build_title(arb_data, event_info)
            click_url = self._build_deep_link(event_info)

            # Send notification
            success = await self._send_ntfy(
                title=title,
                message=message,
                click_url=click_url,
                priority=self.priority,
                tags=self.tags
            )

            if success:
                self._update_cooldown(event_key)
                logger.info(f"✅ Alert sent: {title}")
            else:
                logger.warning(f"⚠️  Failed to send alert: {title}")

            return success

        except Exception as e:
            logger.error(f"Error sending arbitrage alert: {e}")
            return False

    def _build_message(self, arb_data: Dict[str, Any], event_info: Dict[str, Any]) -> str:
        """Build notification message body"""
        profit = arb_data.get('profit_pct', 0)
        arb_type = arb_data.get('type', '2-way')

        # Extract team names
        home_team = event_info.get('home_team', 'Home')
        away_team = event_info.get('away_team', 'Away')
        league = event_info.get('league', 'NHL')

        # Build message based on arb type
        if arb_type == '2-way':
            leg1 = arb_data['leg1']
            leg2 = arb_data['leg2']

            message = f"""
🏒 {league}: {home_team} vs {away_team}

💰 Profit: {profit}%

Leg 1: {leg1['book'].upper()} - {leg1['market'].capitalize()} @ {leg1['odd']}
Leg 2: {leg2['book'].upper()} - {leg2['market'].capitalize()} @ {leg2['odd']}

Implied Prob: {arb_data.get('implied_prob', 'N/A')}

⚡ Act fast! Odds may move quickly.
""".strip()
        else:
            message = f"🏒 {league}: {home_team} vs {away_team}\n💰 3-Way Arb: {profit}%"

        return message

    def _build_title(self, arb_data: Dict[str, Any], event_info: Dict[str, Any]) -> str:
        """Build notification title"""
        profit = arb_data.get('profit_pct', 0)
        home_team = event_info.get('home_team', 'Home')
        away_team = event_info.get('away_team', 'Away')

        # Emoji indicators based on profit margin
        if float(profit) >= 5.0:
            emoji = "🔥🔥"  # Hot arb
        elif float(profit) >= 3.0:
            emoji = "🔥"
        else:
            emoji = "💰"

        return f"{emoji} ARB: {profit}% | {home_team} vs {away_team}"

    def _build_deep_link(self, event_info: Dict[str, Any]) -> str:
        """Build deep link to Pinnacle bet slip"""
        event_id = event_info.get('event_id')
        league_id = event_info.get('league_id')

        if event_id and league_id:
            # Direct link to event page
            return f"https://www.ps3838.com/sports/hockey/leagues/{league_id}/events/{event_id}"
        else:
            # Fallback to NHL main page
            return "https://www.ps3838.com/sports/hockey/nhl"

    def _is_cooldown_active(self, event_key: str) -> bool:
        """Check if cooldown period is active for this event"""
        if event_key not in self.last_alert_time:
            return False

        elapsed = datetime.now().timestamp() - self.last_alert_time[event_key]
        return elapsed < self.cooldown

    def _update_cooldown(self, event_key: str):
        """Update last alert time for cooldown tracking"""
        self.last_alert_time[event_key] = datetime.now().timestamp()

    async def _send_ntfy(
        self,
        title: str,
        message: str,
        click_url: Optional[str] = None,
        priority: int = 5,
        tags: str = "warning"
    ) -> bool:
        """
        Send notification via ntfy.sh API

        Args:
            title: Notification title
            message: Notification body
            click_url: Deep link URL (opens when tapped)
            priority: 1-5, where 5 is critical (bypasses silent mode)
            tags: Comma-separated emoji tags

        Returns:
            bool: Success status
        """
        try:
            url = f"{self.server}/{self.topic}"

            headers = {
                "Title": title,
                "Priority": str(priority),
                "Tags": tags,
            }

            if click_url:
                headers["Click"] = click_url

            # Send POST request
            response = await self.client.post(
                url,
                data=message.encode('utf-8'),
                headers=headers
            )

            if response.status_code == 200:
                return True
            else:
                logger.warning(f"ntfy.sh returned status {response.status_code}: {response.text}")
                return False

        except httpx.TimeoutException:
            logger.error("Timeout sending notification to ntfy.sh")
            return False
        except Exception as e:
            logger.error(f"Error sending ntfy notification: {e}")
            return False

    async def send_system_alert(self, title: str, message: str, priority: int = 3) -> bool:
        """
        Send system health/status notification

        Args:
            title: Alert title
            message: Alert message
            priority: 1-5 (3 = default for non-critical)

        Returns:
            bool: Success status
        """
        return await self._send_ntfy(
            title=title,
            message=message,
            priority=priority,
            tags="gear,warning"
        )

    async def send_test_notification(self) -> bool:
        """Send test notification to verify setup"""
        return await self._send_ntfy(
            title="🧪 Project Acheron Test",
            message="Test notification from Project Acheron. If you see this, notifications are working! 🎉",
            click_url="https://github.com/acheron",
            priority=3,
            tags="white_check_mark,rocket"
        )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("Notifier closed")


# Example usage
if __name__ == "__main__":
    import yaml

    async def test():
        # Load config
        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        notifier = Notifier(config)

        # Send test notification
        await notifier.send_test_notification()

        # Send mock arbitrage alert
        arb_data = {
            "type": "2-way",
            "profit_pct": "3.45",
            "leg1": {"book": "pinnacle", "market": "home", "odd": 2.15},
            "leg2": {"book": "bet365", "market": "away", "odd": 2.05},
            "implied_prob": "0.9655"
        }

        event_info = {
            "event_id": "1234567",
            "league_id": "1456",
            "home_team": "Toronto Maple Leafs",
            "away_team": "Montreal Canadiens",
            "league": "NHL"
        }

        await notifier.send_arbitrage_alert(arb_data, event_info)

        await notifier.close()

    asyncio.run(test())
