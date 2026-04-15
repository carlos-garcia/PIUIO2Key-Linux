"""Setup instructions printed by --setup-help."""

SETUP_HELP = """
=== PIUIO/LXIO Linux Setup Guide ===

1) INSTALL DEPENDENCIES

   System packages (CachyOS / Arch):
     sudo pacman -S python-pyusb python-evdev

   Debian / Ubuntu:
     sudo apt install python3-usb python3-evdev

   Fedora:
     sudo dnf install python3-pyusb python3-evdev

   Optional (for system tray + diagnostics):
     sudo pacman -S python-pyqt6      # or pip install PyQt6

2) SET UP USB PERMISSIONS

   Run the installer script (grants non-root USB + uinput access):
     sudo ./install-udev.sh

   Then log out and log back in (for the 'input' group to take effect).
   Replug your PIUIO/LXIO device after running the script.

   What it does:
   - Creates /etc/udev/rules.d/99-piuio.rules with MODE="0666" for all
     known PIUIO/LXIO USB device nodes
   - Loads the uinput kernel module (for virtual keyboard output)
   - Adds your user to the 'input' group (for /dev/uinput access)

3) VERIFY THE DEVICE

     python3 piu_bridge.py --detect
     python3 piu_bridge.py --dump       # raw data from the device

4) RUN THE BRIDGE

     python3 piu_bridge.py              # auto-detect + defaults (tray + diag)
     python3 piu_bridge.py -c my.ini    # custom key mappings
     python3 piu_bridge.py --dump       # raw hex dump mode
     python3 piu_bridge.py --no-tray    # terminal-only mode

5) CONFIG FILE FORMAT (INI)

     [keymap]
     ; Player 1 (QESZC layout)
     MAP_1P_7=KEY_Q       ; UL
     MAP_1P_9=KEY_E       ; UR
     MAP_1P_5=KEY_S       ; CENTER
     MAP_1P_1=KEY_Z       ; DL
     MAP_1P_3=KEY_C       ; DR
     ; Player 2 (Numpad 79513)
     MAP_2P_7=KEY_KP7
     MAP_2P_9=KEY_KP9
     MAP_2P_5=KEY_KP5
     MAP_2P_1=KEY_KP1
     MAP_2P_3=KEY_KP3
     ; Cabinet
     MAP_CONFIG=KEY_F1    ; TEST button
     MAP_SERVICE=KEY_F2   ; SERVICE button

   Key names: Linux evdev names (KEY_Q, KEY_KP7, KEY_ESC, KEY_F1, etc.)
   List all: python3 -c "from evdev import ecodes; [print(k) for k in sorted(dir(ecodes)) if k.startswith('KEY_')]"

6) SUPPORTED HARDWARE

   | Device          | VID:PID     | USB Protocol         |
   |-----------------|-------------|----------------------|
   | PIUIO (EZ-USB)  | 0547:1002   | Vendor control (0xAE)|
   | PIUIO Button    | 0D2F:1010   | Vendor control       |
   | LXIO v1         | 0D2F:1020   | Interrupt endpoints  |
   | LXIO v2         | 0D2F:1040   | Interrupt endpoints  |

7) NOTES ON POLL RATE & SIMULTANEOUS PRESSES

   - All button states are read atomically in every poll cycle.
     All 10 pad buttons + 2 cabinet buttons per read.
   - XOR change detection: only state transitions generate keyboard events.
   - Default poll rate: 1000 Hz (1ms). Use --poll-hz 0 for tight loop.
   - For PIU charts requiring 10 simultaneous buttons: all are read
     atomically — no ghosting or lost inputs.
"""
