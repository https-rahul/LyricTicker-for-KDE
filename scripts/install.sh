#!/bin/bash
# LyricTicker for KDE — Install Script
# ------------------------------------
# Installs the plasmoid and sets up the backend as a systemd user service.

set -e  # Exit on any error

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Colour

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PLASMOID_ID="org.rahul.lyricticker"
PLASMOID_DEST="$HOME/.local/share/plasma/plasmoids/$PLASMOID_ID"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SYSTEMD_DIR/lyricticker.service"
BACKEND_MAIN="$PROJECT_DIR/backend/main.py"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     LyricTicker for KDE — Install    ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Step 1: Check Python ──────────────────────────────────────────────────────
echo -e "${YELLOW}[1/5] Checking Python...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗ Python3 not found. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# ── Step 2: Install Python dependencies ───────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/5] Installing Python dependencies...${NC}"
pip install --quiet PySide6 aiohttp dbus-next qasync
echo -e "${GREEN}✓ Dependencies installed${NC}"

# ── Step 3: Install plasmoid ──────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/5] Installing plasmoid...${NC}"

if [ ! -d "$PROJECT_DIR/plasmoid" ]; then
    echo -e "${RED}✗ plasmoid/ directory not found. Are you running this from the repo root?${NC}"
    exit 1
fi

mkdir -p "$PLASMOID_DEST"
cp -r "$PROJECT_DIR/plasmoid/contents" "$PLASMOID_DEST/"
cp "$PROJECT_DIR/plasmoid/metadata.json" "$PLASMOID_DEST/"
echo -e "${GREEN}✓ Plasmoid installed to $PLASMOID_DEST${NC}"

# ── Step 4: Install systemd user service ─────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/5] Setting up backend service...${NC}"

mkdir -p "$SYSTEMD_DIR"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=LyricTicker Backend
Documentation=https://github.com/https-rahul/LyricTicker-for-KDE
After=graphical-session.target network.target

[Service]
Type=simple
ExecStart=$(which python3) $BACKEND_MAIN
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable lyricticker
echo -e "${GREEN}✓ Service installed and enabled${NC}"

# ── Step 5: Reload Plasma shell ───────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/5] Reloading Plasma shell...${NC}"
if command -v kquitapp6 &>/dev/null; then
    kquitapp6 plasmashell
    sleep 2

    if command -v kstart6 &>/dev/null; then
        kstart6 plasmashell &
    elif command -v kstart &>/dev/null; then
        kstart plasmashell &
    else
        plasmashell &
    fi
    echo -e "${GREEN}✓ Plasma shell reloading...${NC}"
else
    echo -e "${YELLOW}⚠ Could not reload Plasma shell automatically.${NC}"
    echo "  Please log out and back in."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Installation complete!           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Start the backend:  systemctl --user start lyricticker"
echo "  2. Add the widget:     Right-click panel → Add Widgets → search 'Lyric Ticker'"
echo ""
echo "To check backend status:"
echo "  systemctl --user status lyricticker"
echo ""
echo "To view backend logs:"
echo "  journalctl --user -u lyricticker -f"
echo ""
