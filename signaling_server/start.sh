#!/bin/bash
# Quick start script for signaling server

echo "========================================="
echo "Universal Clipboard Sync - Server"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "Starting signaling server..."
echo "Server will be available at http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python server.py
