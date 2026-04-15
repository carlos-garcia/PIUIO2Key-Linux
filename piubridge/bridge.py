"""
Core bridge loops (terminal mode) and raw dump debug modes.

Supports two backends:
  - LXIO: pyusb interrupt transfers (16-byte packets)
  - PIUIO: pyusb vendor control transfers (8-byte, 4 mux reads)
"""

import time

from evdev import UInput, ecodes as e

from .config import UINPUT_NAME, UINPUT_PRODUCT, UINPUT_VENDOR
from .keymap import build_input_table, build_piuio_input_table, extract_piuio_state, extract_state


def _create_uinput(all_keys):
    """Create the virtual keyboard device (shared by all backends)."""
    cap = {
        e.EV_KEY: list(all_keys),
        e.EV_MSC: [e.MSC_SCAN],
        # EV_REP is auto-enabled by the kernel for keyboard devices
    }
    return UInput(cap, name=UINPUT_NAME, vendor=UINPUT_VENDOR, product=UINPUT_PRODUCT)


def _emit_changes(ui, table, changed, state, key_index):
    """Emit MSC_SCAN + EV_KEY events for changed buttons, then SYN."""
    for i, entry in enumerate(table):
        bit = 1 << i
        if changed & bit:
            keycode = entry[key_index]
            pressed = 1 if (state & bit) else 0
            ui.write(e.EV_MSC, e.MSC_SCAN, keycode)
            ui.write(e.EV_KEY, keycode, pressed)
    ui.syn()


# ---------------------------------------------------------------------------
#  LXIO — pyusb interrupt transfers
# ---------------------------------------------------------------------------

def run_dump_lxio():
    """Raw hex dump for LXIO — shows 16-byte packets, highlights changes."""
    from .lxio import LxioDevice

    dev = LxioDevice()
    if not dev.open():
        print("ERROR: Could not open LXIO USB device.")
        return

    print(f"--- LXIO Raw Dump Mode: {dev.description()} ---")
    print("Press buttons on the pad and watch for changes.")
    print("Format: byte0 byte1 ... byte15 (changed bytes in red)")
    print("Press Ctrl+C to stop.\n")

    prev = None
    try:
        while True:
            data = dev.read()
            if data is None:
                continue
            if data != prev:
                parts = []
                for i, b in enumerate(data):
                    if prev and b != prev[i]:
                        parts.append(f"\033[1;31m{b:02x}\033[0m")
                    else:
                        parts.append(f"{b:02x}")
                print(f"  [{' '.join(parts)}]")
                if prev:
                    for i, b in enumerate(data):
                        if b != prev[i]:
                            print(f"    ^ byte {i}: {prev[i]:08b} -> {b:08b}")
                prev = data
    except KeyboardInterrupt:
        print("\nDump stopped.")
    finally:
        dev.close()


def run_bridge_lxio(keymap, poll_hz):
    """Bridge loop for LXIO boards (pyusb interrupt transfers).

    Returns 0 on clean shutdown, 1 on error.
    """
    from .lxio import LxioDevice

    table, all_keys = build_input_table(keymap)
    if not table:
        print("ERROR: No valid key mappings!")
        return 1

    dev = LxioDevice()
    if not dev.open():
        print("ERROR: Could not open LXIO USB device.")
        print("Is it plugged in? Do you have permission? (see install-udev.sh)")
        return 1

    ui = _create_uinput(all_keys)
    poll_interval = 1.0 / poll_hz if poll_hz > 0 else 0
    prev_state = 0

    print(f"LXIO mode (direct USB) — {dev.description()}")
    print(f"Poll rate: {'max (tight loop)' if poll_hz == 0 else f'{poll_hz} Hz'}")
    print(f"Mapped {len(table)} inputs")
    print("--- Bridge Running (Ctrl+C to stop) ---\n")

    try:
        while True:
            data = dev.read()
            if data is None:
                continue

            state = extract_state(data, table)
            changed = state ^ prev_state

            if changed:
                # table entries: (byte_idx, bit_idx, keycode, name) — keycode at index 2
                _emit_changes(ui, table, changed, state, key_index=2)

            prev_state = state

            if poll_interval > 0:
                time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as err:
        print(f"\nError: {err}")
        return 1
    finally:
        ui.close()
        dev.close()

    return 0


# ---------------------------------------------------------------------------
#  PIUIO — pyusb vendor control transfers
# ---------------------------------------------------------------------------

def run_dump_piuio():
    """Raw dump for PIUIO — shows the 32-bit combined field each poll cycle."""
    from .piuio import PiuioDevice

    dev = PiuioDevice()
    if not dev.open():
        print("ERROR: Could not open PIUIO USB device.")
        return

    print("--- PIUIO Raw Dump Mode ---")
    print("Press buttons on the pad and watch for changes.")
    print("Format: hex(combined) [binary of bytes 3,2,1,0]")
    print("Press Ctrl+C to stop.\n")

    prev = None
    try:
        while True:
            combined = dev.poll()
            if combined != prev:
                b = combined.to_bytes(4, "big")
                bits = " ".join(f"{x:08b}" for x in b)
                marker = " <-- CHANGED" if prev is not None else ""
                print(f"  0x{combined:08x}  [{bits}]{marker}")
                prev = combined
            time.sleep(0.001)
    except KeyboardInterrupt:
        print("\nDump stopped.")
    finally:
        dev.close()


def run_bridge_piuio(keymap, poll_hz):
    """Bridge loop for PIUIO boards (pyusb vendor control transfers).

    Returns 0 on clean shutdown, 1 on error.
    """
    from .piuio import PiuioDevice

    table, all_keys = build_piuio_input_table(keymap)
    if not table:
        print("ERROR: No valid key mappings!")
        return 1

    dev = PiuioDevice()
    if not dev.open():
        print("ERROR: Could not open PIUIO USB device.")
        print("Is it plugged in? Do you have permission? (see install-udev.sh)")
        return 1

    ui = _create_uinput(all_keys)
    poll_interval = 1.0 / poll_hz if poll_hz > 0 else 0
    prev_state = 0

    print("PIUIO mode (direct USB)")
    print(f"Poll rate: {'max (tight loop)' if poll_hz == 0 else f'{poll_hz} Hz'}")
    print(f"Mapped {len(table)} inputs")
    print("--- Bridge Running (Ctrl+C to stop) ---\n")

    try:
        while True:
            combined = dev.poll()
            state = extract_piuio_state(combined, table)
            changed = state ^ prev_state

            if changed:
                # table entries: (bit_pos, keycode, name) — keycode at index 1
                _emit_changes(ui, table, changed, state, key_index=1)

            prev_state = state

            if poll_interval > 0:
                time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as err:
        print(f"\nError: {err}")
        return 1
    finally:
        ui.close()
        dev.close()

    return 0
