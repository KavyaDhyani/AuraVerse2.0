#!/usr/bin/env python3
"""View all tables in the clipboard sync database."""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

db_path = Path.home() / '.clipboard-sync' / 'clipboard_sync.db'

if not db_path.exists():
    print(f"❌ Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n" + "="*100)
print("📊 CLIPBOARD SYNC DATABASE")
print("="*100)

# 1. Paired Devices
print("\n1️⃣  PAIRED DEVICES")
print("-"*100)
cursor.execute("SELECT * FROM paired_devices")
devices = cursor.fetchall()
if devices:
    print(f"{'Device ID':<40} {'Name':<15} {'Type':<10} {'Status':<10} {'Sync':<6} {'Last Seen':<20}")
    print("-"*100)
    for row in devices:
        device_id, name, dtype, pubkey, date_paired, last_seen, sync_enabled, status = row
        last_seen_str = datetime.fromtimestamp(last_seen).strftime('%Y-%m-%d %H:%M:%S') if last_seen else 'Never'
        sync_str = "✓" if sync_enabled else "✗"
        print(f"{device_id:<40} {name:<15} {dtype:<10} {status:<10} {sync_str:<6} {last_seen_str:<20}")
else:
    print("  No paired devices")

# 2. Clipboard History (last 10)
print("\n\n2️⃣  CLIPBOARD HISTORY (Last 10)")
print("-"*100)
cursor.execute("SELECT * FROM clipboard_history ORDER BY timestamp DESC LIMIT 10")
history = cursor.fetchall()
if history:
    print(f"{'ID':<5} {'Source Device':<20} {'Timestamp':<20} {'Type':<10} {'Content (preview)':<40}")
    print("-"*100)
    for row in history:
        hist_id, content, source_device_id, timestamp, content_type = row
        time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        preview = content[:40] + "..." if len(content) > 40 else content
        preview = preview.replace('\n', ' ')
        print(f"{hist_id:<5} {source_device_id[:20]:<20} {time_str:<20} {content_type:<10} {preview:<40}")
else:
    print("  No clipboard history")

# 3. Offline Queue
print("\n\n3️⃣  OFFLINE QUEUE")
print("-"*100)
cursor.execute("SELECT * FROM offline_queue")
queue = cursor.fetchall()
if queue:
    print(f"{'ID':<5} {'Peer Device':<40} {'Timestamp':<20} {'Retries':<8} {'Content (preview)':<30}")
    print("-"*100)
    for row in queue:
        queue_id, peer_device_id, content, timestamp, retry_count = row
        time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        preview = content[:30] + "..." if len(content) > 30 else content
        preview = preview.replace('\n', ' ')
        print(f"{queue_id:<5} {peer_device_id:<40} {time_str:<20} {retry_count:<8} {preview:<30}")
else:
    print("  No items in offline queue")

# 4. Sync Preferences
print("\n\n4️⃣  SYNC PREFERENCES")
print("-"*100)
cursor.execute("SELECT * FROM sync_preferences")
prefs = cursor.fetchall()
if prefs:
    print(f"{'Key':<30} {'Value':<50}")
    print("-"*100)
    for row in prefs:
        key, value = row
        print(f"{key:<30} {value:<50}")
else:
    print("  No preferences set")

# Statistics
print("\n\n📈 STATISTICS")
print("-"*100)
cursor.execute("SELECT COUNT(*) FROM paired_devices")
total_devices = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM paired_devices WHERE status='online'")
online_devices = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM clipboard_history")
total_history = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM offline_queue")
queue_count = cursor.fetchone()[0]

print(f"  Total Paired Devices: {total_devices}")
print(f"  Online Devices: {online_devices}")
print(f"  Total History Items: {total_history}")
print(f"  Queued Items: {queue_count}")

conn.close()
print("\n" + "="*100)
print(f"📁 Database location: {db_path}")
print("="*100 + "\n")
