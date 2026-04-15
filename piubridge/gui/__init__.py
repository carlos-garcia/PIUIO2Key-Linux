"""
Optional Qt-based GUI (system tray icon + diagnostics window).

If PyQt6 is not installed, HAS_QT is False and run_tray is None;
the CLI falls back to terminal-only mode.
"""

import os

HAS_QT = False
run_tray = None

try:
    from PyQt6 import QtCore  # noqa: F401  (ensure the suite is importable)
    HAS_QT = True
except ImportError:
    pass

if HAS_QT:
    from .tray import run_tray  # noqa: F401  (re-exported)


def has_display():
    """Return True if a graphical session (X11 or Wayland) is available."""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def show_error_dialog(title, message):
    """Show a modal error dialog. No-op if Qt/display unavailable."""
    if not (HAS_QT and has_display()):
        return
    import sys
    from PyQt6.QtWidgets import QApplication, QMessageBox

    app = QApplication.instance() or QApplication(sys.argv)
    box = QMessageBox()
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.exec()
