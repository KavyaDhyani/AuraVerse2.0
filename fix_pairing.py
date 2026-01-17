#!/usr/bin/env python3
"""Fix duplicate device entries in the database."""
import sqlite3
import os
from pathlib import Path

db_path = Path.home() / '.clipboard-sync' / 'clipboard_sync.db'

if not db_path.exists():
    print(f"❌ Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Show current paired devices
print("\n📋 Current paired devices:")
print("-" * 80)
cursor.execute("SELECT device_id, device_name, device_type, status FROM paired_devices")
devices = cursor.fetchall()
for dev_id, name, dev_type, status in devices:
    print(f"  {dev_id} | {name} | {dev_type} | {status}")

# Remove devices with 'p' prefix (these are incorrect)
print("\n🧹 Removing duplicate entries with 'p' prefix...")
cursor.execute("DELETE FROM paired_devices WHERE device_id LIKE 'p%'")
deleted = cursor.rowcount
print(f"  Deleted {deleted} duplicate entries")

# Clean up offline queue for invalid device IDs
print("\n🧹 Cleaning offline queue...")
cursor.execute("DELETE FROM offline_queue WHERE peer_device_id LIKE 'p%'")
queue_deleted = cursor.rowcount
print(f"  Removed {queue_deleted} queued items for invalid devices")

conn.commit()

# Show remaining devices
print("\n✅ Remaining paired devices:")
print("-" * 80)
cursor.execute("SELECT device_id, device_name, device_type, status FROM paired_devices")
devices = cursor.fetchall()
for dev_id, name, dev_type, status in devices:
    print(f"  {dev_id} | {name} | {dev_type} | {status}")

print(f"\n💾 Database updated: {db_path}")

# Show this device's ID
your_device_id = "b6edbd04-8412-4f60-a69f-2d8cc54700c1"
print(f"\n📱 Your device ID: {your_device_id}")

if devices:
    print("\n🔗 To properly pair devices, on the OTHER device run:")
    print(f"\n   python3 -c \"")
    print(f"import sqlite3, time, os")
    print(f"conn = sqlite3.connect(os.path.expanduser('~/.clipboard-sync/clipboard_sync.db'))")
    print(f"conn.execute('''INSERT OR REPLACE INTO paired_devices ")
    print(f"    (device_id, device_name, device_type, public_key, date_paired, last_seen, sync_enabled, status)")
    print(f"    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',")
    print(f"    ('{your_device_id}', 'Laptop', 'laptop', None, time.time(), time.time(), 1, 'online'))")
    print(f"conn.commit()")
    print(f"print('✓ Paired with Laptop')")
    print(f"\"")

conn.close()
print("\n✨ Done! Restart your client for changes to take effect.\n")
