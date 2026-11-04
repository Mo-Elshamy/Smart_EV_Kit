#!/usr/bin/env python3
"""Smart EV Kit - Vehicle Control Unit Dashboard (software_V2.0).

Entrypoint executed automatically on vehicle boot.
"""
import sys
import os

# Chromium flags for root / kiosk mode and GPU-accelerated WebGL rendering
flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
required_flags = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--ignore-gpu-blocklist",
    "--enable-gpu-rasterization"
]
for rf in required_flags:
    if rf not in flags:
        flags = (flags + " " + rf).strip()
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = flags

try:
    from PyQt5.QtWebEngine import QtWebEngine
    QtWebEngine.initialize()
except ImportError:
    pass

from PyQt5.QtWidgets import QApplication
from ui.main_window import EVSystem


def main():
    if os.environ.get("DISPLAY") is None:
        os.environ["DISPLAY"] = ":0"

    app = QApplication(sys.argv)
    window = EVSystem()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
