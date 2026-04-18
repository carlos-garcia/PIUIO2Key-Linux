"""
Constants and hardware definitions for the PIU bridge.

PIU pad layout:
    7(UL)  9(UR)
       5(CENTER)
    1(DL)  3(DR)
"""

# --- Default key mappings (matches Windows io2key defaults) ---
DEFAULT_KEYMAP = {
    # Player 1 pad
    "MAP_1P_7": "KEY_Q",
    "MAP_1P_9": "KEY_E",
    "MAP_1P_5": "KEY_S",
    "MAP_1P_1": "KEY_Z",
    "MAP_1P_3": "KEY_C",
    # Player 2 pad
    "MAP_2P_7": "KEY_KP7",
    "MAP_2P_9": "KEY_KP9",
    "MAP_2P_5": "KEY_KP5",
    "MAP_2P_1": "KEY_KP1",
    "MAP_2P_3": "KEY_KP3",
    # Cabinet buttons
    "MAP_CONFIG": "KEY_F1",
    "MAP_SERVICE": "KEY_F2",
}

# --- HID packet bit layout (confirmed via hexdump on LXIO v1) ---
# Each entry: (byte_index, bit_index) in the 16-byte HID packet
# Active-low: bit=0 means pressed
#
# Confirmed mapping from live hardware testing:
#   Byte 0: P1 sensors, bits 0-4 = UL, UR, CENTER, DL, DR
#   Byte 4: P2 sensors, bits 0-4 = UL, UR, CENTER, DL, DR
#   Byte 8: Cabinet, bit 6 = TEST (0xbf), bit 1 = SERVICE (0xfd)
BIT_LAYOUT = {
    # Player 1: byte 0, bits 0-4
    "MAP_1P_7": (0, 0),   # UL
    "MAP_1P_9": (0, 1),   # UR
    "MAP_1P_5": (0, 2),   # CENTER
    "MAP_1P_1": (0, 3),   # DL
    "MAP_1P_3": (0, 4),   # DR
    # Player 2: byte 4, bits 0-4
    "MAP_2P_7": (4, 0),   # UL
    "MAP_2P_9": (4, 1),   # UR
    "MAP_2P_5": (4, 2),   # CENTER
    "MAP_2P_1": (4, 3),   # DL
    "MAP_2P_3": (4, 4),   # DR
    # Cabinet: byte 8
    "MAP_CONFIG": (8, 6),   # TEST button  - byte 8 goes 0xbf (bit 6 = 0)
    "MAP_SERVICE": (8, 1),  # SERVICE button - byte 8 goes 0xfd (bit 1 = 0)
}

# Known device VID:PID pairs
KNOWN_DEVICES = {
    (0x0547, 0x1002): "PIUIO (EZ-USB FX2)",
    (0x0D2F, 0x1010): "PIUIO Button",
    (0x0D2F, 0x1020): "LXIO v1 (Andamiro PIU HID)",
    (0x0D2F, 0x1040): "LXIO v2",
}

# Virtual uinput device identity (shown to the OS as the source of keypresses).
#
# We deliberately DO NOT reuse the LXIO's real VID:PID here. SDL2's fullscreen
# input path in some games matches devices against its gamepad database by
# VID:PID — if we announce 0x0D2F:0x1020 (Andamiro) it can get misclassified
# as a controller and ignored when the game scans for keyboards.
#
# Instead we use Linux Foundation's reserved virtual-device VID (0x1D6B) with
# a generic product ID, and a neutral name that doesn't contain "bridge" or
# "custom" keywords some SDL games filter on.
UINPUT_NAME = "PIU Pad Keyboard"
UINPUT_VENDOR = 0x1D6B   # Linux Foundation (virtual devices)
UINPUT_PRODUCT = 0x0001  # generic

# --- PIUIO bit positions in the combined 32-bit input field ---
# The PIUIO returns sensor data as uint32_t (LE), active-low, inverted after
# read.  Each sensor set is read via a separate USB control transfer (4 per
# cycle), then OR'd together.  Bit positions confirmed via live hardware
# dump on an MK6/9 PIUIO (EZ-USB FX2).
PIUIO_BIT_LAYOUT = {
    "MAP_1P_7": 0,    # P1 UL
    "MAP_1P_9": 1,    # P1 UR
    "MAP_1P_5": 2,    # P1 CENTER
    "MAP_1P_1": 3,    # P1 DL
    "MAP_1P_3": 4,    # P1 DR
    "MAP_2P_7": 16,   # P2 UL
    "MAP_2P_9": 17,   # P2 UR
    "MAP_2P_5": 18,   # P2 CENTER
    "MAP_2P_1": 19,   # P2 DL
    "MAP_2P_3": 20,   # P2 DR
    "MAP_CONFIG":  9,  # TEST
    "MAP_SERVICE": 14, # SERVICE
}

# --- PIUIO light output bit positions ---
# Light bits in the 32-bit output word sent with each poll.
# Panel lights are shifted +2 from sensor positions.
PIUIO_LIGHT_BITS = {
    "1P_UL":  2,   # P1 Upper Left
    "1P_UR":  3,   # P1 Upper Right
    "1P_CTR": 4,   # P1 Center
    "1P_DL":  5,   # P1 Down Left
    "1P_DR":  6,   # P1 Down Right
    "2P_UL":  18,  # P2 Upper Left
    "2P_UR":  19,  # P2 Upper Right
    "2P_CTR": 20,  # P2 Center
    "2P_DL":  21,  # P2 Down Left
    "2P_DR":  22,  # P2 Down Right
}

# Mapping from input bit position to light bit position
PIUIO_INPUT_TO_LIGHT = {
    0: 2,   # P1 UL sensor -> P1 UL light
    1: 3,   # P1 UR sensor -> P1 UR light
    2: 4,   # P1 CTR sensor -> P1 CTR light
    3: 5,   # P1 DL sensor -> P1 DL light
    4: 6,   # P1 DR sensor -> P1 DR light
    16: 18, # P2 UL sensor -> P2 UL light
    17: 19, # P2 UR sensor -> P2 UR light
    18: 20, # P2 CTR sensor -> P2 CTR light
    19: 21, # P2 DL sensor -> P2 DL light
    20: 22, # P2 DR sensor -> P2 DR light
}
