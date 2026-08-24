#!/usr/bin/env bash

# Build script for ethereal-lyrics binaries
# Usage: ./scripts/build.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}▸${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }

# Check dependencies
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Create build directory
BUILD_DIR="dist"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

info "Installing PyInstaller..."
pip install pyinstaller --quiet --disable-pip-version-check

info "Building binary..."
pyinstaller \
    --onefile \
    --name ethereal-lyrics \
    --add-data "src:src" \
    --hidden-import src.main \
    --hidden-import src.config \
    --hidden-import src.terminal_ui \
    --hidden-import src.lyrics_fetcher \
    --hidden-import src.local_spotify \
    --hidden-import src.spotify_client \
    --clean \
    --noconfirm \
    src/main.py 2>/dev/null

# Move binary to dist
mv dist/ethereal-lyrics "$BUILD_DIR/"
rm -rf build ethereal-lyrics.spec

success "Binary built: $BUILD_DIR/ethereal-lyrics"
echo ""
echo "Platform: $(uname -s)-$(uname -m)"
echo "Size: $(du -h "$BUILD_DIR/ethereal-lyrics" | cut -f1)"