#!/usr/bin/env python3
"""Simple script to pair two devices for testing."""
import asyncio
import sys
from pathlib import Path

# Add client to path
sys.path.insert(0, str(Path(__file__).parent / 'client'))

from storage.database import Database
from pairing.security import Security

async def pair_devices():
    """Manually pair two device IDs in the database."""
    print("=" * 60)
    print("Device Pairing Tool")
    print("=" * 60)
    print()

    # Device IDs from your logs
    laptop_id = "b6edbd04-8412-4f60-a69f-2d8cc54700c1"

    print(f"Laptop Device ID: {laptop_id}")
    print()

    # Get Desktop device ID
    desktop_id = input("Enter Desktop Device ID (from Desktop client logs): ").strip()

    if not desktop_id:
        print("No device ID entered. Exiting.")
        return

    print()
    print("Generating keypairs for pairing...")

    # Generate keypairs
    laptop_priv, laptop_pub = Security.generate_device_keypair()
    desktop_priv, desktop_pub = Security.generate_device_keypair()

    # Initialize database
    db_path = Path.home() / '.clipboard-sync' / 'clipboard_sync.db'
    db = Database(str(db_path))
    await db.initialize_database()

    print(f"\nAdding Desktop to Laptop's paired devices...")
    await db.save_paired_device(
        device_id=desktop_id,
        device_name="Desktop",
        device_type="Linux",
        public_key=desktop_pub.decode('utf-8')
    )

    print(f"✓ Devices paired in database!")
    print()
    print("=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Restart both clients")
    print("2. Copy text on one device")
    print("3. Watch the logs for WebRTC connection establishment")
    print("4. The clipboard should sync automatically!")
    print()

if __name__ == '__main__':
    asyncio.run(pair_devices())
