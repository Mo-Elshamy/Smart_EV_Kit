from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from config import THEME
from ui.styles import apply_background, create_icon_button, create_turn_button, create_push_button
from ui.widgets.parking_radar import ParkingVisualizer


class DashboardPage(QWidget):
    """Main Driving Dashboard view."""

    def __init__(self, callbacks, parent=None):
        super().__init__(parent)
        self.cb = callbacks
        apply_background(self)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(5, 5, 5, 5)
        root_layout.setSpacing(5)

        # --- TOP SECTION: Visualizer (Left) + Telemetry & Controls (Right) ---
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # Left: Parking Visualizer Container
        self.parking_viz = ParkingVisualizer()
        viz_container = QFrame()
        viz_container.setStyleSheet(f"background-color: {THEME['bg_panel']}; border: 1px solid #ccc; border-radius: 15px;")
        viz_layout = QVBoxLayout(viz_container)
        viz_layout.addWidget(self.parking_viz)
        top_row.addWidget(viz_container, 60)

        # Right: Telemetry & Controls Frame
        controls_frame = QFrame()
        controls_frame.setStyleSheet(f"background-color: {THEME['bg_panel']}; border-radius: 15px; border: 1px solid #ccc;")
        right_layout = QVBoxLayout(controls_frame)
        right_layout.setContentsMargins(10, 12, 10, 12)
        right_layout.setSpacing(8)

        # Clock & Date (Vertically expanded to reach Light and Reverse buttons)
        self.lbl_clock = QLabel("--:--")
        self.lbl_clock.setAlignment(Qt.AlignCenter)
        self.lbl_clock.setFont(QFont("Segoe UI", 72, QFont.Bold))
        self.lbl_clock.setStyleSheet(f"color: {THEME['text_main']};")
        self.lbl_clock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.lbl_date = QLabel("--/--")
        self.lbl_date.setAlignment(Qt.AlignCenter)
        self.lbl_date.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.lbl_date.setStyleSheet(f"color: {THEME['accent_cyan']}; letter-spacing: 3px;")
        self.lbl_date.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_layout.addWidget(self.lbl_clock, 3)
        right_layout.addWidget(self.lbl_date, 1)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #ccc; margin: 4px 0;")
        right_layout.addWidget(divider)

        # Temp & Humidity (Large high-contrast display)
        self.lbl_temp = QLabel("24°C  50%")
        self.lbl_temp.setAlignment(Qt.AlignCenter)
        self.lbl_temp.setFont(QFont("Segoe UI", 42, QFont.Bold))
        self.lbl_temp.setStyleSheet(f"color: {THEME['text_main']};")
        self.lbl_temp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.lbl_temp, 2)

        # Authenticated User ID
        self.lbl_user = QLabel("Welcome User")
        self.lbl_user.setAlignment(Qt.AlignCenter)
        self.lbl_user.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.lbl_user.setStyleSheet(f"color: {THEME['accent_green']}; margin-top: 4px;")
        self.lbl_user.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.lbl_user, 1)

        # Main Driving Icon Buttons Grid (Enlarged for touch)
        btn_grid = QGridLayout()
        btn_grid.setSpacing(12)

        self.btn_lights = create_icon_button("💡", self._on_lights_clicked)
        self.btn_lights.setFont(QFont("Segoe UI", 60))
        self.btn_lights.setMinimumHeight(135)

        self.btn_reverse = create_icon_button("R", self._on_reverse_clicked, is_reverse=True)
        self.btn_reverse.setFont(QFont("Segoe UI", 60, QFont.Bold))
        self.btn_reverse.setMinimumHeight(135)

        self.btn_lock = create_icon_button("🔒", self._on_lock_clicked, is_red=True)
        self.btn_lock.setFont(QFont("Segoe UI", 60))
        self.btn_lock.setMinimumHeight(135)

        btn_grid.addWidget(self.btn_lights, 0, 0)
        btn_grid.addWidget(self.btn_reverse, 0, 1)
        btn_grid.addWidget(self.btn_lock, 1, 0, 1, 2)
        right_layout.addLayout(btn_grid)

        # Underglow & Settings Row
        config_row = QHBoxLayout()
        config_row.setSpacing(12)
        self.btn_body = create_push_button("UNDERGLOW", self._on_body_clicked, min_height=95, font_size=22, checkable=True)
        self.btn_body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        btn_cfg = QPushButton("⚙")
        btn_cfg.setFixedSize(95, 95)
        btn_cfg.setFont(QFont("Segoe UI", 48))
        btn_cfg.setStyleSheet(f"""
            QPushButton {{
                background-color: #ddd;
                color: #333;
                border-radius: 14px;
                border: 2px solid #bbb;
            }}
            QPushButton:pressed {{
                background-color: #bbb;
            }}
        """)
        btn_cfg.clicked.connect(self._on_settings_clicked)

        config_row.addWidget(self.btn_body)
        config_row.addWidget(btn_cfg)
        right_layout.addLayout(config_row)

        top_row.addWidget(controls_frame, 40)
        root_layout.addLayout(top_row)

        # --- BOTTOM SECTION: Turn Signals & Hazard ---
        bot_row = QHBoxLayout()
        bot_row.setSpacing(10)

        self.btn_left = create_turn_button("⬅", lambda: self._on_turn_clicked("LEFT", self.btn_left))
        self.btn_haz = create_turn_button("⚠", lambda: self._on_turn_clicked("HAZARD", self.btn_haz), is_hazard=True)
        self.btn_right = create_turn_button("➡", lambda: self._on_turn_clicked("RIGHT", self.btn_right))

        bot_row.addWidget(self.btn_left)
        bot_row.addWidget(self.btn_haz)
        bot_row.addWidget(self.btn_right)
        root_layout.addLayout(bot_row)

    def _on_lights_clicked(self):
        state = self.btn_lights.isChecked()
        self.cb['toggle_main_lights'](state)

    def _on_reverse_clicked(self):
        state = self.btn_reverse.isChecked()
        self.cb['toggle_reverse'](state)

    def _on_lock_clicked(self):
        self.cb['prompt_lock']()

    def _on_body_clicked(self):
        state = self.btn_body.isChecked()
        self.cb['toggle_interior_lights'](state)

    def _on_settings_clicked(self):
        self.cb['open_settings']()

    def _on_turn_clicked(self, mode, btn):
        if mode == "LEFT":
            self.btn_right.setChecked(False)
            self.btn_haz.setChecked(False)
        elif mode == "RIGHT":
            self.btn_left.setChecked(False)
            self.btn_haz.setChecked(False)
        elif mode == "HAZARD":
            self.btn_left.setChecked(False)
            self.btn_right.setChecked(False)

        signal_mode = mode if btn.isChecked() else "OFF"
        self.cb['set_turn_signal'](signal_mode)

    def reset_controls(self):
        """Unchecks all buttons when vehicle is locked."""
        self.btn_lights.setChecked(False)
        self.btn_reverse.setChecked(False)
        self.btn_body.setChecked(False)
        self.btn_left.setChecked(False)
        self.btn_haz.setChecked(False)
        self.btn_right.setChecked(False)

