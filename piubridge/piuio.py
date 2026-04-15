"""
PIUIO (EZ-USB FX2) direct USB backend using pyusb.

The PIUIO board (VID 0x0547, PID 0x1002) is NOT a HID device — it uses
vendor-specific USB control transfers (request 0xAE).  This module provides
direct USB access via pyusb/libusb.

Protocol reverse-engineered from the Windows io2key source (piuio.cpp).
"""

import usb.core
import usb.util

PIUIO_VID = 0x0547
PIUIO_PID = 0x1002
PIUIO_CTL_REQ = 0xAE
REQ_TIMEOUT = 10  # ms


def find_piuio():
    """Check if a PIUIO is on the USB bus. Returns True/False."""
    try:
        dev = usb.core.find(idVendor=PIUIO_VID, idProduct=PIUIO_PID)
        return dev is not None
    except Exception:
        return False


class PiuioDevice:
    """Manages USB connection and I/O for a PIUIO board."""

    def __init__(self):
        self.dev = None
        self.light_data = 0

    def open(self):
        """Find and claim the PIUIO USB device. Returns True on success."""
        self.dev = usb.core.find(idVendor=PIUIO_VID, idProduct=PIUIO_PID)
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

    def poll(self):
        """One poll cycle: 4 sensor-mux reads combined into a 32-bit field.

        Returns an int where bit=1 means pressed (already inverted from the
        active-low hardware).
        """
        combined = 0
        for i in range(4):
            # Select sensor set i
            self.light_data &= 0xFFFCFFFC
            self.light_data |= (i | (i << 16))
            out = self.light_data.to_bytes(4, "little").ljust(8, b"\x00")
            # Write selector
            self.dev.ctrl_transfer(
                0x40, PIUIO_CTL_REQ, 0, 0, out, REQ_TIMEOUT
            )
            # Read sensors
            data = self.dev.ctrl_transfer(
                0xC0, PIUIO_CTL_REQ, 0, 0, 8, REQ_TIMEOUT
            )
            raw = int.from_bytes(bytes(data[:4]), "little")
            combined |= ~raw & 0xFFFFFFFF
        return combined
