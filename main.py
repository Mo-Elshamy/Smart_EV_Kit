#!/usr/bin/env python3
"""Smart EV Kit - Vehicle Control Unit Dashboard (software_V2.0).

Entrypoint executed automatically on vehicle boot.
"""
import sys
import os

# Chromium sandbox flags for running under root / vehicle kiosk mode
flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
if "--no-sandbox" not in flags:
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (flags + " --no-sandbox --disable-dev-shm-usage").strip()

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
