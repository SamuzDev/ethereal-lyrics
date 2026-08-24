#!/usr/bin/env bash

# ethereal-lyrics installer
# Usage: curl -fsSL https://raw.githubusercontent.com/SamuzDev/ethereal-lyrics/main/install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
DIM='\033[2m'
NC='\033[0m'

# Constants
REPO="SamuzDev/ethereal-lyrics"
INSTALL_DIR="$HOME/.local/share/ethereal-lyrics"
BIN_DIR="$HOME/.local/bin"

# Helpers
info() { echo -e "${BLUE}▸${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Check dependencies
check_deps() {
    local missing=()
    
    command -v python3 &> /dev/null || missing+=("python3")
    command -v pip3 &> /dev/null || missing+=("pip3")
    command -v git &> /dev/null || missing+=("git")
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing: ${missing[*]}. Install them first."
    fi
}

# Install
install() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                                                                                                ║${NC}"
    echo -e "${PURPLE}║${CYAN} ██████ █████ █   █ █████ ████  █████  ███  █        █     █   █ ████  ███  ███   ████              ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN} █░░░░░ ░█░░░█░  █░█░░░░░█░░░█ █░░░░░█ ░░█ █░       █░     █ ░ █░░░░█  █░░█ ░░░ █ ░░░░             ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN} ████░░░ █░░░█████░████░░████░░████░░█████░█░░      █░░     █ ░ ████░░ █░░█░ ░░░ ███░░░            ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN} █░░░░   █░░ █░░░█░█░░░░ █░░█░ █░░░░ █░░░█░█░░      █░░     █░ ░█░░█░ ░█░░█░░     ░░█              ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN} █████░  █░░ █░░░█░█████░█░░░█░█████░█░░░█░█████    █████   █░░ █░░░█░███░ ███  ████░░             ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}  ░░░░░   ░░  ░░  ░░░░░░░ ░░  ░ ░░░░░ ░░  ░░░░░░░    ░░░░░   ░░  ░░  ░ ░░░  ░░░  ░░░░ ░            ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}   ░░░░░   ░   ░   ░ ░░░░░ ░   ░ ░░░░░ ░   ░ ░░░░░    ░░░░░   ░   ░   ░ ░░░  ░░░  ░░░░             ${PURPLE}║${NC}"
    echo -e "${PURPLE}║                                                                                                ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Check dependencies
    info "Checking dependencies..."
    check_deps
    success "Dependencies OK"
    
    # Remove old installation
    if [ -d "$INSTALL_DIR" ]; then
        info "Removing old installation..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Clone repository
    info "Downloading ethereal-lyrics..."
    git clone --depth 1 "https://github.com/${REPO}.git" "$INSTALL_DIR" 2>/dev/null
    
    # Create virtual environment
    info "Setting up Python environment..."
    cd "$INSTALL_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    info "Installing dependencies..."
    pip install -e . --quiet --disable-pip-version-check
    
    # Create wrapper script
    info "Creating launcher..."
    mkdir -p "$BIN_DIR"
    cat > "$BIN_DIR/ethereal-lyrics" << 'EOF'
#!/bin/bash
source "$HOME/.local/share/ethereal-lyrics/venv/bin/activate"
python -m src.main "$@"
EOF
    chmod +x "$BIN_DIR/ethereal-lyrics"
    
    # Check if bin is in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        warn "Add to your shell config:"
        echo -e "  ${DIM}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    fi
    
    echo ""
    success "Installation complete!"
    echo ""
    echo -e "  Run: ${WHITE}ethereal-lyrics${NC}"
    echo ""
}

# Uninstall
uninstall() {
    echo ""
    info "Uninstalling ethereal-lyrics..."
    
    rm -f "$BIN_DIR/ethereal-lyrics"
    rm -rf "$INSTALL_DIR"
    
    success "Uninstalled!"
    echo ""
}

# Main
case "${1:-install}" in
    install) install ;;
    uninstall) uninstall ;;
    *)
        echo "Usage: $0 [install|uninstall]"
        exit 1
        ;;
esac