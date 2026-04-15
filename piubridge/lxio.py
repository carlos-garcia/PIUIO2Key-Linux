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
LXIO_PIDS = (0x1020, 0x1040)
LXIO_ENDPOINT_IN = 0x81
LXIO_PACKET_SIZE = 16
LXIO_TIMEOUT = 1000  # ms


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

    def description(self):
        """Human-readable device description."""
        from .config import KNOWN_DEVICES
        return KNOWN_DEVICES.get((LXIO_VID, self.pid), f"LXIO ({self.pid:#06x})")
