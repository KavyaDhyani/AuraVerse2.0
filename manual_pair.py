#!/usr/bin/env python3
"""Manually register pairing with signaling server."""
import asyncio
import socketio

async def pair_devices(server_url, device1_id, device2_id):
    """
    Register pairing between two devices with the signaling server.

    Args:
        server_url: Signaling server URL
        device1_id: First device ID
        device2_id: Second device ID
    """
    sio = socketio.AsyncClient()

    try:
        print(f"Connecting to signaling server: {server_url}")
        await sio.connect(server_url)
        print("✓ Connected")

        # Emit pairing accepted events for both devices
        print(f"\nRegistering pairing: {device1_id[:8]}... <-> {device2_id[:8]}...")

        # Device 1 accepts Device 2
        await sio.emit('pairing_accepted', {
            'from_device_id': device1_id,
            'to_device_id': device2_id
        })

        # Device 2 accepts Device 1
        await sio.emit('pairing_accepted', {
            'from_device_id': device2_id,
            'to_device_id': device1_id
        })

        await asyncio.sleep(1)  # Give server time to process

        print("✓ Pairing registered with server")
        print("\n✨ Devices are now paired on the signaling server!")
        print("   You can now use 'connect' command to establish WebRTC connection.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python3 manual_pair.py <server_url> <device1_id> <device2_id>")
        print("\nExample:")
        print("  python3 manual_pair.py http://192.168.2.98:5000 \\")
        print("    b6edbd04-8412-4f60-a69f-2d8cc54700c1 \\")
        print("    3a5b2f22-57bb-4a63-956e-ff5ebcb7b00c")
        sys.exit(1)

    server_url = sys.argv[1]
    device1_id = sys.argv[2]
    device2_id = sys.argv[3]

    asyncio.run(pair_devices(server_url, device1_id, device2_id))
