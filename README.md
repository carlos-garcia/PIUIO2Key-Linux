# PIU IO Bridge (Linux)

A Linux port of the [Windows io2key driver](../windows/) for Pump It Up arcade
IO boards (PIUIO / LXIO / Andamiro PIU HID). Reads the pad over USB and
emits keyboard events via `uinput`, so any game or simulator that accepts
keyboard input (**ITGMania**, **OutFox**, **XSanity**, **PIU Rise**, etc.)
can use the pad natively — no custom game plugins required.

## Features

- 🎮 **All 12 inputs**: 5 panels per player + TEST / SERVICE cabinet buttons
- ⚡ **1000 Hz polling** with XOR change detection — no event flooding, true
  10-button simultaneous support (JUMPs, brackets)
- 🔧 **INI config** for key remapping (same format as the Windows version)
- 🖥️ **System tray icon** (KDE/Qt) with:
  - Live diagnostics window (panels light up red when stepped on)
  - Status / current device / key mapping readout
  - Clean exit
- 🔌 **Auto-detection** via pyusb (VID/PID scan — no kernel driver binding)
- 🐛 **Raw hex dump mode** (`--dump`) for debugging unknown hardware
- 🧪 **Graceful degradation**: works with or without PyQt6 installed
- 🎯 **Zero sudo** once udev rules are in place

## Supported hardware

| Board | VID:PID | USB Protocol |
|-------|---------|--------------|
| PIUIO (EZ-USB FX2) | `0547:1002` | Vendor control (request 0xAE) |
| PIUIO Button | `0D2F:1010` | Vendor control |
| LXIO v1 (Andamiro PIU HID) | `0D2F:1020` | Interrupt endpoint (0x81) |
| LXIO v2 | `0D2F:1040` | Interrupt endpoint (0x81) |

All devices are accessed directly via **pyusb** (libusb) — the bridge
does not need the kernel to expose a HID node or bind any driver.

Default bit layouts for LXIO and PIUIO are confirmed — other boards may
need tweaks in `piubridge/config.py::BIT_LAYOUT` or `PIUIO_BIT_LAYOUT`.
Use `--dump` to see what your hardware sends.

---

## Quick start

### Arch / CachyOS (easiest)

Download and install the pre-built package from the [releases page](https://github.com/carlos-garcia/PIUIO2Key-Linux/releases):

```bash
# Download the latest release
curl -LO https://github.com/carlos-garcia/PIUIO2Key-Linux/releases/download/v1.0.1/piuio2key-1.0.1-1-any.pkg.tar.zst

# Install
sudo pacman -U piuio2key-1.0.1-1-any.pkg.tar.zst
```

Or build from the PKGBUILD:

```bash
git clone https://github.com/carlos-garcia/PIUIO2Key-Linux.git
cd PIUIO2Key-Linux
makepkg -si
```

After installation, **log out and back in** (to apply the `input` group), then run `piuio2key` or launch "PIU IO Bridge" from your app menu.

---

### Other distros (manual install)

#### 1. Dependencies

```bash
# Debian / Ubuntu
sudo apt install python3 python3-usb python3-evdev python3-pyqt6

# Fedora
sudo dnf install python3 python3-pyusb python3-evdev python3-pyqt6
```

Or install the Python deps via pip:

```bash
pip install -r requirements.txt
# optional, for the tray icon + diagnostics window:
pip install PyQt6
```

#### 2. Grant device access (udev rules)

```bash
./install-udev.sh
```

This:
- Installs `/etc/udev/rules.d/99-piuio.rules` to grant user access to the
  PIUIO/LXIO USB device nodes and `/dev/uinput`
- Loads the `uinput` kernel module now and on every boot
- Adds your user to the `input` group (log out and back in after)

**After logging out and back in**, unplug and replug the pad.

#### 3. Verify the device is visible

```bash
python3 piu_bridge.py --detect
# Expected:
#   Found LXIO v1 (Andamiro PIU HID) — lxio mode (direct USB)
```

#### 4. Run the bridge

```bash
python3 piu_bridge.py
```

You should see a PIU icon appear in your system tray. Right-click it for
**Status**, **Key Mapping**, **Diagnostics**, and **Exit**. Step on the pad
→ keys are emitted (open a text editor to verify).

#### 5. Install a desktop launcher (optional)

```bash
./install-launcher.sh
```

Adds "PIU IO Bridge" to your app menu and KRunner — no more terminal needed.

---

## Usage

```bash
python3 piu_bridge.py                      # auto-detect + tray + diag
python3 piu_bridge.py --no-tray            # terminal-only mode
python3 piu_bridge.py -c my_keys.ini       # custom key mappings
python3 piu_bridge.py --dump               # raw hex dump (debug)
python3 piu_bridge.py --detect             # scan and exit
python3 piu_bridge.py --show-keymap        # print active mapping
python3 piu_bridge.py --setup-help         # full setup instructions
python3 piu_bridge.py --poll-hz 500        # custom poll rate (default 1000)
```

### Command-line arguments

| Flag | Argument | Default | Description |
|------|----------|---------|-------------|
| `-h`, `--help` | — | — | Show the argparse help and exit. |
| `-c`, `--config` | `FILE` | `default.ini` next to the script | INI file with `[keymap]` overrides. Unknown keys are warned and skipped. |
| `--poll-hz` | `INT` | `1000` | Polling frequency in Hz. `0` = tight loop (no sleep). The effective rate is capped by the USB transfer timing (~1 kHz on LXIO). |
| `--detect` | — | — | Scan the USB bus for known PIUIO/LXIO devices, print results, exit. Exit code `0` = found, `1` = not found. |
| `--dump` | — | — | Raw hex-dump mode. Prints each incoming packet with changed bytes highlighted in red. Useful when reverse-engineering an unknown board's bit layout. Does not emit keyboard events. |
| `--setup-help` | — | — | Print the full multi-section setup guide (udev rules, config format, packet layout) and exit. |
| `--show-keymap` | — | — | Print the active key mapping (after loading config) and exit. Good for sanity-checking your INI. |
| `--no-tray` | — | off | Disable the Qt system-tray icon even when PyQt6 is available. Bridge runs in terminal-only mode with stdout logs. |

Notes:

- The **tray icon** is auto-enabled when PyQt6 is importable **and** a display
  server is present (`$DISPLAY` or `$WAYLAND_DISPLAY`). If either check fails,
  the bridge silently falls back to terminal mode.
- `--dump` and `--show-keymap` short-circuit before the bridge starts —
  they never open `/dev/uinput`.

## Key mapping configuration

Edit `default.ini` (or copy it and pass with `-c`):

```ini
[keymap]
; Player 1 (QESZC)
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
MAP_CONFIG=KEY_F1    ; TEST
MAP_SERVICE=KEY_ENTER ; SERVICE
```

Key names use Linux evdev `KEY_*` names. List all:

```bash
python3 -c "from evdev import ecodes; [print(k) for k in sorted(dir(ecodes)) if k.startswith('KEY_')]"
```

## Project layout

```
linux/
├── piu_bridge.py            # thin launcher
├── default.ini              # key mapping config
├── install-udev.sh          # udev rules + uinput access
├── install-launcher.sh      # creates app-menu launcher
├── piu-bridge.desktop.in    # launcher template
├── requirements.txt
├── README.md
└── piubridge/               # Python package
    ├── cli.py               # CLI arg parsing & dispatch
    ├── config.py            # constants, keymap defaults, bit layouts
    ├── keymap.py            # key resolution, INI parsing, state extraction
    ├── device.py            # USB device detection (pyusb)
    ├── piuio.py             # PIUIO (EZ-USB FX2) backend — vendor ctrl xfers
    ├── lxio.py              # LXIO backend — interrupt endpoint xfers
    ├── bridge.py            # terminal-mode poll loop
    ├── setup_help.py        # --setup-help text
    └── gui/                 # optional Qt-based GUI
        ├── worker.py        # background QThread running the poll loop
        ├── diag.py          # diagnostics window (pad visualization)
        ├── tray.py          # system tray icon + context menu
        ├── make_icon.py     # regenerate icon.png
        ├── icon.png         # tray icon (vector-rendered PNG)
        └── icon.ico         # legacy fallback (from Windows build)
```

## How it works

1. **Detection** — scans the USB bus (via pyusb) for known VID:PID pairs
   and picks the right backend (`piuio` or `lxio`).
2. **Polling** —
   - **LXIO**: reads 16-byte packets from interrupt IN endpoint `0x81`.
   - **PIUIO**: vendor control transfers (request `0xAE`), 4 sensor-mux
     cycles per poll, each reading 4 bytes — OR'd together and inverted
     (active-low hardware) into a single 32-bit field.
3. **Decoding** — maps each bit to a named button using `BIT_LAYOUT`
   (LXIO) or `PIUIO_BIT_LAYOUT`; builds a single integer bitmask of
   "currently pressed" buttons.
4. **XOR change detection** — only state *transitions* produce key events,
   matching the Windows io2key behavior.
5. **uinput emission** — writes key press/release events through
   `/dev/uinput` as a virtual keyboard called "PIU Pad Keyboard".
6. **Qt tray** — a background `QThread` runs the poll loop and emits Qt
   signals for the tray menu and diagnostics window. GUI is optional;
   if PyQt6 isn't installed, the bridge runs in terminal mode.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No PIUIO/LXIO USB devices found` | Device not plugged in, or udev rules not applied | Check `lsusb`, run `./install-udev.sh`, replug |
| `Permission denied` opening USB device | udev rules not applied | Run `./install-udev.sh`, replug device |
| `Permission denied: /dev/uinput` | User not in `input` group | Run `install-udev.sh`, **log out + back in** |
| Tray icon missing (`SNI unavailable`) | Running as root / D-Bus session mismatch | Run **without** `sudo` after udev rules are in place |
| Wrong buttons register | Different hardware packet layout | Run `--dump`, step on each arrow, update `piubridge/config.py` |
| `ModuleNotFoundError: PyQt6` | Optional GUI dep missing | `pip install PyQt6`, or use `--no-tray` |

## Credits

- Based on the Windows [io2key](https://github.com/ckdur/piuio2key) driver
  by **CkDur** — the reference implementation this port follows.

## License

Same license as the parent project — see [LICENSE](LICENSE).
