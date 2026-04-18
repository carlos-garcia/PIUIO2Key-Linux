"""
LXIO (Andamiro PIU HID) direct USB backend using pyusb.

The LXIO boards (VID 0x0D2F, PID 0x1020/0x1040) use interrupt endpoints
for 16-byte transfers. This module talks directly to the USB endpoints
via pyusb (no kernel usbhid binding required).

Endpoint layout (from Windows lxio.cpp):
  IN:  0x81 (interrupt, 16 bytes — sensor/button state)
  OUT: 0x02 (interrupt, 16 bytes — lamp data, unused by this bridge)
"""

import usb.core
import usb.util

LXIO_VID = 0x0D2F
LXIO_PIDS = (0x1010, 0x1020, 0x1040)  # 0x1010 = PIUIO Button, 0x1020 = LXIO v1, 0x1040 = LXIO v2
LXIO_ENDPOINT_IN = 0x81
LXIO_ENDPOINT_OUT = 0x02
LXIO_PACKET_SIZE = 16
LXIO_TIMEOUT = 1000  # ms

# Mask for P1 (bits 0-4) and P2 (bits 16-20) panel sensors
PANEL_MASK = 0x001F001F


def find_lxio():
    """Check if an LXIO is on the USB bus. Returns (dev, pid) or (None, None)."""
    try:
        for pid in LXIO_PIDS:
            dev = usb.core.find(idVendor=LXIO_VID, idProduct=pid)
            if dev is not None:
                return dev, pid
    except Exception:
        pass
    return None, None


class LxioDevice:
    """Manages USB connection and I/O for an LXIO board."""

    def __init__(self):
        self.dev = None
        self.pid = None
        self.light_data = 0
        self.reactive_lights = False

    def open(self):
        """Find and claim the LXIO USB device. Returns True on success."""
        self.dev, self.pid = find_lxio()
        if self.dev is None:
            return False
        # Detach kernel driver if attached (usbhid may claim it on some distros)
        for cfg in self.dev:
            for intf in cfg:
                try:
                    if self.dev.is_kernel_driver_active(intf.bInterfaceNumber):
                        self.dev.detach_kernel_driver(intf.bInterfaceNumber)
                except usb.core.USBError:
                    pass
        self.dev.set_configuration()
        return True

    def close(self):
        """Release the USB device."""
        if self.dev:
            try:
                usb.util.dispose_resources(self.dev)
            except Exception:
                pass
            self.dev = None

    def read(self):
        """Read one 16-byte input packet from the interrupt IN endpoint.

        Returns a bytes object (16-byte packet), or None on timeout / error.
        """
        try:
            data = self.dev.read(LXIO_ENDPOINT_IN, LXIO_PACKET_SIZE, LXIO_TIMEOUT)
            return bytes(data)
        except usb.core.USBTimeoutError:
            return None
        except usb.core.USBError:
            return None

    def write_lights(self):
        """Write light data to the interrupt OUT endpoint."""
        if not self.reactive_lights:
            return
        try:
            # First 4 bytes are light data, rest is zeros
            out = self.light_data.to_bytes(4, "little").ljust(16, b"\x00")
            self.dev.write(LXIO_ENDPOINT_OUT, out, LXIO_TIMEOUT)
        except usb.core.USBError:
            pass

    def set_lights_from_input(self, data):
        """Set light bits based on sensor input state.

        Matches Windows: m_iLightData = (m_iInputField & 0x001F001F) << 2
        """
        if not self.reactive_lights:
            return
        # Extract P1 (byte 0, bits 0-4) and P2 (byte 4, bits 0-4) sensor state
        # Active-low: bit=0 means pressed, so invert
        p1 = (~data[0]) & 0x1F
        p2 = (~data[4]) & 0x1F
        combined = p1 | (p2 << 16)
        # Shift by 2 to get light bits (same as PIUIO)
        self.light_data = (combined & PANEL_MASK) << 2
        self.write_lights()

    def description(self):
        """Human-readable device description."""
        from .config import KNOWN_DEVICES
        return KNOWN_DEVICES.get((LXIO_VID, self.pid), f"LXIO ({self.pid:#06x})")
