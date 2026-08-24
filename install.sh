#!/usr/bin/env bash

# ethereal-lyrics installer
# Synced Spotify lyrics for your terminal

set -e

# Colors
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
PINK='\033[1;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
WHITE='\033[1;37m'
DIM='\033[2m'
NC='\033[0m'

show_banner() {
    clear
    echo ""
    echo -e "${PURPLE}    ╔═══════════════════════════════════════════════════════════╗${NC}"
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

install() {
    echo -e "${CYAN}Installing ethereal-lyrics...${NC}\n"
    
    # Clone repo
    echo -e "${DIM}Cloning repository...${NC}"
    rm -rf /tmp/ethereal-lyrics
    git clone --depth 1 https://github.com/SamuzDev/ethereal-lyrics.git /tmp/ethereal-lyrics 2>/dev/null
    
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
    cat > ~/.local/bin/ethereal-lyrics << 'WRAPPER'
#!/bin/bash
source /tmp/ethereal-lyrics/venv/bin/activate
python -m src.main "$@"
WRAPPER
    chmod +x ~/.local/bin/ethereal-lyrics
    
    echo -e "\n${GREEN}✓ Installation complete!${NC}"
    echo -e "\n${CYAN}Run with: ${WHITE}ethereal-lyrics${NC}"
    echo -e "${DIM}Or: python -m src.main${NC}\n"
}

configure() {
    echo -e "\n${CYAN}Spotify API Configuration${NC}\n"
    
    echo -e "${DIM}Follow these steps:${NC}\n"
    echo -e "  ${YELLOW}1.${NC} Go to ${CYAN}https://developer.spotify.com/dashboard${NC}"
    echo -e "  ${YELLOW}2.${NC} Create a new app"
    echo -e "  ${YELLOW}3.${NC} Set redirect URI to: ${CYAN}http://localhost:8888/callback${NC}"
    echo -e "  ${YELLOW}4.${NC} Copy your Client ID and Client Secret\n"
    
    read -p "Client ID: " client_id
    read -p "Client Secret: " client_secret
    
    # Create .env file
    mkdir -p ~/.config/ethereal-lyrics
    cat > ~/.config/ethereal-lyrics/.env << EOF
SPOTIFY_CLIENT_ID=$client_id
SPOTIFY_CLIENT_SECRET=$client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
LYRIC_OFFSET_MS=1000
EOF
    
    echo -e "\n${GREEN}✓ Configuration saved!${NC}\n"
}

uninstall() {
    echo -e "\n${CYAN}Uninstalling ethereal-lyrics...${NC}\n"
    
    rm -f ~/.local/bin/ethereal-lyrics
    rm -rf /tmp/ethereal-lyrics
    pip3 uninstall ethereal-lyrics -y 2>/dev/null || true
    
    echo -e "\n${GREEN}✓ Uninstalled successfully${NC}\n"
}

show_menu() {
    echo -e "${CYAN}╔$(printf '═%.0s' $(seq 1 50))╗${NC}"
    echo -e "${CYAN}║${WHITE}                    OPTIONS                           ${CYAN}║${NC}"
    echo -e "${CYAN}╠$(printf '═%.0s' $(seq 1 50))╣${NC}"
    echo -e "${CYAN}║${NC}                                                          ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}[1]${NC}  Install                                           ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}[2]${NC}  Configure Spotify API                            ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${RED}[3]${NC}  Uninstall                                        ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${DIM}[4]${NC}  Exit                                             ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                          ${CYAN}║${NC}"
    echo -e "${CYAN}╚$(printf '═%.0s' $(seq 1 50))╝${NC}"
    echo ""
}

main() {
    show_banner
    
    while true; do
        show_menu
        read -p "Select option [1-4]: " choice
        
        case $choice in
            1)
                install
                ;;
            2)
                configure
                ;;
            3)
                uninstall
                ;;
            4)
                echo -e "\n${GREEN}Thanks for using ethereal-lyrics!${NC}\n"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                ;;
        esac
        
        read -p "Press Enter to continue..." _
        show_banner
    done
}

main "$@"
