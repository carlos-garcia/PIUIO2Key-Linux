"""
Background worker thread that runs the bridge loop for the Qt tray mode.

Supports both LXIO (pyusb interrupt) and PIUIO (pyusb control) backends.
"""

import time

from evdev import UInput, ecodes as e
from PyQt6.QtCore import QThread, pyqtSignal

from ..config import UINPUT_NAME, UINPUT_PRODUCT, UINPUT_VENDOR
from ..keymap import (build_input_table, build_piuio_input_table,
                      extract_piuio_state, extract_state)


class BridgeWorker(QThread):
    """Runs the bridge poll loop in a background thread.

    Signals:
      status_changed(str)  - human-readable status update (tooltip/menu)
      error_occurred(str)  - fatal or recoverable error message
      state_updated(int)   - new bitmask of pressed buttons (for diagnostics)
    """

    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    state_updated = pyqtSignal(int)

    def __init__(self, keymap, poll_hz, backend="lxio"):
        super().__init__()
        self.keymap = keymap
        self.poll_hz = poll_hz
        self.backend = backend
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        if self.backend == "piuio":
            self._run_piuio()
        else:
            self._run_lxio()

    def _create_uinput(self, all_keys):
        """Create the virtual keyboard (shared by both backends)."""
        cap = {
            e.EV_KEY: list(all_keys),
            e.EV_MSC: [e.MSC_SCAN],
        }
        return UInput(cap, name=UINPUT_NAME,
                      vendor=UINPUT_VENDOR, product=UINPUT_PRODUCT)

    def _run_lxio(self):
        """LXIO backend: pyusb interrupt transfers."""
        from ..lxio import LxioDevice

        table, all_keys = build_input_table(self.keymap)
        if not table:
            self.error_occurred.emit("No valid key mappings!")
            return

        dev = LxioDevice()
        if not dev.open():
            self.error_occurred.emit(
                "Could not open LXIO USB device.\n"
                "Is it plugged in? Check permissions (install-udev.sh)."
            )
            return

        try:
            ui = self._create_uinput(all_keys)
        except Exception as err:
            dev.close()
            self.error_occurred.emit(f"Failed to create uinput device: {err}")
            return

        poll_interval = 1.0 / self.poll_hz if self.poll_hz > 0 else 0
        prev_state = 0

        self.status_changed.emit(
            f"Running - {dev.description()} ({len(table)} inputs)"
        )

        try:
            while self._running:
                data = dev.read()
                if data is None:
                    continue

                state = extract_state(data, table)
                changed = state ^ prev_state

                if changed:
                    for i, (_byte_idx, _bit_idx, keycode, _name) in enumerate(table):
                        bit = 1 << i
                        if changed & bit:
                            pressed = 1 if (state & bit) else 0
                            ui.write(e.EV_MSC, e.MSC_SCAN, keycode)
                            ui.write(e.EV_KEY, keycode, pressed)
                    ui.syn()
                    self.state_updated.emit(state)

                prev_state = state

                if poll_interval > 0:
                    time.sleep(poll_interval)

        except Exception as err:
            self.error_occurred.emit(str(err))
        finally:
            ui.close()
            dev.close()
            if self._running:
                self.status_changed.emit("Stopped")

    def _run_piuio(self):
        """PIUIO backend: pyusb vendor control transfers."""
        from ..piuio import PiuioDevice

        table, all_keys = build_piuio_input_table(self.keymap)
        if not table:
            self.error_occurred.emit("No valid key mappings!")
            return

        dev = PiuioDevice()
        if not dev.open():
            self.error_occurred.emit(
                "Could not open PIUIO USB device.\n"
                "Is it plugged in? Check permissions (install-udev.sh)."
            )
            return

        try:
            ui = self._create_uinput(all_keys)
        except Exception as err:
            dev.close()
            self.error_occurred.emit(f"Failed to create uinput device: {err}")
            return

        poll_interval = 1.0 / self.poll_hz if self.poll_hz > 0 else 0
        prev_state = 0

        self.status_changed.emit(
            f"Running - PIUIO direct USB ({len(table)} inputs)"
        )

        try:
            while self._running:
                combined = dev.poll()
                state = extract_piuio_state(combined, table)
                changed = state ^ prev_state

                if changed:
                    for i, (_bit_pos, keycode, _name) in enumerate(table):
                        bit = 1 << i
                        if changed & bit:
                            pressed = 1 if (state & bit) else 0
                            ui.write(e.EV_MSC, e.MSC_SCAN, keycode)
                            ui.write(e.EV_KEY, keycode, pressed)
                    ui.syn()
                    self.state_updated.emit(state)

                prev_state = state

                if poll_interval > 0:
                    time.sleep(poll_interval)

        except Exception as err:
            self.error_occurred.emit(str(err))
        finally:
            ui.close()
            dev.close()
            if self._running:
                self.status_changed.emit("Stopped")
