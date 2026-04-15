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
        return gui.run_tray(keymap, args.poll_hz, backend=backend)

    if backend == "piuio":
        return run_bridge_piuio(keymap, args.poll_hz)
    return run_bridge_lxio(keymap, args.poll_hz)
