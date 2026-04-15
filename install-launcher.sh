#!/bin/bash
# Install a KDE/GNOME application launcher for the PIU IO Bridge.
#
# Creates ~/.local/share/applications/piu-bridge.desktop pointing at the
# script and icon in this folder. After running, the bridge will appear
# in your app menu (KRunner, Plasma menu, GNOME Activities) and can be
# launched with a double-click from Dolphin/Files.

set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/piu_bridge.py"
ICON="$HERE/piubridge/gui/icon.png"
PYTHON="$(command -v python3)"

if [ ! -f "$SCRIPT" ]; then
    echo "ERROR: $SCRIPT not found"
    exit 1
fi
if [ ! -f "$ICON" ]; then
    echo "ERROR: $ICON not found (run 'python3 piubridge/gui/make_icon.py' first)"
    exit 1
fi
if [ -z "$PYTHON" ]; then
    echo "ERROR: python3 not found in PATH"
    exit 1
fi

DEST_DIR="$HOME/.local/share/applications"
DEST="$DEST_DIR/piu-bridge.desktop"

mkdir -p "$DEST_DIR"

sed \
    -e "s|@PYTHON@|$PYTHON|g" \
    -e "s|@SCRIPT@|$SCRIPT|g" \
    -e "s|@ICON@|$ICON|g" \
    -e "s|@HERE@|$HERE|g" \
    "$HERE/piu-bridge.desktop.in" > "$DEST"

chmod +x "$DEST"

# Register with the desktop environment
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database "$DEST_DIR" 2>/dev/null || true
fi

echo "=== Launcher Installed ==="
echo "  Desktop file: $DEST"
echo "  Exec:         $PYTHON $SCRIPT"
echo "  Icon:         $ICON"
echo ""
echo "You can now:"
echo "  - Find 'PIU IO Bridge' in your app menu / KRunner"
echo "  - Pin it to your taskbar or add to favorites"
echo "  - Double-click a copy on your Desktop if you place one there"
echo ""
echo "To also put it on your Desktop (KDE Plasma):"
echo "  cp '$DEST' ~/Desktop/"
echo "  (then right-click the icon and 'Allow Executing' if prompted)"
echo ""
echo "To uninstall: rm '$DEST'"
