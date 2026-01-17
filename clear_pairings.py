#!/usr/bin/env python3
"""Clear all paired devices from local database."""
import sqlite3
import os
from pathlib import Path

db_path = Path.home() / '.clipboard-sync' / 'clipboard_sync.db'

if not db_path.exists():
    print(f"❌ Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Show current devices
cursor.execute("SELECT device_id, device_name FROM paired_devices")
devices = cursor.fetchall()
print("\n📋 Current paired devices:")
for dev_id, name in devices:
    print(f"  {dev_id} | {name}")

# Clear all
cursor.execute("DELETE FROM paired_devices")
cursor.execute("DELETE FROM offline_queue")
conn.commit()

print(f"\n✓ Cleared {len(devices)} paired devices")
print("✓ Cleared offline queue")
print("\n✨ You can now use 'pair' command to pair devices properly!\n")

conn.close()
