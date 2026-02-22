#!/usr/bin/env python3
"""
Project Acheron - Mobile Hotspot Authentication
Run this on your computer (connected to phone hotspot) to get cookies
"""

import asyncio
import json
import yaml
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scout import Scout


async def authenticate_and_save():
    """Authenticate via mobile hotspot and save cookies"""

    print("=" * 60)
    print("  PROJECT ACHERON - MOBILE HOTSPOT AUTHENTICATION")
    print("=" * 60)
    print()
    print("📱 Make sure you're connected to your phone's hotspot!")
    print()

    input("Press Enter when connected to mobile hotspot...")

    # Load config
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)

    print()
    print("🚀 Starting authentication...")
    print()

    # Initialize Scout (no proxy - using mobile IP directly)
    scout = Scout(config, proxy_manager=None)
    await scout.initialize()

    # Authenticate
    success = await scout.authenticate()

    if not success:
        print()
        print("❌ Authentication failed!")
        print("Check your Pinnacle credentials in config.yaml")
        await scout.close()
        return

    print()
    print("✅ Authentication successful!")
    print()

    # Get session data
    session_data = scout.get_session_data()

    # Save to file
    output_file = Path(__file__).parent.parent / 'session_data.json'
    with open(output_file, 'w') as f:
        json.dump(session_data, f, indent=2)

    print(f"💾 Session data saved to: {output_file}")
    print()
    print("📋 Session details:")
    print(f"  - Cookies: {len(session_data['cookies'])} cookies")
    print(f"  - WebSocket URL: {session_data['websocket_url']}")
    print(f"  - Expires in: {scout.time_until_expiry():.0f} seconds")
    print()
    print("🎯 Next steps:")
    print("  1. Upload session_data.json to your VPS:")
    print(f"     scp {output_file} your-vps:/app/")
    print()
    print("  2. VPS will use these cookies for WebSocket connection")
    print()
    print("  3. Re-run this script every 25 minutes OR when session expires")
    print()

    await scout.close()
    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(authenticate_and_save())
