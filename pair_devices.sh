#!/bin/bash
# Simple pairing script using sqlite3

echo "============================================================"
echo "Device Pairing Tool"
echo "============================================================"
echo ""

LAPTOP_ID="b6edbd04-8412-4f60-a69f-2d8cc54700c1"
DB_PATH="$HOME/.clipboard-sync/clipboard_sync.db"

echo "Laptop Device ID: $LAPTOP_ID"
echo ""

# Check if Desktop client is running and get its ID
echo "First, start the Desktop client in another terminal:"
echo "  cd client"
echo "  ./start.sh --device-name \"Desktop\" --no-tui --config-path ~/.clipboard-sync/config-desktop.json"
echo ""
read -p "Enter Desktop Device ID (from Desktop client logs): " DESKTOP_ID

if [ -z "$DESKTOP_ID" ]; then
    echo "No device ID entered. Exiting."
    exit 1
fi

echo ""
echo "Pairing devices in database..."

# Add Desktop to Laptop's paired devices
sqlite3 "$DB_PATH" <<EOF
INSERT OR REPLACE INTO paired_devices (device_id, device_name, device_type, public_key, paired_at, last_seen, status)
VALUES ('$DESKTOP_ID', 'Desktop', 'Linux', 'dummy_key', datetime('now'), datetime('now'), 'offline');
EOF

# Also add to Desktop's database if it exists
DESKTOP_DB="$HOME/.clipboard-sync/clipboard_sync-desktop.db"
if [ -f "$DESKTOP_DB" ]; then
    sqlite3 "$DESKTOP_DB" <<EOF
INSERT OR REPLACE INTO paired_devices (device_id, device_name, device_type, public_key, paired_at, last_seen, status)
VALUES ('$LAPTOP_ID', 'Laptop', 'Linux', 'dummy_key', datetime('now'), datetime('now'), 'offline');
EOF
    echo "✓ Devices paired in both databases!"
else
    echo "✓ Device paired in Laptop database!"
    echo "⚠ Desktop database not found yet (will be created when Desktop client starts)"
fi

echo ""
echo "============================================================"
echo "Next Steps:"
echo "============================================================"
echo "1. Restart both clients (Ctrl+C then re-run)"
echo "2. Watch the logs for 'Loaded X paired devices'"
echo "3. Copy text on one device"
echo "4. Look for WebRTC connection logs"
echo ""
