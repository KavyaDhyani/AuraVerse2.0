#!/bin/bash
# Quick start script for client

echo "========================================="
echo "Universal Clipboard Sync - Client"
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
echo "Starting clipboard sync client..."
echo "Press Ctrl+C to stop"
echo ""

python main.py "$@"
