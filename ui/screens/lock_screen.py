import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap
from config import THEME, LOGO_PNG_PATH, BG_PNG_PATH
from ui.styles import apply_background


class LockScreenPage(QWidget):
    """The default locked idle screen with brand logo."""

    def __init__(self, on_enter_pin, parent=None):
        super().__init__(parent)
        apply_background(self)
        layout = QVBoxLayout(self)

        lbl_welcome = QLabel("Welcome to RQ EV Car")
        lbl_welcome.setAlignment(Qt.AlignCenter)
        lbl_welcome.setFont(QFont("Segoe UI", 36, QFont.Bold))
        lbl_welcome.setStyleSheet("color: black; margin-top: 30px;")
        layout.addWidget(lbl_welcome)

        layout.addStretch(1)

        # Prominent Brand Logo (fills the screen width)
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.lbl_logo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        logo_path = LOGO_PNG_PATH if os.path.exists(LOGO_PNG_PATH) else BG_PNG_PATH
        self.orig_logo_pixmap = QPixmap(logo_path) if os.path.exists(logo_path) else QPixmap()
        self._update_logo_size()
        layout.addWidget(self.lbl_logo)

        layout.addStretch(1)

        bot_row = QHBoxLayout()
        btn_pass = QPushButton("ENTER PIN")
        btn_pass.setFixedSize(160, 60)
        btn_pass.setFont(QFont("Segoe UI", 14, QFont.Bold))
        btn_pass.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['bg_panel']};
                color: {THEME['text_main']};
                border: 2px solid #aaa;
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: #ddd;
                color: black;
            }}
        """)
        btn_pass.clicked.connect(on_enter_pin)

        lbl_scan = QLabel("SCAN CARD ⬇️")
        lbl_scan.setAlignment(Qt.AlignCenter)
        lbl_scan.setFont(QFont("Segoe UI", 18, QFont.Bold))
        lbl_scan.setStyleSheet("""
            color: black;
            font-weight: bold;
            background: rgba(255, 255, 255, 0.75);
            border-radius: 10px;
            padding: 10px 20px;
            border: 1px solid #ccc;
        """)

        bot_row.addSpacing(20)
        bot_row.addWidget(btn_pass)
        bot_row.addStretch()
        bot_row.addWidget(lbl_scan)
        bot_row.addSpacing(20)

        layout.addLayout(bot_row)
        layout.addSpacing(30)

    def _update_logo_size(self):
        if hasattr(self, 'orig_logo_pixmap') and not self.orig_logo_pixmap.isNull():
            w = self.width() if self.width() > 100 else 1920
            h = self.height() if self.height() > 100 else 1080
            target_w = max(300, int(w * 0.92))
            target_h = max(100, int(h * 0.58))
            self.lbl_logo.setPixmap(
                self.orig_logo_pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_logo_size()


class PinScreenPage(QWidget):
    """Touchscreen Numeric PIN entry page."""

    def __init__(self, on_pin_success, on_cancel, get_valid_pin_fn, parent=None):
        super().__init__(parent)
        self.on_pin_success = on_pin_success
        self.on_cancel = on_cancel
        self.get_valid_pin_fn = get_valid_pin_fn
        self.pin_buffer = ""

        apply_background(self)
        layout = QVBoxLayout(self)

        self.lbl_pin_display = QLabel("Enter PIN")
        self.lbl_pin_display.setAlignment(Qt.AlignCenter)
        self.lbl_pin_display.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self.lbl_pin_display.setStyleSheet(f"color: {THEME['text_main']}; margin: 15px;")
        layout.addWidget(self.lbl_pin_display)

        grid = QGridLayout()
        grid.setSpacing(10)

        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('⌫', 3, 0), ('0', 3, 1), ('OK', 3, 2),
            ('CANCEL', 4, 0, 1, 3)
        ]

        for item in keys:
            text = item[0]
            r, c = item[1], item[2]
            rowspan = item[3] if len(item) > 3 else 1
            colspan = item[4] if len(item) > 4 else 1

            btn = QPushButton(text)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            if text == 'OK':
                btn.setFont(QFont("Segoe UI", 28, QFont.Bold))
                btn.setStyleSheet(f"background-color: {THEME['accent_green']}; color: white; border-radius: 10px;")
                btn.clicked.connect(self._check_pin)
            elif text == '⌫':
                btn.setFont(QFont("Segoe UI", 28, QFont.Bold))
                btn.setStyleSheet("background-color: #e0e0e0; color: #333; border-radius: 10px; border: 1px solid #ccc;")
                btn.clicked.connect(self._backspace)
            elif text == 'CANCEL':
                btn.setFont(QFont("Segoe UI", 16, QFont.Bold))
                btn.setFixedHeight(50)
                btn.setStyleSheet(f"background-color: {THEME['accent_red']}; color: white; border-radius: 10px;")
                btn.clicked.connect(self._cancel)
            else:
                btn.setFont(QFont("Segoe UI", 32, QFont.Bold))
                btn.setStyleSheet(f"background-color: {THEME['bg_panel']}; color: {THEME['text_main']}; border-radius: 10px; border: 1px solid #ccc;")
                btn.clicked.connect(lambda _, t=text: self._add_digit(t))

            grid.addWidget(btn, r, c, rowspan, colspan)

        layout.addLayout(grid)

    def _add_digit(self, digit):
        if len(self.pin_buffer) < 8:
            self.pin_buffer += digit
            self.lbl_pin_display.setText("● " * len(self.pin_buffer))

    def _backspace(self):
        if self.pin_buffer:
            self.pin_buffer = self.pin_buffer[:-1]
            if self.pin_buffer:
                self.lbl_pin_display.setText("● " * len(self.pin_buffer))
            else:
                self.lbl_pin_display.setText("Enter PIN")

    def _cancel(self):
        self.pin_buffer = ""
        self.lbl_pin_display.setText("Enter PIN")
        self.on_cancel()

    def _check_pin(self):
        valid_pin = self.get_valid_pin_fn()
        if self.pin_buffer == valid_pin:
            self.pin_buffer = ""
            self.lbl_pin_display.setText("Enter PIN")
            self.on_pin_success("MANUAL_PIN")
        else:
            self.lbl_pin_display.setText("WRONG PIN!")
            self.lbl_pin_display.setStyleSheet("color: red; margin: 15px;")
            QTimer.singleShot(1000, self._reset_display)
            self.pin_buffer = ""

    def _reset_display(self):
        self.lbl_pin_display.setStyleSheet(f"color: {THEME['text_main']}; margin: 15px;")
        self.lbl_pin_display.setText("Enter PIN")


class ConfirmLockPage(QWidget):
    """Safety confirmation prompt before locking vehicle."""

    def __init__(self, on_confirm_lock, on_cancel, parent=None):
        super().__init__(parent)
        apply_background(self)
        layout = QVBoxLayout(self)
        layout.addStretch()

        lbl_prompt = QLabel("LOCK VEHICLE?")
        lbl_prompt.setAlignment(Qt.AlignCenter)
        lbl_prompt.setFont(QFont("Segoe UI", 32, QFont.Bold))
        lbl_prompt.setStyleSheet(f"color: {THEME['text_main']}; margin-bottom: 30px;")
        layout.addWidget(lbl_prompt)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        btn_no = QPushButton("CANCEL")
        btn_no.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_no.setFixedHeight(110)
        btn_no.setFont(QFont("Segoe UI", 20, QFont.Bold))
        btn_no.setStyleSheet(f"background-color: {THEME['bg_panel']}; color: {THEME['text_main']}; border-radius: 15px; border: 1px solid #ccc;")
        btn_no.clicked.connect(on_cancel)

        btn_yes = QPushButton("YES, LOCK")
        btn_yes.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_yes.setFixedHeight(110)
        btn_yes.setFont(QFont("Segoe UI", 20, QFont.Bold))
        btn_yes.setStyleSheet(f"background-color: {THEME['accent_red']}; color: white; border-radius: 15px;")
        btn_yes.clicked.connect(on_confirm_lock)

        btn_row.addWidget(btn_no)
        btn_row.addWidget(btn_yes)
        layout.addLayout(btn_row)
        layout.addSpacing(40)

