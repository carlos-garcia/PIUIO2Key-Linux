#!/usr/bin/env python3
"""
piu_bridge.py - Launcher for the PIU IO Bridge.

All logic lives in the `piubridge` package (same folder). This file only
bootstraps the Python path so the script works whether invoked as
`python3 piu_bridge.py` or `python3 linux/piu_bridge.py` from elsewhere.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from piubridge.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
