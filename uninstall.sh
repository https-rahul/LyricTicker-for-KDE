#!/bin/bash
# LyricTicker for KDE — Uninstall Script

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PLASMOID_ID="org.rahul.lyricticker"
PLASMOID_DEST="$HOME/.local/share/plasma/plasmoids/$PLASMOID_ID"
SERVICE_FILE="$HOME/.config/systemd/user/lyricticker.service"
CACHE_FILE="$HOME/.cache/lyricticker"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║    LyricTicker for KDE — Uninstall   ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Stop and disable service
echo -e "${YELLOW}[1/3] Stopping backend service...${NC}"
systemctl --user stop lyricticker 2>/dev/null || true
systemctl --user disable lyricticker 2>/dev/null || true
rm -f "$SERVICE_FILE"
systemctl --user daemon-reload
echo -e "${GREEN}✓ Service removed${NC}"

# Remove plasmoid
echo ""
echo -e "${YELLOW}[2/3] Removing plasmoid...${NC}"
rm -rf "$PLASMOID_DEST"
echo -e "${GREEN}✓ Plasmoid removed${NC}"

# Remove cache
echo ""
echo -e "${YELLOW}[3/3] Cleaning up cache...${NC}"
rm -rf "$CACHE_FILE"
echo -e "${GREEN}✓ Cache cleared${NC}"

echo ""
echo -e "${GREEN}LyricTicker has been uninstalled.${NC}"
echo "You may want to log out and back in to fully reload the Plasma shell."
echo ""