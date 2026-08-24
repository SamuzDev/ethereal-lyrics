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
PINK='\033[38;5;213m'
WHITE='\033[1;37m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# Gradient colors
GRADIENT1='\033[38;5;141m'
GRADIENT2='\033[38;5;135m'
GRADIENT3='\033[38;5;129m'

# Constants
REPO="SamuzDev/ethereal-lyrics"
INSTALL_DIR="$HOME/.local/share/ethereal-lyrics"
BIN_DIR="$HOME/.local/bin"

# Helpers
info() { echo -e "  ${BLUE}●${NC} $1"; }
success() { echo -e "  ${GREEN}✓${NC} ${BOLD}$1${NC}"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }
error() { echo -e "  ${RED}✗${NC} $1"; exit 1; }

# Spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while [ "$(ps -p $pid -o pid= 2>/dev/null)" ]; do
        for (( i=0; i<${#spinstr}; i++ )); do
            printf "\r  ${CYAN}${spinstr:$i:1}${NC} %s" "$2"
            sleep $delay
        done
    done
    printf "\r"
}

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

# Print banner
print_banner() {
    clear
    echo ""
    echo -e "${GRADIENT1}  ╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GRADIENT1}  ║                                                           ║${NC}"
    echo -e "${GRADIENT1}  ║${CYAN}    _____ _               _                  _             ${GRADIENT1}║${NC}"
    echo -e "${GRADIENT1}  ║${CYAN}   / ____| |             | |                | |            ${GRADIENT1}║${NC}"
    echo -e "${GRADIENT1}  ║${CYAN}  | (___ | |__   __ _  __| | ___  _ __   ___| |_ ___ _ __ ${GRADIENT1}║${NC}"
    echo -e "${GRADIENT1}  ║${CYAN}   \___ \| '_ \ / _\` |/ _\` |/ _ \| '_ \ / _ \ __/ _ \ '__|${GRADIENT1}║${NC}"
    echo -e "${GRADIENT1}  ║${CYAN}   ____) | | | | (_| | (_| | (_) | | | |  __/ ||  __/ |   ${GRADIENT1}║${NC}"
    echo -e "${GRADIENT1}  ║${CYAN}  |_____/|_| |_|\__,_|\__,_|\___/|_| |_|\___|\__\___|_|   ${GRADIENT1}║${NC}"
    echo -e "${GRADIENT1}  ║                                                           ║${NC}"
    echo -e "${GRADIENT2}  ║${PINK}     ${BOLD}✦ Synced Spotify lyrics for your terminal${NC}${PINK} ✦          ${GRADIENT2}║${NC}"
    echo -e "${GRADIENT1}  ║                                                           ║${NC}"
    echo -e "${GRADIENT1}  ╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Progress bar
progress_bar() {
    local current=$1
    local total=$2
    local width=40
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\r  ${CYAN}[${GREEN}"
    printf "%${filled}s" | tr ' ' '█'
    printf "${NC}"
    printf "%${empty}s" | tr ' ' '░'
    printf "${CYAN}]${NC} ${WHITE}%3d%%${NC}" "$percentage"
}

# Install
install() {
    print_banner
    
    # Check dependencies
    info "Checking dependencies..."
    check_deps
    success "All dependencies found"
    echo ""
    
    # Remove old installation
    if [ -d "$INSTALL_DIR" ]; then
        warn "Removing previous installation..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Clone repository
    info "Downloading ethereal-lyrics..."
    if git clone --depth 1 "https://github.com/${REPO}.git" "$INSTALL_DIR" 2>/dev/null; then
        success "Repository downloaded"
    else
        error "Failed to download repository"
    fi
    
    # Create virtual environment
    info "Setting up Python environment..."
    cd "$INSTALL_DIR"
    python3 -m venv venv 2>/dev/null
    source venv/bin/activate 2>/dev/null
    success "Virtual environment created"
    
    # Install dependencies
    info "Installing dependencies..."
    pip install -e . --quiet --disable-pip-version-check 2>/dev/null
    success "Dependencies installed"
    echo ""
    
    # Create wrapper script
    info "Creating launcher..."
    mkdir -p "$BIN_DIR"
    cat > "$BIN_DIR/ethereal-lyrics" << 'EOF'
#!/bin/bash
source "$HOME/.local/share/ethereal-lyrics/venv/bin/activate"
python -m src.main "$@"
EOF
    chmod +x "$BIN_DIR/ethereal-lyrics"
    success "Launcher created"
    
    # Check if bin is in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo ""
        warn "Add to your shell config:"
        echo -e "    ${DIM}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    fi
    
    echo ""
    echo -e "${GRADIENT1}  ═══════════════════════════════════════════════════════════${NC}"
    success "${BOLD}Installation complete!${NC}"
    echo ""
    echo -e "  ${CYAN}→${NC} Run: ${WHITE}ethereal-lyrics${NC}"
    echo -e "  ${CYAN}→${NC} Docs: ${WHITE}https://github.com/${REPO}${NC}"
    echo -e "${GRADIENT1}  ═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Uninstall
uninstall() {
    print_banner
    
    info "Uninstalling ethereal-lyrics..."
    
    rm -f "$BIN_DIR/ethereal-lyrics"
    rm -rf "$INSTALL_DIR"
    
    success "Uninstalled successfully!"
    echo ""
}

# Main
case "${1:-install}" in
    install) install ;;
    uninstall) uninstall ;;
    *)
        echo -e "${RED}Usage: $0 [install|uninstall]${NC}"
        exit 1
        ;;
esac