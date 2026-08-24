#!/usr/bin/env bash

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    ETHEREAL LYRICS INSTALLER                     ║
# ║              Synced Spotify lyrics for your terminal             ║
# ╚══════════════════════════════════════════════════════════════════╝

set -e

# Colors
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
PINK='\033[1;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
WHITE='\033[1;37m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# Gradient function
gradient() {
    local text="$1"
    local len=${#text}
    local colors=("$PURPLE" "$CYAN" "$PINK" "$BLUE")
    local result=""
    for ((i=0; i<len; i++)); do
        local color_idx=$((i % ${#colors[@]}))
        result+="${colors[$color_idx]}${text:$i:1}"
    done
    result+="$NC"
    echo -e "$result"
}

# Box drawing
BOX_WIDTH=56

print_box_top() {
    echo -e "${PURPLE}╔$(printf '═%.0s' $(seq 1 $BOX_WIDTH))╗${NC}"
}

print_box_bottom() {
    echo -e "${PURPLE}╚$(printf '═%.0s' $(seq 1 $BOX_WIDTH))╝${NC}"
}

print_box_line() {
    local text="$1"
    local padding=$((BOX_WIDTH - ${#text} - 2))
    local left=$((padding / 2))
    local right=$((padding - left))
    echo -e "${PURPLE}║${NC}$(printf ' %.0s' $(seq 1 $left))${text}$(printf ' %.0s' $(seq 1 $right))${PURPLE}║${NC}"
}

print_box_line_color() {
    local text="$1"
    local color="$2"
    local padding=$((BOX_WIDTH - ${#text} - 2))
    local left=$((padding / 2))
    local right=$((padding - left))
    echo -e "${PURPLE}║${NC}$(printf ' %.0s' $(seq 1 $left))${color}${text}${NC}$(printf ' %.0s' $(seq 1 $right))${PURPLE}║${NC}"
}

print_separator() {
    echo -e "${DIM}$(printf '─%.0s' $(seq 1 $BOX_WIDTH))${NC}"
}

# Main banner
show_banner() {
    clear
    echo ""
    echo -e "${PURPLE}    ╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}    ║                                                           ║${NC}"
    echo -e "${PURPLE}    ║${CYAN}     ███████╗██████╗ ██╗   ██╗███████╗██╗     ██╗          ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${CYAN}     ██╔════╝██╔══██╗██║   ██║██╔════╝██║     ██║          ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${CYAN}     █████╗  ██████╔╝██║   ██║█████╗  ██║     ██║          ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${CYAN}     ██╔══╝  ██╔══██╗██║   ██║██╔══╝  ██║     ██║          ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${CYAN}     ██║     ██║  ██║╚██████╔╝██║     ███████╗███████╗     ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${CYAN}     ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚══════╝╚══════╝     ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${PINK}     ██████╗██╗     ██╗██████╗ ███████╗██████╗             ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${PINK}    ██╔════╝██║     ██║██╔══██╗██╔════╝██╔══██╗            ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${PINK}    ██║     ██║     ██║██████╔╝█████╗  ██████╔╝            ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${PINK}    ██║     ██║     ██║██╔═══╝ ██╔══╝  ██╔══██╗            ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${PINK}    ╚██████╗███████╗██║██║     ███████╗██║  ██║            ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║${PINK}     ╚═════╝╚══════╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝            ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║                                                           ║${NC}"
    echo -e "${PURPLE}    ║${DIM}           Synced Spotify lyrics for your terminal          ${PURPLE}║${NC}"
    echo -e "${PURPLE}    ║                                                           ║${NC}"
    echo -e "${PURPLE}    ╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check dependencies
check_deps() {
    local missing=()
    
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        missing+=("pip")
    fi
    
    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}Missing dependencies: ${missing[*]}${NC}"
        return 1
    fi
    
    return 0
}

# Install with pip (simple)
install_pip() {
    echo -e "\n${CYAN}Installing with pip...${NC}\n"
    
    # Clone repo
    echo -e "${DIM}Cloning repository...${NC}"
    git clone --depth 1 https://github.com/SamuzDev/ethereal-lyrics.git /tmp/ethereal-lyrics 2>/dev/null || {
        echo -e "${YELLOW}Repository not found on GitHub. Installing locally...${NC}"
        cp -r "$(dirname "$0")" /tmp/ethereal-lyrics
    }
    
    cd /tmp/ethereal-lyrics
    
    # Create virtual environment
    echo -e "${DIM}Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    echo -e "${DIM}Installing dependencies...${NC}"
    pip install -e . --quiet
    
    # Create wrapper script
    mkdir -p ~/.local/bin
    cat > ~/.local/bin/ethereal-lyrics << 'EOF'
#!/bin/bash
source /tmp/ethereal-lyrics/venv/bin/activate
python -m src.main "$@"
EOF
    chmod +x ~/.local/bin/ethereal-lyrics
    
    echo -e "\n${GREEN}✓ Installation complete!${NC}"
    echo -e "\n${CYAN}Run with: ${WHITE}ethereal-lyrics${NC}\n"
}

# Install globally
install_global() {
    echo -e "\n${CYAN}Installing globally...${NC}\n"
    
    # Clone repo
    echo -e "${DIM}Cloning repository...${NC}"
    git clone --depth 1 https://github.com/SamuzDev/ethereal-lyrics.git /tmp/ethereal-lyrics 2>/dev/null || {
        echo -e "${YELLOW}Repository not found on GitHub. Installing locally...${NC}"
        cp -r "$(dirname "$0")" /tmp/ethereal-lyrics
    }
    
    cd /tmp/ethereal-lyrics
    
    # Install with pip
    echo -e "${DIM}Installing package...${NC}"
    sudo pip3 install -e . --break-system-packages 2>/dev/null || pip3 install -e .
    
    echo -e "\n${GREEN}✓ Installation complete!${NC}"
    echo -e "\n${CYAN}Run with: ${WHITE}ethereal-lyrics${NC}\n"
}

# Uninstall
uninstall() {
    echo -e "\n${CYAN}Uninstalling ethereal-lyrics...${NC}\n"
    
    # Remove wrapper
    rm -f ~/.local/bin/ethereal-lyrics
    
    # Remove installation
    rm -rf /tmp/ethereal-lyrics
    
    # Uninstall package
    pip3 uninstall ethereal-lyrics -y 2>/dev/null || true
    
    echo -e "\n${GREEN}✓ Uninstalled successfully${NC}\n"
}

# Show menu
show_menu() {
    echo -e "${CYAN}╔$(printf '═%.0s' $(seq 1 50))╗${NC}"
    echo -e "${CYAN}║${WHITE}                    OPTIONS                           ${CYAN}║${NC}"
    echo -e "${CYAN}╠$(printf '═%.0s' $(seq 1 50))╣${NC}"
    echo -e "${CYAN}║${NC}                                                          ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}[1]${NC}  Quick Install (pip, local)                       ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}[2]${NC}  Global Install (requires sudo)                   ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}[3]${NC}  Configure Spotify API                            ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${RED}[4]${NC}  Uninstall                                        ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${DIM}[5]${NC}  Exit                                             ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                          ${CYAN}║${NC}"
    echo -e "${CYAN}╚$(printf '═%.0s' $(seq 1 50))╝${NC}"
    echo ""
}

# Configure Spotify
configure_spotify() {
    echo -e "\n${CYAN}╔$(printf '═%.0s' $(seq 1 50))╗${NC}"
    echo -e "${CYAN}║${WHITE}              SPOTIFY API CONFIGURATION               ${CYAN}║${NC}"
    echo -e "${CYAN}╚$(printf '═%.0s' $(seq 1 50))╝${NC}\n"
    
    echo -e "${DIM}Follow these steps:${NC}\n"
    echo -e "  ${YELLOW}1.${NC} Go to ${CYAN}https://developer.spotify.com/dashboard${NC}"
    echo -e "  ${YELLOW}2.${NC} Create a new app"
    echo -e "  ${YELLOW}3.${NC} Set redirect URI to: ${CYAN}http://localhost:8888/callback${NC}"
    echo -e "  ${YELLOW}4.${NC} Copy your Client ID and Client Secret\n"
    
    read -p "$(echo -e ${CYAN}Client\ ID:\ ${NC})" client_id
    read -p "$(echo -e ${CYAN}Client\ Secret:\ ${NC})" client_secret
    
    # Create .env file
    cat > ~/.config/ethereal-lyrics/.env << EOF
SPOTIFY_CLIENT_ID=$client_id
SPOTIFY_CLIENT_SECRET=$client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
LYRIC_OFFSET_MS=1000
EOF
    
    mkdir -p ~/.config/ethereal-lyrics
    mv .env ~/.config/ethereal-lyrics/ 2>/dev/null || true
    
    echo -e "\n${GREEN}✓ Configuration saved!${NC}\n"
}

# Main
main() {
    show_banner
    
    if ! check_deps; then
        echo -e "\n${RED}Please install missing dependencies first.${NC}\n"
        exit 1
    fi
    
    while true; do
        show_menu
        read -p "$(echo -e ${CYAN}Select\ option\ [1-5]:\ ${NC})" choice
        
        case $choice in
            1)
                install_pip
                ;;
            2)
                install_global
                ;;
            3)
                configure_spotify
                ;;
            4)
                uninstall
                ;;
            5)
                echo -e "\n${GREEN}Thanks for using ethereal-lyrics!${NC}\n"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                ;;
        esac
        
        read -p "$(echo -e ${DIM}Press\ Enter\ to\ continue...${NC})" _
        show_banner
    done
}

main "$@"
