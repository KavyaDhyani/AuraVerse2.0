#!/bin/bash
# Installation verification script

echo "========================================"
echo "Universal Clipboard Sync - Verification"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✓${NC} Python found: $python_version"
else
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Python >= 3.8
python_check=$(python3 -c 'import sys; print(sys.version_info >= (3, 8))')
if [[ "$python_check" == "True" ]]; then
    echo -e "${GREEN}✓${NC} Python version is 3.8 or higher"
else
    echo -e "${RED}✗${NC} Python version must be 3.8 or higher"
    exit 1
fi

# Check pip
echo ""
echo "Checking pip..."
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip found"
else
    echo -e "${RED}✗${NC} pip not found. Please install pip"
    exit 1
fi

# Check project structure
echo ""
echo "Verifying project structure..."

declare -a required_files=(
    "signaling_server/server.py"
    "signaling_server/requirements.txt"
    "client/main.py"
    "client/requirements.txt"
    "README.md"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
        all_files_exist=false
    fi
done

if [[ "$all_files_exist" == false ]]; then
    echo -e "${RED}✗${NC} Some required files are missing"
    exit 1
fi

# Test imports
echo ""
echo "Testing Python imports..."

# Create temp test script
cat > /tmp/test_imports.py << 'EOF'
try:
    import sys
    import json
    import asyncio
    import logging
    import platform
    import sqlite3
    print("✓ Standard library imports OK")
except ImportError as e:
    print(f"✗ Standard library import failed: {e}")
    sys.exit(1)
EOF

python3 /tmp/test_imports.py
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✓${NC} Python standard library OK"
else
    echo -e "${RED}✗${NC} Python standard library check failed"
fi

rm /tmp/test_imports.py

# Check for required system tools
echo ""
echo "Checking optional tools..."

if command -v curl &> /dev/null; then
    echo -e "${GREEN}✓${NC} curl found (useful for testing)"
else
    echo -e "${YELLOW}⚠${NC} curl not found (optional, but recommended)"
fi

if command -v git &> /dev/null; then
    echo -e "${GREEN}✓${NC} git found"
else
    echo -e "${YELLOW}⚠${NC} git not found (optional)"
fi

# Summary
echo ""
echo "========================================"
echo "Verification Summary"
echo "========================================"
echo ""
echo -e "${GREEN}✓${NC} All core requirements met!"
echo ""
echo "Next steps:"
echo "  1. Install server dependencies:"
echo "     cd signaling_server && pip install -r requirements.txt"
echo ""
echo "  2. Install client dependencies:"
echo "     cd client && pip install -r requirements.txt"
echo ""
echo "  3. Start the server:"
echo "     cd signaling_server && ./start.sh"
echo ""
echo "  4. Start the client:"
echo "     cd client && ./start.sh"
echo ""
echo "See QUICKSTART.md for detailed instructions."
echo ""
