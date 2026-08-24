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
MIN_PYTHON_VERSION="3.10"

# Helpers
info() { echo -e "${BLUE}▸${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

# Get install command for missing packages
get_install_cmd() {
    local distro=$(detect_distro)
    case "$distro" in
        ubuntu|debian) echo "sudo apt install -y" ;;
        fedora) echo "sudo dnf install -y" ;;
        arch|manjaro) echo "sudo pacman -S --noconfirm" ;;
        opensuse*|sles) echo "sudo zypper install -y" ;;
        alpine) echo "sudo apk add" ;;
        *) echo "Install manually" ;;
    esac
}

# Check Python version
check_python_version() {
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    local major=$(echo "$python_version" | cut -d. -f1)
    local minor=$(echo "$python_version" | cut -d. -f2)
    
    if [ -z "$major" ] || [ -z "$minor" ]; then
        return 1
    fi
    
    if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
        return 0
    fi
    return 1
}

# Check if venv module is available
check_venv_module() {
    python3 -c "import venv" 2>/dev/null
}

# Check dependencies
check_deps() {
    local missing=()
    local install_cmd=$(get_install_cmd)
    
    # Check git
    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi
    
    # Check python3
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    elif ! check_python_version; then
        error "Python 3.10+ required. You have: $(python3 --version 2>&1)\n  ${DIM}Install: ${install_cmd} python3${NC}"
    fi
    
    # Check venv module
    if command -v python3 &> /dev/null && ! check_venv_module; then
        warn "Missing python3-venv module. Attempting to install..."
        case "$(detect_distro)" in
            ubuntu|debian) 
                if sudo apt install -y python3-venv 2>/dev/null; then
                    success "python3-venv installed"
                else
                    error "Missing python3-venv. Install manually:\n  ${DIM}sudo apt install python3-venv${NC}"
                fi
                ;;
            fedora)
                if sudo dnf install -y python3-virtualenv 2>/dev/null; then
                    success "python3-virtualenv installed"
                else
                    error "Missing python3-virtualenv. Install manually:\n  ${DIM}sudo dnf install python3-virtualenv${NC}"
                fi
                ;;
            arch|manjaro)
                # python3-venv is included with python on Arch
                ;;
            *)
                error "Missing venv module. Install python3-venv or python3-virtualenv for your distro"
                ;;
        esac
    fi
    
    # Check dbus-python (optional but recommended)
    if command -v python3 &> /dev/null; then
        if ! python3 -c "import dbus" 2>/dev/null; then
            warn "dbus-python not found. Local Spotify detection may not work."
            echo -e "  ${DIM}To enable: pip install dbus-python (may need libdbus-1-dev)${NC}"
        fi
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing: ${missing[*]}\n  ${DIM}Install: ${install_cmd} ${missing[*]}${NC}"
    fi
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
    
    # Check dependencies
    info "Checking dependencies..."
    check_deps
    success "All dependencies found"
    
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
    cat > "$BIN_DIR/ethereal-lyrics" << 'EOF'
#!/bin/bash
source "$HOME/.local/share/ethereal-lyrics/venv/bin/activate"
python -m src.main "$@"
EOF
    chmod +x "$BIN_DIR/ethereal-lyrics"
    
    # Add to PATH if needed
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