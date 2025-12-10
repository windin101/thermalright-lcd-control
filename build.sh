#!/bin/bash
# Build, uninstall, and install thermalright-lcd-control in one step

set -e  # Exit on any error

# Store the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================="
echo "Thermalright LCD Control - Build"
echo "=================================="
echo

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script requires sudo privileges."
    echo "Re-running with sudo..."
    exec sudo "$0" "$@"
fi

echo "[1/3] Creating package..."
bash ./create_package.sh
echo

# Copy wheel, requirements, and desktop/service files to current directory for install.sh
cp dist/*.whl . 2>/dev/null || true
cp build/thermalright-lcd-control-*/requirements.txt . 2>/dev/null || true
cp scripts/thermalright-lcd-control.desktop . 2>/dev/null || true
cp scripts/thermalright-lcd-control.service . 2>/dev/null || true
cp -r scripts/usr . 2>/dev/null || true

echo "[2/3] Uninstalling previous version..."
bash ./uninstall.sh
echo

echo "[3/3] Installing new version..."
bash ./install.sh
echo

# Clean up copied files
rm -f ./*.whl 2>/dev/null || true
rm -f ./requirements.txt 2>/dev/null || true
rm -f ./thermalright-lcd-control.desktop 2>/dev/null || true
rm -f ./thermalright-lcd-control.service 2>/dev/null || true
rm -rf ./usr 2>/dev/null || true

echo "=================================="
echo "Build complete!"
echo "=================================="
echo "Run 'thermalright-lcd-control-gui' to start the application."
