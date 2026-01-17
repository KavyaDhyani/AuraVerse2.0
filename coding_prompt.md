## UNIVERSAL CLIPBOARD SYNC - WebRTC Implementation Prompt

### PROJECT OVERVIEW
Build a cross-platform, internet-based clipboard synchronization system using WebRTC that enables real-time clipboard sharing between paired devices across different networks, operating systems, and geographic locations.

**Core Technology Stack:**
- WebRTC (peer-to-peer communication)
- Python 3.8+ with aiortc library
- Flask + WebSocket (lightweight signaling server)
- TUI (Terminal User Interface) using Rich
- QR Code generation for device pairing
- End-to-end encryption (DTLS-SRTP built into WebRTC)

---

## SYSTEM ARCHITECTURE

### Signaling Server (Minimal, Stateless)
- Does NOT store clipboard data
- Does NOT see or decrypt clipboard content
- Only handles: device registration, SDP/ICE forwarding, peer discovery
- Deployed on free tier (Heroku, Replit, or local)

### Client Application (Each Device)
- WebRTC PeerConnection manager
- Clipboard monitor and synchronizer
- Device pairing handler
- Offline queue manager
- TUI for user interaction

### Communication Flow
1. **Signaling Phase**: Exchange connection metadata via WebSocket (encrypted HTTPS)
2. **ICE Gathering**: Discover connection paths via free STUN/TURN servers
3. **Direct P2P**: Establish encrypted RTC Data Channel (DTLS-SRTP)
4. **Data Transfer**: Clipboard sync via encrypted tunnel (server never sees data)

---

## REQUIRED FUNCTIONS & FILES

### Directory Structure
```
universal-clipboard-sync/
│
├── signaling_server/
│   ├── requirements.txt
│   ├── server.py                 # Flask WebSocket signaling server
│   ├── handlers.py               # WebSocket message handlers
│   ├── device_registry.py        # In-memory device registry
│   └── config.py                 # Server configuration
│
├── client/
│   ├── requirements.txt
│   ├── main.py                   # Entry point
│   ├── config.py                 # Client configuration
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── webrtc_manager.py     # PeerConnection lifecycle
│   │   ├── data_channel.py       # RTC Data Channel handler
│   │   ├── signaling_client.py   # WebSocket signaling
│   │   └── ice_config.py         # STUN/TURN servers config
│   │
│   ├── clipboard/
│   │   ├── __init__.py
│   │   ├── monitor.py            # Monitor clipboard changes
│   │   ├── sync_engine.py        # Sync logic & conflict resolution
│   │   ├── offline_queue.py      # Queue for offline updates
│   │   └── history.py            # Local clipboard history storage
│   │
│   ├── pairing/
│   │   ├── __init__.py
│   │   ├── pairing_manager.py    # Device pairing logic
│   │   ├── qr_generator.py       # QR code generation
│   │   ├── device_registry.py    # Local paired devices database
│   │   └── security.py           # Encryption for device IDs
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── tui.py                # Terminal User Interface (Rich)
│   │   ├── screens.py            # TUI screen components
│   │   └── handlers.py           # User input handlers
│   │
│   └── storage/
│       ├── __init__.py
│       ├── database.py           # Local SQLite for paired devices & history
│       └── encryption.py         # Encrypt sensitive data locally
│
├── tests/
│   ├── __init__.py
│   ├── test_webrtc.py
│   ├── test_pairing.py
│   └── test_sync.py
│
└── README.md                      # Documentation
```

---

## CORE FUNCTION SPECIFICATIONS

### SIGNALING SERVER (`signaling_server/server.py`)

**Functions:**
- `initialize_server()` → Start Flask app + WebSocket
- `register_device(device_id, device_name, device_type)` → Add device to registry
- `unregister_device(device_id)` → Remove device from registry
- `get_paired_devices(device_id)` → Return list of devices this device can pair with
- `forward_sdp_offer(from_device, to_device, sdp)` → Forward SDP offer
- `forward_sdp_answer(from_device, to_device, sdp)` → Forward SDP answer
- `forward_ice_candidate(from_device, to_device, candidate)` → Forward ICE candidates
- `handle_disconnect(device_id)` → Mark device offline
- `broadcast_device_status(device_id, status)` → Notify all devices of online/offline change

**Routes:**
- `POST /register` - Device registration
- `WS /ws` - WebSocket for SDP/ICE/status
- `GET /devices` - List online devices
- `POST /unpair` - Remove pairing relationship
- `GET /health` - Server health check

---

### CLIENT CORE (`client/core/webrtc_manager.py`)

**Functions:**
- `create_peer_connection()` → Initialize RTCPeerConnection with STUN/TURN
- `create_offer(peer_device_id)` → Generate SDP offer for new connection
- `handle_offer(sdp_offer)` → Process incoming SDP offer
- `create_answer(sdp_offer)` → Generate SDP answer
- `handle_answer(sdp_answer)` → Apply remote SDP answer
- `add_ice_candidate(candidate)` → Add ICE candidate
- `handle_ice_candidate(candidate)` → Process incoming ICE candidate
- `wait_for_connection_ready()` → Block until P2P connection established
- `close_peer_connection(peer_id)` → Gracefully close connection
- `get_connection_state(peer_id)` → Return connection status
- `handle_connection_state_change()` → Callback for state changes

**Connection States:**
- `connecting` → ICE gathering in progress
- `connected` → P2P established, ready for data
- `disconnected` → Temporary network issue
- `failed` → Connection failed, retry or fallback
- `closed` → Connection terminated

---

### DATA CHANNEL (`client/core/data_channel.py`)

**Functions:**
- `create_data_channel(peer_id, channel_name='clipboard')` → Create RTC Data Channel
- `handle_data_channel_open()` → Callback when channel opens
- `send_clipboard_data(peer_id, content, metadata)` → Send clipboard via channel
- `handle_incoming_message(message)` → Process incoming clipboard update
- `handle_data_channel_close()` → Cleanup on channel close
- `handle_data_channel_error(error)` → Error handling
- `is_channel_open(peer_id)` → Check if channel ready

**Message Format (JSON over encrypted tunnel):**
```json
{
  "type": "clipboard_update",
  "timestamp": 1705434600,
  "device_id": "device-a-abc123",
  "device_name": "My Laptop",
  "content": "clipboard content here",
  "content_type": "text",
  "sequence_number": 42
}
```

---

### SIGNALING CLIENT (`client/core/signaling_client.py`)

**Functions:**
- `connect_to_signaling_server(server_url)` → WebSocket connection
- `register_device(device_id, device_name, device_type)` → Tell server about us
- `request_peer_list()` → Get list of paired devices
- `send_sdp_offer(to_device_id, sdp)` → Send offer via server
- `send_sdp_answer(to_device_id, sdp)` → Send answer via server
- `send_ice_candidate(to_device_id, candidate)` → Send ICE via server
- `handle_incoming_offer(from_device_id, sdp)` → Receive offer
- `handle_incoming_answer(from_device_id, sdp)` → Receive answer
- `handle_incoming_ice(from_device_id, candidate)` → Receive ICE
- `broadcast_status(status)` → Tell server we're online/offline
- `handle_device_status_change(device_id, status)` → React to peer status
- `disconnect_from_server()` → Graceful disconnect

---

### CLIPBOARD MONITOR (`client/clipboard/monitor.py`)

**Functions:**
- `start_monitoring()` → Begin clipboard polling (500ms interval)
- `stop_monitoring()` → Stop clipboard monitor
- `get_current_clipboard()` → Read OS clipboard (cross-platform)
- `on_clipboard_change(content)` → Callback when clipboard changes
- `should_sync(content)` → Filter what gets synced (ignore small/duplicate)
- `set_clipboard(content)` → Write to OS clipboard (cross-platform)
- `is_clipboard_changed()` → Compare against last known state

**Platform-Specific Implementations:**
- Windows: Use `pyperclip` or `win32clipboard`
- Linux: Use `xclip` or `xsel`
- macOS: Use `pbcopy`/`pbpaste`
- Android: (Future) Use native Android APIs

---

### SYNC ENGINE (`client/clipboard/sync_engine.py`)

**Functions:**
- `sync_to_peer(peer_id, clipboard_content)` → Send to single peer
- `sync_to_all_peers(clipboard_content)` → Broadcast to all connected peers
- `receive_from_peer(peer_id, content, timestamp)` → Process incoming clipboard
- `resolve_conflict(local_content, remote_content, local_time, remote_time)` → Handle simultaneous updates
- `queue_sync_if_offline(peer_id, content)` → Save for later if peer offline
- `retry_offline_syncs()` → Send queued items when peer reconnects
- `apply_filters(content)` → Apply user-configured sync filters
- `should_update_local_clipboard(content, source)` → Decide if we update local clipboard

**Conflict Resolution Strategy:**
- Last-write-wins: Compare timestamps, newer content wins
- Sequence numbering: Track update order
- User preference: Configurable (accept all, prompt, reject remote)

---

### OFFLINE QUEUE (`client/clipboard/offline_queue.py`)

**Functions:**
- `enqueue_update(peer_id, content, timestamp)` → Add to queue
- `get_queued_updates(peer_id)` → Retrieve pending updates
- `clear_queue(peer_id)` → Remove all queued items
- `is_peer_offline(peer_id)` → Check peer status
- `flush_queue(peer_id)` → Send all queued items to peer
- `save_queue_to_disk()` → Persist queue (in case of crash)
- `load_queue_from_disk()` → Restore queue on startup

**Queue Storage:**
- Local SQLite database
- Filename: `~/.clipboard-sync/offline_queue.db`
- Retained for 24 hours max
- Never sent to server

---

### CLIPBOARD HISTORY (`client/clipboard/history.py`)

**Functions:**
- `add_to_history(content, source_device, timestamp)` → Log clipboard event
- `get_history(limit=50)` → Get recent clipboard items
- `search_history(query)` → Search clipboard history
- `clear_history()` → Delete all history
- `get_history_by_device(device_id, limit=20)` → Items from specific device
- `export_history(format='json')` → Export for backup

**History Storage:**
- Local SQLite only
- Encrypted at rest if user enables
- No cloud sync
- User can delete anytime

---

### PAIRING MANAGER (`client/pairing/pairing_manager.py`)

**Functions:**
- `initiate_pairing_flow()` → Start QR code generation
- `generate_pairing_qr()` → Create QR code for this device
- `pair_with_qr(qr_data)` → Parse QR, establish pairing
- `pair_with_manual_code(pairing_code)` → Manual pairing via code
- `get_pair_request_from_peer()` → Handle incoming pairing request
- `accept_pairing(peer_id)` → Approve pairing request
- `reject_pairing(peer_id)` → Deny pairing request
- `unpair_device(peer_id)` → Remove device from paired list
- `get_paired_devices()` → List all paired devices
- `refresh_pairing_status()` → Check which devices are still paired

**Pairing Flow:**
1. User A generates QR code (contains: device-id, device-name, public-key, server-url)
2. User B scans QR code
3. B sends pairing request to A via signaling server
4. A accepts pairing
5. Both devices add each other to paired device list locally
6. Exchange happens only via signaling server (no clipboard data)
7. Future clipboard syncs happen directly P2P

---

### DEVICE REGISTRY (`client/pairing/device_registry.py`)

**Functions:**
- `add_paired_device(device_id, device_name, device_type, public_key)` → Store paired device
- `remove_paired_device(device_id)` → Unpair device
- `get_paired_device(device_id)` → Retrieve device info
- `get_all_paired_devices()` → List all paired devices
- `update_device_status(device_id, status)` → Update online/offline status
- `get_device_status(device_id)` → Get current status
- `is_device_trusted(device_id)` → Check if device is in paired list

**Stored Per Device:**
- device_id (unique identifier)
- device_name (user-friendly name)
- device_type (Windows/Linux/Mac/Android)
- public_key (for verification)
- date_paired (timestamp)
- last_seen (timestamp)
- sync_enabled (boolean)

**Storage Location:**
- `~/.clipboard-sync/devices.db` (SQLite)
- Encrypted with user password (optional)

---

### QR CODE GENERATOR (`client/pairing/qr_generator.py`)

**Functions:**
- `generate_pairing_qr()` → Create QR code for this device
- `get_qr_as_image()` → Return QR as PIL Image
- `display_qr_in_terminal()` → Show QR in TUI
- `parse_qr_data(qr_string)` → Decode QR payload
- `validate_qr_format(qr_string)` → Verify QR is valid

**QR Payload (JSON encoded):**
```json
{
  "device_id": "device-a-abc123",
  "device_name": "Alice's Laptop",
  "device_type": "Windows",
  "server_url": "https://signaling-server.com",
  "public_key": "-----BEGIN PUBLIC KEY-----...",
  "qr_version": "1.0"
}
```

---

### SECURITY (`client/pairing/security.py`)

**Functions:**
- `generate_device_keypair()` → Create RSA keypair for device
- `sign_device_id(device_id, private_key)` → Create signature
- `verify_device_signature(device_id, signature, public_key)` → Verify identity
- `derive_shared_secret(peer_public_key)` → For future encryption
- `hash_device_id(device_id)` → One-way hash for comparison
- `encrypt_local_data(data, password)` → Encrypt sensitive local storage
- `decrypt_local_data(encrypted_data, password)` → Decrypt on access

**Security Notes:**
- Device ID is cryptographically signed to prevent spoofing
- WebRTC provides DTLS-SRTP encryption automatically
- No passwords transmitted over network
- Local storage encrypted at rest (optional)

---

### LOCAL DATABASE (`client/storage/database.py`)

**Functions:**
- `initialize_database()` → Create SQLite tables
- `save_paired_device(device_info)` → Store device
- `load_paired_devices()` → Retrieve all paired devices
- `save_clipboard_item(content, source, timestamp)` → Log clipboard
- `load_clipboard_history(limit)` → Get recent items
- `save_offline_queue_item(peer_id, content)` → Queue for offline
- `load_offline_queue(peer_id)` → Retrieve queued items
- `delete_paired_device(device_id)` → Remove device
- `clear_all_data()` → Nuclear option (for uninstall)

**Tables:**
- `paired_devices` - device_id, name, type, public_key, date_paired, status
- `clipboard_history` - id, content, source_device_id, timestamp, content_type
- `offline_queue` - id, peer_device_id, content, timestamp, retry_count
- `sync_preferences` - key, value (user settings)

---

### TUI SCREENS (`client/ui/screens.py`)

**Main Dashboard Screen:**
- List all paired devices with status indicator (🟢 online / 🔴 offline / ⏳ connecting)
- Last synced time for each device
- Current clipboard preview (first 100 chars)
- Quick action buttons

**Screens to Implement:**

1. **Home/Dashboard**
   - Paired devices list with status
   - Sync statistics (today's syncs, total history items)
   - Quick actions (add device, settings, help)

2. **Paired Devices Screen**
   - List all paired devices
   - Status indicator (online/offline/connecting)
   - Last sync time
   - Device type icon
   - Actions: Remove, Disable sync, View info

3. **Add Device Screen**
   - Show generated QR code
   - "Scan QR from other device" instruction
   - Option to display pairing code
   - Manual code entry field

4. **Remove Device Screen**
   - Confirm unpair
   - Option to keep history or delete

5. **Clipboard History Screen**
   - Recent items (with timestamp & source device)
   - Search functionality
   - Copy to current clipboard
   - Delete item

6. **Settings Screen**
   - Device name
   - Auto-sync toggle
   - Sync filters (file size limit, etc.)
   - History retention (days)
   - Encryption toggle
   - Export/import settings

7. **Connection Status Screen**
   - Current connection state
   - NAT type detected
   - STUN/TURN server info
   - Bandwidth usage
   - Debug logs

---

### TUI HANDLERS (`client/ui/handlers.py`)

**Functions:**
- `handle_key_input(key)` → Process user keyboard input
- `handle_device_selection(device_id)` → React to device click
- `handle_add_device()` → Show pairing flow
- `handle_remove_device(device_id)` → Confirm unpair
- `handle_settings_change(key, value)` → Update configuration
- `handle_search_query(query)` → Search history
- `refresh_ui_on_device_status_change(device_id, status)` → Update display
- `show_notification(message, level)` → Display messages
- `confirm_action(message)` → Show yes/no dialog

**User Input:**
- Arrow keys to navigate
- Enter to select
- 'q' to quit
- 's' for settings
- 'a' to add device
- 'r' to remove device
- '?' for help

---

### TUI DISPLAY (`client/ui/tui.py`)

**Functions:**
- `initialize_tui()` → Set up Rich + Terminal
- `run_main_loop()` → Main event loop
- `render_home_screen()` → Draw dashboard
- `render_device_list()` → Draw device status table
- `render_history_view()` → Draw clipboard history
- `update_device_status(device_id, status)` → Live update device indicator
- `display_error(message)` → Show error popup
- `display_success(message)` → Show success notification
- `display_qr_code(qr_image)` → Render QR in terminal
- `get_user_input()` → Read keyboard/mouse input
- `refresh_display()` → Redraw screen

**TUI Components (Using Rich):**
- Tables for device list & history
- Live updating status indicators
- Colored text (red=offline, green=online, yellow=connecting)
- QR code ASCII art display
- Progress bars for syncing
- Modal dialogs for confirmations

---

### ENTRY POINT (`client/main.py`)

**Functions:**
- `parse_arguments()` → Handle CLI flags
- `load_configuration()` → Read config file
- `initialize_client()` → Set up all subsystems
- `start_background_tasks()` → Start monitoring, sync, signaling
- `start_tui()` → Launch terminal interface
- `handle_shutdown()` → Graceful cleanup on exit
- `main()` → Orchestrate startup

**CLI Arguments:**
```
--device-name "My Device"
--server-url https://signaling-server.com
--config-path ~/.clipboard-sync/config.json
--debug (enable verbose logging)
--no-tui (run headless)
```

---

### CONFIGURATION (`client/config.py`)

**Stored Configuration:**
- Device ID (auto-generated)
- Device name (user-configured)
- Server URL
- Auto-sync enabled/disabled
- Sync filters
- History retention days
- Encryption password (hashed)
- Preferred device type label

**Config File Location:**
- `~/.clipboard-sync/config.json` (JSON format)
- User-readable, manually editable
- Does NOT contain clipboard data

---

## CORE WORKFLOWS

### Workflow 1: Initial Device Pairing
```
User A (Device 1):
  1. Launch app → TUI home screen
  2. Press 'a' → "Add Device"
  3. See QR code displayed
  4. Tell User B to scan it

User B (Device 2):
  1. Launch app → TUI home screen
  2. Press 'a' → "Add Device"
  3. Scan QR code from Device 1
  4. Confirm pairing request
  5. Pairing complete!

Result:
  - Both devices have each other in paired device list
  - No clipboard data exchanged yet
  - Both devices registered with signaling server
```

### Workflow 2: First Clipboard Sync
```
User A copies text on Device 1:
  1. Clipboard monitor detects change (500ms)
  2. Determines peer (Device 2) is online
  3. Initiates WebRTC connection (if not already connected)
  4. Creates SDP offer, sends via signaling server
  5. Receives SDP answer from Device 2
  6. Exchanges ICE candidates
  7. Establishes direct P2P connection
  8. Sends clipboard data via encrypted RTC Data Channel
  9. DTLS-SRTP encrypts in-flight

Device 2 receives:
  1. Data channel receives encrypted message
  2. Decrypts automatically (DTLS-SRTP)
  3. Updates local clipboard with User A's content
  4. TUI shows "Synced from Device 1: [content preview]"

Latency: ~100-200ms
Server involvement: Minimal (only signaling)
Clipboard data stored on server: No
```

### Workflow 3: Offline Handling
```
User A copies on Device 1, but Device 2 is offline:
  1. Device 1 detects Device 2 is offline
  2. Adds clipboard to offline queue (local SQLite)
  3. Shows user: "Device 2 offline, will sync when online"
  4. No attempt to send to server (data stays local)

Later, Device 2 comes online:
  1. Device 2 reconnects to signaling server
  2. Device 1 receives notification that Device 2 is online
  3. Device 1 checks offline queue
  4. Establishes new P2P connection to Device 2
  5. Flushes queue: sends all queued items
  6. Device 2 receives & applies all updates in order
```

### Workflow 4: Device Removal
```
User wants to unpair Device 2:
  1. Press 'r' in TUI → "Remove Device"
  2. Select Device 2 from list
  3. Confirm unpair
  4. Device 2 removed from local paired device list
  5. Connection to Device 2 closed
  6. Notify signaling server (device unpairing)
  
Result:
  - Device 2 no longer appears in device list
  - No more clipboard sync to/from Device 2
  - All data about Device 2 removed from local storage
  - Can re-pair later using new QR code
```

### Workflow 5: TUI Status Updates
```
Main Screen displays:
  - Device A (My Laptop) - 🟢 Online - Last sync: 2 mins ago
  - Device B (My Phone) - 🔴 Offline - Last sync: 1 hour ago
  - Device C (Work PC) - ⏳ Connecting... - Last sync: never

When Device B comes online:
  - Status updates: 🔴 → 🟢
  - Offline queue flushes automatically
  - User sees notification: "Device B is online"

When clipboard changes:
  - Timestamp updates in real-time
  - Content preview refreshes
  - Shows which device it came from
```

---

## TECHNICAL REQUIREMENTS

### Language & Dependencies
- Python 3.8+
- aiortc (WebRTC)
- aiohttp (WebSocket client)
- Flask (signaling server)
- Rich (TUI)
- pyperclip (clipboard access)
- qrcode (QR generation)
- cryptography (encryption)
- sqlite3 (local database)
- python-dotenv (configuration)

### Cross-Platform Considerations
- Clipboard access: Platform-specific implementations
- File paths: Use `pathlib` for cross-platform paths
- Testing: Test on Windows, Linux, macOS before submission

### Code Quality Standards
- Clean code: Clear naming, small functions (< 50 lines)
- Modularity: Each file has single responsibility
- Error handling: Graceful failures, user-friendly messages
- Logging: Debug logs for troubleshooting
- Documentation: Docstrings for all functions
- No hardcoded values: Use config files

### Testing Requirements
- Unit tests for sync logic
- Integration tests for P2P connection
- Offline queue tests
- Pairing flow tests
- Error handling tests

---

## DEPLOYMENT TARGETS

### Signaling Server
- Deploy to: Heroku (free tier), Replit, or PythonAnywhere
- Auto-start with zero configuration
- No persistent storage needed (stateless)

### Client
- Run as: `python main.py`
- Works on: Windows, Linux, macOS
- Future: Package as standalone exe/dmg/snap

---

## SUCCESS CRITERIA

✅ Clipboard syncs across different networks (not LAN-only)
✅ QR code pairing works
✅ TUI shows device status (online/offline)
✅ Can remove/unpair devices
✅ Offline queue persists and syncs on reconnect
✅ No clipboard data stored on server
✅ Direct device-to-device communication (verified with Wireshark)
✅ Works cross-platform (Windows ↔ Linux minimum)
✅ Handles network failures gracefully
✅ Clean, well-documented code
✅ Judges can understand architecture & ask deep questions

---

## EVALUATION CHECKLIST FOR JUDGES

**Judge can verify:**
- [ ] Signaling server is minimal and stateless
- [ ] Clipboard data never appears in server logs
- [ ] P2P connection established before data transfer
- [ ] QR code pairing works correctly
- [ ] Offline queue persists across restarts
- [ ] Device status updates in real-time
- [ ] Unpair button removes device completely
- [ ] Works across different networks (demo)
- [ ] Code is clean, modular, well-documented
- [ ] Team can explain every architectural decision

