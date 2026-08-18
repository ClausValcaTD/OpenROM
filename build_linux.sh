#!/bin/bash
echo "========================================"
echo "  OpenROM Build Script - Linux"
echo "  M5 Dev"
echo "========================================"

set -e

# Install dependencies
echo "[1/3] Installing dependencies..."
pip install -r requirements.txt
pip install "pyinstaller>=6.0.0"

# Build
echo "[2/3] Building executable..."
pyinstaller \
  --noconfirm \
  --onefile \
  --windowed \
  --name "OpenROM" \
  --add-data "assets:assets" \
  main.py

# Done
echo ""
echo "[3/3] Done!"
if [ -f "dist/OpenROM" ]; then
    echo "✅ dist/OpenROM is ready!"
else
    echo "❌ Build failed — check errors above"
    exit 1
fi
