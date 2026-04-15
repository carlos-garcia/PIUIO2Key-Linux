"""
Keymap loading and HID packet state extraction.
"""

import configparser
import os

from evdev import ecodes as e

from .config import BIT_LAYOUT, DEFAULT_KEYMAP, PIUIO_BIT_LAYOUT


def resolve_keycode(name):
    """Resolve a key name like 'KEY_Q', 'Q', or numeric code to an evdev ecodes value."""
    if isinstance(name, int):
        return name
    name = name.strip()
    if hasattr(e, name):
        return getattr(e, name)
    full = f"KEY_{name}"
    if hasattr(e, full):
        return getattr(e, full)
    try:
        return int(name, 0)
    except ValueError:
        pass
    print(f"WARNING: Unknown key '{name}', skipping")
    return None


def load_keymap(config_path):
    """Load key mappings from an INI file, falling back to defaults."""
    # Accept any key that's valid in either backend's bit layout
    valid_keys = set(BIT_LAYOUT) | set(PIUIO_BIT_LAYOUT)
    keymap = dict(DEFAULT_KEYMAP)
    if config_path and os.path.isfile(config_path):
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
        if cfg.has_section("keymap"):
            for key, value in cfg.items("keymap"):
                key_upper = key.upper()
                if key_upper in valid_keys:
                    keymap[key_upper] = value
                else:
                    print(f"WARNING: Unknown mapping '{key_upper}' in config, skipping")
        print(f"Config loaded from: {config_path}")
    else:
        if config_path:
            print(f"Config not found: {config_path}, using defaults")
        else:
            print("No config specified, using defaults")
    return keymap


def build_input_table(keymap):
    """Build processing table: list of (byte_idx, bit_idx, keycode, map_name)."""
    table = []
    all_keys = set()
    for map_name, (byte_idx, bit_idx) in BIT_LAYOUT.items():
        key_name = keymap.get(map_name)
        if not key_name:
            continue
        keycode = resolve_keycode(key_name)
        if keycode is not None:
            table.append((byte_idx, bit_idx, keycode, map_name))
            all_keys.add(keycode)
    return table, all_keys


def build_piuio_input_table(keymap):
    """Build processing table for PIUIO: list of (bit_pos, keycode, map_name).

    Same role as build_input_table() but uses PIUIO's 32-bit combined field
    bit positions instead of byte:bit pairs.
    """
    table = []
    all_keys = set()
    for map_name, bit_pos in PIUIO_BIT_LAYOUT.items():
        key_name = keymap.get(map_name)
        if not key_name:
            continue
        keycode = resolve_keycode(key_name)
        if keycode is not None:
            table.append((bit_pos, keycode, map_name))
            all_keys.add(keycode)
    return table, all_keys


def extract_piuio_state(combined, table):
    """Extract a bitmask of pressed buttons from a PIUIO 32-bit combined field."""
    state = 0
    for i, (bit_pos, _keycode, _name) in enumerate(table):
        if combined & (1 << bit_pos):
            state |= (1 << i)
    return state


def extract_state(data, table):
    """Extract a bitmask of pressed buttons from a 16-byte HID packet."""
    state = 0
    for i, (byte_idx, bit_idx, _keycode, _name) in enumerate(table):
        # Active-low: bit=0 means pressed
        if not (data[byte_idx] & (1 << bit_idx)):
            state |= (1 << i)
    return state


def print_keymap(keymap):
    """Print the active key mapping to stdout."""
    print("\n--- Active Key Mapping ---")
    print("Player 1:  ", end="")
    for pos, label in [("1P_7", "UL"), ("1P_9", "UR"), ("1P_5", "CTR"),
                       ("1P_1", "DL"), ("1P_3", "DR")]:
        print(f"{label}={keymap.get(f'MAP_{pos}', '?')}", end="  ")
    print()
    print("Player 2:  ", end="")
    for pos, label in [("2P_7", "UL"), ("2P_9", "UR"), ("2P_5", "CTR"),
                       ("2P_1", "DL"), ("2P_3", "DR")]:
        print(f"{label}={keymap.get(f'MAP_{pos}', '?')}", end="  ")
    print()
    print(f"Cabinet:   TEST={keymap.get('MAP_CONFIG', '?')}  "
          f"SERVICE={keymap.get('MAP_SERVICE', '?')}")
    print()
