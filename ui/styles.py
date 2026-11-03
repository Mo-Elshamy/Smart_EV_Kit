import os
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from config import THEME, BG_PNG_PATH, BG_JPG_PATH


def apply_background(widget):
    """Apply PNG or JPG background image to a QWidget if available."""
    widget.setObjectName("bg_widget")
    bg_style = f"background-color: {THEME['bg_dark']};"

    if os.path.exists(BG_PNG_PATH):
        bg_style += f" border-image: url({BG_PNG_PATH.replace(os.sep, '/')}) 0 0 0 0 stretch stretch;"
    elif os.path.exists(BG_JPG_PATH):
        bg_style += f" border-image: url({BG_JPG_PATH.replace(os.sep, '/')}) 0 0 0 0 stretch stretch;"

    widget.setStyleSheet(f"""
        QWidget#bg_widget {{ {bg_style} }}
        QLabel {{ background: transparent; color: {THEME['text_main']}; font-family: 'Segoe UI'; }}
    """)


def create_push_button(text, on_click=None, min_height=60, font_size=12, checkable=False):
    """Creates a standard styled button."""
    btn = QPushButton(text)
    btn.setFont(QFont("Segoe UI", font_size, QFont.Bold))
    btn.setCheckable(checkable)
    if min_height > 0:
        btn.setMinimumHeight(min_height)

    btn.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0f0f0, stop:1 #d0d0d0);
            color: {THEME['text_main']};
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #aaa;
        }}
        QPushButton:checked {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {THEME['accent_cyan']}, stop:1 #006699);
            color: white;
            border: 1px solid {THEME['accent_cyan']};
        }}
        QPushButton:pressed {{
            background: #bbb;
        }}
    """)
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def create_icon_button(icon_text, on_click=None, is_red=False, is_reverse=False):
    """Creates large icon buttons for Driving Controls (Headlights, Reverse, Lock)."""
    btn = QPushButton(icon_text)
    btn.setFont(QFont("Segoe UI", 48))
    btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    btn.setMinimumSize(80, 80)
    btn.setCheckable(not is_red)

    if is_red:
        active_color = THEME['accent_red']
    elif is_reverse:
        active_color = THEME['accent_amber']
    else:
        active_color = THEME['accent_cyan']

    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #444444;
            color: white;
            border-radius: 15px;
            border: 2px solid #666666;
        }}
        QPushButton:checked {{
            background-color: {active_color};
            color: black;
            border: 2px solid white;
        }}
        QPushButton:pressed {{
            background-color: #666666;
        }}
    """)
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def create_turn_button(arrow_text, on_click=None, is_hazard=False):
    """Creates turn signal & hazard warning buttons."""
    btn = QPushButton(arrow_text)
    btn.setFont(QFont("Segoe UI", 26, QFont.Bold))
    btn.setMinimumHeight(120)
    btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    btn.setCheckable(True)

    color = THEME['accent_red'] if is_hazard else THEME['accent_amber']
    text_color = "#cc0000" if is_hazard else "#cc8800"

    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.65);
            color: {text_color};
            border-radius: 10px;
            border: 2px solid {text_color};
        }}
        QPushButton:checked {{
            background-color: {color};
            color: white;
        }}
    """)
    if on_click:
        btn.clicked.connect(on_click)
    return btn

