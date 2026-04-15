# Maintainer: carlos-garcia <carlos.garcia83@gmail.com>
pkgname=piuio2key
pkgver=1.0.0
pkgrel=1
pkgdesc="PIU IO Bridge - Maps PIUIO/LXIO arcade inputs to keyboard events"
arch=('any')
url="https://github.com/carlos-garcia/PIUIO2Key-Linux"
license=('MIT')
depends=(
    'python'
    'python-evdev'
    'python-pyusb'
)
optdepends=(
    'python-pystray: System tray icon support'
    'python-pillow: Icon generation'
)
install="$pkgname.install"
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('7092ce8619c3f06e724ec1418aae7dacef3e6db81ad2beee6d661165a966f26f')

# For git version, use this instead:
# source=("git+$url.git")
# sha256sums=('SKIP')

package() {
    cd "$srcdir/PIUIO2Key-Linux-$pkgver"
    
    # Install Python package
    install -dm755 "$pkgdir/usr/lib/$pkgname"
    cp -r piubridge "$pkgdir/usr/lib/$pkgname/"
    install -Dm755 piu_bridge.py "$pkgdir/usr/lib/$pkgname/piu_bridge.py"
    install -Dm644 default.ini "$pkgdir/usr/lib/$pkgname/default.ini"
    
    # Install launcher script
    install -dm755 "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/$pkgname" << 'EOF'
#!/bin/bash
exec python3 /usr/lib/piuio2key/piu_bridge.py "$@"
EOF
    chmod 755 "$pkgdir/usr/bin/$pkgname"
    
    # Install udev rules
    install -Dm644 /dev/stdin "$pkgdir/usr/lib/udev/rules.d/99-piuio.rules" << 'EOF'
# PIUIO/LXIO arcade IO boards — allow user access to USB device nodes

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

    # Install modules-load.d config for uinput
    install -Dm644 /dev/stdin "$pkgdir/usr/lib/modules-load.d/$pkgname.conf" << 'EOF'
uinput
EOF

    # Install desktop file
    install -Dm644 /dev/stdin "$pkgdir/usr/share/applications/$pkgname.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=PIU IO Bridge
Comment=Map arcade pad inputs to keyboard
Exec=/usr/bin/piuio2key --gui
Icon=piuio2key
Terminal=false
Categories=Game;Utility;
Keywords=piu;pump;arcade;dance;
EOF

    # Generate and install icon (if make_icon.py exists)
    if [ -f piubridge/gui/make_icon.py ]; then
        python3 piubridge/gui/make_icon.py || true
        if [ -f piubridge/gui/icon.png ]; then
            install -Dm644 piubridge/gui/icon.png "$pkgdir/usr/share/pixmaps/$pkgname.png"
        fi
    fi
}
