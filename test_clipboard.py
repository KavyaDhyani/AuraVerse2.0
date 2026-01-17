#!/usr/bin/env python3
"""Simple test script to verify clipboard sync without TUI."""
import asyncio
import sys
import os

# Add client directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client'))

from config import Config
from pairing.security import Security
from pairing.qr_generator import QRGenerator

async def main():
    """Generate pairing QR code for testing."""
    print("=" * 60)
    print("Universal Clipboard Sync - Device Pairing")
    print("=" * 60)
    print()

    # Get device info
    device_name = input("Enter device name (e.g., 'Laptop'): ").strip() or "TestDevice"

    # Generate device ID and keypair
    import uuid
    device_id = str(uuid.uuid4())

    print(f"\nDevice ID: {device_id}")
    print("Generating keypair...")

    private_key, public_key = Security.generate_device_keypair()
    public_key_pem = public_key.decode('utf-8')

    print("\n" + "=" * 60)
    print("QR CODE FOR PAIRING:")
    print("=" * 60)

    # Generate QR
    qr_gen = QRGenerator()
    qr_payload = {
        'device_id': device_id,
        'device_name': device_name,
        'device_type': 'Linux',
        'server_url': 'http://localhost:5000',
        'public_key': public_key_pem,
        'qr_version': '1.0'
    }

    qr_ascii = qr_gen.display_qr_in_terminal(qr_payload)
    print(qr_ascii)

    print("\n" + "=" * 60)
    print(f"Share this Device ID with other devices:")
    print(f"  {device_id}")
    print("=" * 60)
    print()

    # Instructions
    print("To pair devices:")
    print("1. Run this script on both devices")
    print("2. Copy the Device ID from one device")
    print("3. Enter it when prompted on the other device")
    print()

    pair_id = input("Enter Device ID to pair with (or press Enter to skip): ").strip()
    if pair_id:
        print(f"\nWould pair with: {pair_id}")
        print("(Pairing logic would happen here in full implementation)")

if __name__ == '__main__':
    asyncio.run(main())
