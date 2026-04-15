"""
System tray icon entry point: builds the tray menu and runs the Qt event loop.
"""

import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .diag import DiagWindow
from .worker import BridgeWorker

# Bundled icon — icon.png is a hi-res vector-rendered version (preferred);
# icon.ico is the legacy Windows stealthdialog.ico kept as a fallback.
_ICON_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PNG = os.path.join(_ICON_DIR, "icon.png")
ICON_ICO = os.path.join(_ICON_DIR, "icon.ico")


def make_tray_icon():
    """Return the tray icon.

    Prefers the high-resolution PNG (scales crisply to any tray size).
    Falls back to the legacy ICO, then to a procedurally drawn pixmap.
    """
    for path in (ICON_PNG, ICON_ICO):
        if os.path.isfile(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon

    # Fallback: procedurally draw a yellow "PIU" on a dark circle
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(40, 40, 40))
    painter.setPen(QColor(255, 200, 0))
    painter.drawEllipse(2, 2, 60, 60)
    font = QFont("sans-serif", 16, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor(255, 200, 0))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "PIU")
    painter.end()
    return QIcon(pixmap)


def _build_keymap_menu(keymap):
    """Build the (read-only) 'Key Mapping' submenu."""
    keymap_menu = QMenu("Key Mapping")
    for pos, label in [("1P_7", "P1 UL"), ("1P_9", "P1 UR"), ("1P_5", "P1 CTR"),
                       ("1P_1", "P1 DL"), ("1P_3", "P1 DR"),
                       ("2P_7", "P2 UL"), ("2P_9", "P2 UR"), ("2P_5", "P2 CTR"),
                       ("2P_1", "P2 DL"), ("2P_3", "P2 DR")]:
        key_name = keymap.get(f"MAP_{pos}", "?")
        a = QAction(f"{label}: {key_name}")
        a.setEnabled(False)
        keymap_menu.addAction(a)
    keymap_menu.addSeparator()
    for name, label in [("MAP_CONFIG", "TEST"), ("MAP_SERVICE", "SERVICE")]:
        key_name = keymap.get(name, "?")
        a = QAction(f"{label}: {key_name}")
        a.setEnabled(False)
        keymap_menu.addAction(a)
    return keymap_menu


def run_tray(keymap, poll_hz, backend="lxio"):
    """Run the bridge with a KDE system tray icon."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray not available, falling back to terminal mode")
        if backend == "piuio":
            from ..bridge import run_bridge_piuio
            return run_bridge_piuio(keymap, poll_hz)
        from ..bridge import run_bridge_lxio
        return run_bridge_lxio(keymap, poll_hz)

    tray = QSystemTrayIcon(make_tray_icon())
    tray.setToolTip("PIU IO Bridge - Starting...")

    # Context menu
    menu = QMenu()

    status_action = QAction("Status: Starting...")
    status_action.setEnabled(False)
    menu.addAction(status_action)

    device_label = "PIUIO (direct USB)" if backend == "piuio" else "LXIO (direct USB)"
    device_action = QAction(f"Device: {device_label}")
    device_action.setEnabled(False)
    menu.addAction(device_action)

    menu.addSeparator()
    menu.addMenu(_build_keymap_menu(keymap))

    menu.addSeparator()

    diag_window = DiagWindow()
    diag_window.setWindowIcon(tray.icon())
    diag_action = QAction("Diagnostics")
    menu.addAction(diag_action)

    menu.addSeparator()

    exit_action = QAction("Exit")
    menu.addAction(exit_action)

    tray.setContextMenu(menu)
    tray.show()

    # Background worker
    worker = BridgeWorker(keymap, poll_hz, backend=backend)

    def on_status(msg):
        status_action.setText(f"Status: {msg}")
        tray.setToolTip(f"PIU IO Bridge - {msg}")

    def on_error(msg):
        status_action.setText(f"ERROR: {msg}")
        tray.setToolTip("PIU IO Bridge - ERROR")
        tray.showMessage("PIU IO Bridge", msg,
                         QSystemTrayIcon.MessageIcon.Critical, 5000)

    def on_exit():
        worker.stop()
        worker.wait(2000)
        diag_window.close()
        app.quit()

    def on_diag():
        diag_window.show()
        diag_window.raise_()
        diag_window.activateWindow()

    worker.status_changed.connect(on_status)
    worker.error_occurred.connect(on_error)
    worker.state_updated.connect(diag_window.on_state_updated)
    exit_action.triggered.connect(on_exit)
    diag_action.triggered.connect(on_diag)
    worker.start()

    ret = app.exec()
    worker.stop()
    worker.wait(2000)
    return ret
