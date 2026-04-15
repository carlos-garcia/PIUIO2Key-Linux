#!/bin/bash
# Install udev rules for PIUIO/LXIO devices.
#
# Grants non-root access to the USB device nodes (so pyusb can open them)
# and to /dev/uinput (so evdev can create virtual keyboards).

set -e

RULES_FILE="/etc/udev/rules.d/99-piuio.rules"

cat <<'EOF' | sudo tee "$RULES_FILE" > /dev/null
# PIUIO/LXIO arcade IO boards — allow user access to USB device nodes
# Installed by piuio2key/linux/install-udev.sh

# PIUIO (EZ-USB FX2) — vendor control transfers
SUBSYSTEM=="usb", ATTR{idVendor}=="0547", ATTR{idProduct}=="1002", MODE="0666"

# PIUIO Button extension
SUBSYSTEM=="usb", ATTR{idVendor}=="0d2f", ATTR{idProduct}=="1010", MODE="0666"

# LXIO v1 (Andamiro PIU HID) — interrupt transfers
SUBSYSTEM=="usb", ATTR{idVendor}=="0d2f", ATTR{idProduct}=="1020", MODE="0666"

# LXIO v2
SUBSYSTEM=="usb", ATTR{idVendor}=="0d2f", ATTR{idProduct}=="1040", MODE="0666"

# Allow user access to /dev/uinput (needed to emit keyboard events without sudo)
KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"
EOF

# Load uinput module now and at boot
sudo modprobe uinput
echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf > /dev/null

# Add current user to the input group (for uinput access)
if ! groups "$USER" | grep -q "\binput\b"; then
    echo "Adding $USER to 'input' group..."
    sudo usermod -a -G input "$USER"
    NEED_LOGOUT=1
fi

sudo udevadm control --reload-rules
sudo udevadm trigger

echo ""
echo "=== Setup Complete ==="
echo "udev rules installed to $RULES_FILE"
echo "uinput module loaded and configured to load at boot"
if [ -n "$NEED_LOGOUT" ]; then
    echo ""
    echo "IMPORTANT: You must LOG OUT AND LOG BACK IN for the group change to take effect."
    echo "After that, you can run the bridge WITHOUT sudo:"
    echo "  python3 piu_bridge.py"
fi
echo ""
echo "Replug your PIUIO/LXIO device or reboot to apply USB rules."
