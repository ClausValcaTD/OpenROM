#!/bin/bash
echo "========================================"
echo "  OpenROM Build Script - macOS"
echo "  M5 Dev"
echo "========================================"

set -e

# Detect architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

# Install dependencies
echo "[1/3] Installing dependencies..."
pip install -r requirements.txt
pip install "pyinstaller>=6.0.0"

# Build
echo "[2/3] Building app bundle..."
pyinstaller \
  --noconfirm \
  --onefile \
  --windowed \
  --name "OpenROM" \
  --add-data "assets:assets" \
  --target-arch "$ARCH" \
  main.py

# Done
echo ""
echo "[3/3] Done!"
if [ -f "dist/OpenROM" ]; then
    echo "✅ dist/OpenROM ($ARCH) is ready!"
    # اعمل zip جاهز للـ release
    cd dist
    zip "OpenROM_macOS_${ARCH}.zip" OpenROM
    echo "📦 dist/OpenROM_macOS_${ARCH}.zip is ready for release!"
else
    echo "❌ Build failed — check errors above"
    exit 1
fi
