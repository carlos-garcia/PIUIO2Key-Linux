"""
USB device detection for PIUIO and LXIO boards (via pyusb).
"""

from .config import KNOWN_DEVICES


def detect_device():
    """Auto-detect which PIU IO board is connected.

    Returns ("piuio", description) or ("lxio", description) or (None, None).
    """
    try:
        from .piuio import find_piuio, PIUIO_VID, PIUIO_PID
        if find_piuio():
            desc = KNOWN_DEVICES.get((PIUIO_VID, PIUIO_PID), "PIUIO")
            return "piuio", desc
    except ImportError:
        pass

    try:
        from .lxio import find_lxio, LXIO_VID
        dev, pid = find_lxio()
        if dev is not None:
            desc = KNOWN_DEVICES.get((LXIO_VID, pid), "LXIO")
            return "lxio", desc
    except ImportError:
        pass

    return None, None
