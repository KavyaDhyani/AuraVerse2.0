# Universal Clipboard Sync - Quick Start Guide

## Installation & Running

### Step 1: Start the Signaling Server

```bash
cd signaling_server
chmod +x start.sh
./start.sh
```

Or manually:
```bash
cd signaling_server
pip install -r requirements.txt
python server.py
```

Server will start on `http://localhost:5000`

### Step 2: Start Client on Device 1

Open a new terminal:

```bash
cd client
chmod +x start.sh
./start.sh --device-name "My Laptop"
```

Or manually:
```bash
cd client
pip install -r requirements.txt
python main.py --device-name "My Laptop"
```

### Step 3: Start Client on Device 2

Open another terminal (or on different machine):

```bash
cd client
./start.sh --device-name "My Desktop"
```

### Step 4: Pair Devices

1. On **Device 1**: Press `a` to show QR code
2. On **Device 2**: Press `a`, scan/enter code from Device 1
3. Devices will automatically pair and connect!

### Step 5: Test Clipboard Sync

1. Copy text on Device 1
2. Check Device 2 - clipboard should update automatically!
3. Copy text on Device 2
4. Check Device 1 - it syncs both ways!

## TUI Commands

- `a` - Add new device (pair)
- `r` - Remove device (unpair)
- `h` - View clipboard history
- `s` - Settings
- `q` - Quit

## Troubleshooting

### Server not starting?
- Check port 5000 is not in use: `lsof -i :5000`
- Try different port: `PORT=5001 python server.py`

### Client can't connect?
- Ensure server is running
- Check server URL: `curl http://localhost:5000/health`
- Update config if needed: `~/.clipboard-sync/config.json`

### Dependencies failing?
Make sure you have Python 3.8+:
```bash
python3 --version
pip install --upgrade pip
```

## Testing Across Networks

### Option 1: Use ngrok (easiest)
```bash
# In server terminal
ngrok http 5000
```

Use the ngrok URL in client:
```bash
python main.py --server-url "https://your-id.ngrok.io"
```

### Option 2: Deploy to Heroku
```bash
cd signaling_server
heroku create
git push heroku main
```

Use Heroku URL in client.

## Logs

- Client logs: `~/.clipboard-sync/client.log`
- Enable debug: `python main.py --debug`

## Data Storage

All data stored locally in: `~/.clipboard-sync/`
- `config.json` - Configuration
- `clipboard_sync.db` - SQLite database (devices, history, queue)
- `client.log` - Application logs

## Clean Start

To reset everything:
```bash
rm -rf ~/.clipboard-sync/
```

Next run will create fresh config and database.

## Demo Mode

Quick test on same machine:
```bash
# Terminal 1: Server
cd signaling_server && python server.py

# Terminal 2: Client 1
cd client && python main.py --device-name "Device1"

# Terminal 3: Client 2
cd client && python main.py --device-name "Device2"
```

Then pair and test clipboard sync!
