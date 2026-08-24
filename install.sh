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
BINARY_NAME="ethereal-lyrics"

# Helpers
info() { echo -e "${BLUE}▸${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Detect platform
detect_platform() {
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch=$(uname -m)
    
    case "$arch" in
        x86_64|amd64) arch="amd64" ;;
        aarch64|arm64) arch="arm64" ;;
        armv7l|armhf) arch="armv7" ;;
        *) arch="$arch" ;;
    esac
    
    echo "${os}-${arch}"
}

# Get binary download URL
get_binary_url() {
    local platform=$(detect_platform)
    echo "https://github.com/${REPO}/releases/latest/download/${BINARY_NAME}-${platform}"
}

# Check if binary is available
check_binary_available() {
    local url=$(get_binary_url)
    curl -sI -L "$url" | grep -q "HTTP/.*200"
}

# Install binary
install_binary() {
    local url=$(get_binary_url)
    local platform=$(detect_platform)
    
    info "Downloading for ${platform}..."
    
    # Create bin directory if not exists
    mkdir -p "$BIN_DIR"
    
    # Download binary
    if ! curl -sL "$url" -o "$BIN_DIR/$BINARY_NAME"; then
        error "Failed to download binary. Check your internet connection."
    fi
    
    # Make executable
    chmod +x "$BIN_DIR/$BINARY_NAME"
    
    success "Binary installed to $BIN_DIR/$BINARY_NAME"
}

# Add to PATH if needed
setup_path() {
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        # Detect shell config file
        SHELL_CONFIG=""
        if [ -n "$BASH_VERSION" ]; then
            SHELL_CONFIG="$HOME/.bashrc"
        elif [ -n "$ZSH_VERSION" ]; then
            SHELL_CONFIG="$HOME/.zshrc"
        fi
        
        if [ -n "$SHELL_CONFIG" ] && [ -f "$SHELL_CONFIG" ]; then
            # Check if already in config
            if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_CONFIG" 2>/dev/null; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
                success "Added ~/.local/bin to PATH in $SHELL_CONFIG"
                echo -e "  ${DIM}Restart your shell or run: source $SHELL_CONFIG${NC}"
            fi
        else
            warn "Add to your shell config:"
            echo -e "  ${DIM}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        fi
    fi
}

# Install from source (fallback)
install_from_source() {
    info "Binary not available for $(detect_platform). Installing from source..."
    
    # Check dependencies
    local missing=()
    command -v python3 &> /dev/null || missing+=("python3")
    command -v git &> /dev/null || missing+=("git")
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing: ${missing[*]}. Install them first."
    fi
    
    # Check Python version
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
        error "Python 3.10+ required. You have: $(python3 --version 2>&1)"
    fi
    
    # Remove old installation
    if [ -d "$INSTALL_DIR" ]; then
        info "Removing old installation..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Clone repository
    info "Downloading ethereal-lyrics..."
    if ! git clone --depth 1 "https://github.com/${REPO}.git" "$INSTALL_DIR"; then
        error "Failed to download. Check your internet connection."
    fi
    
    # Create virtual environment
    info "Setting up Python environment..."
    cd "$INSTALL_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    info "Installing dependencies..."
    pip install . --quiet --disable-pip-version-check --no-cache-dir
    
    # Create wrapper script
    info "Creating launcher..."
    mkdir -p "$BIN_DIR"
    cat > "$BIN_DIR/$BINARY_NAME" << 'EOF'
#!/bin/bash
source "$HOME/.local/share/ethereal-lyrics/venv/bin/activate"
python -m src.main "$@"
EOF
    chmod +x "$BIN_DIR/$BINARY_NAME"
}

# Install
install() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                                                      ║${NC}"
    echo -e "${PURPLE}║${CYAN}      ███ █   █  ████ █████  ███  █     █             ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}       █░░██  █░█ ░░░░ ░█░░░█ ░░█ █░    █░            ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}       █░░█░█ █░░███░░░ █░░░█████░█░░   █░░           ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}       █░░█░░██░░ ░░█   █░░ █░░░█░█░░   █░░           ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}      ███░█░░ █░████░░  █░░ █░░░█░█████ █████         ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}       ░░░ ░░  ░░░░░░ ░  ░░  ░░  ░░░░░░░ ░░░░░        ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}        ░░░ ░   ░ ░░░░    ░   ░   ░ ░░░░░ ░░░░░       ${PURPLE}║${NC}"
    echo -e "${PURPLE}║                                                      ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Remove old installation
    if [ -d "$INSTALL_DIR" ]; then
        info "Removing old installation..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Try to install binary first
    if check_binary_available; then
        install_binary
    else
        install_from_source
    fi
    
    # Setup PATH
    setup_path
    
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
    
    rm -f "$BIN_DIR/$BINARY_NAME"
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