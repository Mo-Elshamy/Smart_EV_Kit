#!/usr/bin/env python3
"""Smart EV Kit - Vehicle Control Unit Dashboard (software_V2.0).

Entrypoint executed automatically on vehicle boot.
"""
import sys
import os
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
