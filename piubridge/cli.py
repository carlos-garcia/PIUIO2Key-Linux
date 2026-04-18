"""
Command-line interface: argument parsing and dispatch to subcommands.
"""

import argparse

from . import gui
from .bridge import (run_bridge_lxio, run_bridge_piuio,
                     run_dump_lxio, run_dump_piuio)
from .device import detect_device
from .keymap import load_keymap, print_keymap
from .setup_help import SETUP_HELP


def _build_parser():
    parser = argparse.ArgumentParser(
        description="PIU IO Bridge - PIUIO/LXIO to keyboard for Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-c", "--config",
                        help="INI config file for key mappings")
    parser.add_argument("--poll-hz", type=int, default=1000,
                        help="Poll rate in Hz (default: 1000, 0=tight loop)")
    parser.add_argument("--detect", action="store_true",
                        help="Scan for PIUIO/LXIO devices and exit")
    parser.add_argument("--dump", action="store_true",
                        help="Raw hex dump mode - show packet data for debugging")
    parser.add_argument("--setup-help", action="store_true",
                        help="Print Linux setup instructions and exit")
    parser.add_argument("--show-keymap", action="store_true",
                        help="Print active key mapping and exit")
    parser.add_argument("--no-tray", action="store_true",
                        help="Disable system tray icon (terminal-only mode)")
    parser.add_argument("--lights", action="store_true",
                        help="Enable reactive lights (PIUIO only: panels light when pressed)")
    parser.add_argument("--test-lights", action="store_true",
                        help="Turn ALL lights on for testing (PIUIO only, then exit)")
    return parser


def _resolve_config_path(explicit):
    """Find config.ini: explicit arg > cwd/default.ini > package_dir/../default.ini."""
    import os
    if explicit:
        return explicit
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = os.path.dirname(pkg_dir)
    for candidate in ["default.ini", os.path.join(script_dir, "default.ini")]:
        if os.path.isfile(candidate):
            return candidate
    return None


def main():
    """CLI entry point. Returns an integer exit code."""
    args = _build_parser().parse_args()

    if args.setup_help:
        print(SETUP_HELP)
        return 0

    # Detect device
    backend, desc = detect_device()

    if args.detect:
        if backend:
            print(f"Found {desc} — {backend} mode (direct USB)")
            return 0
        print("No PIUIO/LXIO USB devices found. Is the hardware plugged in?")
        return 1

    keymap = load_keymap(_resolve_config_path(args.config))

    if args.show_keymap:
        print_keymap(keymap)
        return 0

    if args.test_lights:
        if not backend:
            print("ERROR: No PIUIO/LXIO USB device found for light test.")
            return 1
        # Turn on ALL panel lights (P1 bits 2-6, P2 bits 18-22)
        all_lights = 0x007C007C
        print(f"Turning on ALL lights (light_data = 0x{all_lights:08x})")
        print("Press Ctrl+C to stop...")
        import time
        
        if backend == "piuio":
            from .piuio import PiuioDevice
            dev = PiuioDevice()
            if not dev.open():
                print("ERROR: Could not open PIUIO USB device.")
                return 1
            try:
                while True:
                    for i in range(4):
                        out_data = (all_lights & 0xFFFCFFFC) | (i | (i << 16))
                        out = out_data.to_bytes(4, "little").ljust(8, b"\x00")
                        dev.dev.ctrl_transfer(0x40, 0xAE, 0, 0, out, 10)
                        dev.dev.ctrl_transfer(0xC0, 0xAE, 0, 0, 8, 10)
                    time.sleep(0.001)
            except KeyboardInterrupt:
                # Turn off lights
                for i in range(4):
                    out = (i | (i << 16)).to_bytes(4, "little").ljust(8, b"\x00")
                    dev.dev.ctrl_transfer(0x40, 0xAE, 0, 0, out, 10)
                print("\nLights off.")
            dev.close()
        else:  # lxio
            from .lxio import LxioDevice, LXIO_ENDPOINT_OUT
            dev = LxioDevice()
            if not dev.open():
                print("ERROR: Could not open LXIO USB device.")
                return 1
            try:
                while True:
                    out = all_lights.to_bytes(4, "little").ljust(16, b"\x00")
                    dev.dev.write(LXIO_ENDPOINT_OUT, out, 100)
                    time.sleep(0.01)
            except KeyboardInterrupt:
                # Turn off lights
                dev.dev.write(LXIO_ENDPOINT_OUT, bytes(16), 100)
                print("\nLights off.")
            dev.close()
        return 0

    if not backend:
        msg_lines = [
            "No PIUIO/LXIO USB devices found!",
            "Is the hardware plugged in?",
            "If you just plugged it in, run: sudo ./install-udev.sh",
            "See --setup-help for full setup instructions.",
        ]
        for line in msg_lines:
            print(line)
        if not args.no_tray:
            gui.show_error_dialog("PIU IO Bridge", "\n".join(msg_lines))
        return 1

    print(f"Found {desc} — {backend} mode")

    if args.dump:
        if backend == "piuio":
            run_dump_piuio()
        else:
            run_dump_lxio()
        return 0

    print_keymap(keymap)

    # Decide between tray and terminal mode
    use_tray = (
        gui.HAS_QT
        and not args.no_tray
        and gui.has_display()
    )

    if use_tray:
        print("Starting with system tray icon (use --no-tray to disable)")
        return gui.run_tray(keymap, args.poll_hz, backend=backend,
                            reactive_lights=args.lights)

    if backend == "piuio":
        return run_bridge_piuio(keymap, args.poll_hz, reactive_lights=args.lights)
    return run_bridge_lxio(keymap, args.poll_hz, reactive_lights=args.lights)
