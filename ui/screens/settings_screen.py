from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QListWidget, QSlider, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from config import THEME, SENSOR_NAMES


class SettingsHubPage(QWidget):
    """Unified Settings Hub (Lighting, Access Control, Diagnostics)."""

    def __init__(self, callbacks, storage, parent=None):
        super().__init__(parent)
        self.cb = callbacks
        self.storage = storage

        self.setStyleSheet(f"background-color: {THEME['bg_dark']}; color: {THEME['text_main']};")
        layout = QHBoxLayout(self)

        # --- LEFT MENU ---
        menu_frame = QFrame()
        menu_frame.setFixedWidth(240)
        menu_frame.setStyleSheet(f"background-color: {THEME['menu_bg']}; border-right: 1px solid #ccc;")
        menu_layout = QVBoxLayout(menu_frame)

        lbl_settings = QLabel("SETTINGS")
        lbl_settings.setFont(QFont("Segoe UI", 20, QFont.Bold))
        lbl_settings.setStyleSheet(f"color: {THEME['text_dim']}; margin-bottom: 20px;")
        menu_layout.addWidget(lbl_settings)

        self.menu_list = QListWidget()
        self.menu_list.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.menu_list.addItem("Light Config")
        self.menu_list.addItem("Access Config")
        self.menu_list.addItem("Diagnostics")
        self.menu_list.setCurrentRow(0)
        self.menu_list.currentRowChanged.connect(self._change_page)
        self.menu_list.setStyleSheet(f"""
            QListWidget {{ border: none; background: transparent; outline: none; }}
            QListWidget::item {{ padding: 18px; color: {THEME['text_main']}; border-radius: 5px; }}
            QListWidget::item:selected {{
                background-color: {THEME['menu_sel']};
                color: black;
                border-left: 6px solid {THEME['accent_cyan']};
            }}
        """)
        menu_layout.addWidget(self.menu_list)

        btn_exit = QPushButton("BACK TO DASH")
        btn_exit.setFont(QFont("Segoe UI", 16, QFont.Bold))
        btn_exit.setStyleSheet("""
            background-color: #ddd;
            color: #333;
            padding: 18px;
            border-radius: 5px;
            border: 1px solid #bbb;
        """)
        btn_exit.clicked.connect(self.cb['return_to_dash'])
        menu_layout.addWidget(btn_exit)

        # --- RIGHT CONTENT (STACK) ---
        self.content_stack = QStackedWidget()

        self.page_light = QWidget()
        self._setup_light_config_ui(self.page_light)

        self.page_access = QWidget()
        self._setup_access_config_ui(self.page_access)

        self.page_diag = QWidget()
        self._setup_diagnostics_ui(self.page_diag)

        self.content_stack.addWidget(self.page_light)
        self.content_stack.addWidget(self.page_access)
        self.content_stack.addWidget(self.page_diag)

        layout.addWidget(menu_frame)
        layout.addWidget(self.content_stack)

    def _change_page(self, index):
        self.content_stack.setCurrentIndex(index)
        if index != 1:
            self.cb['cancel_add_key_mode']()
            self.lbl_access_status.setText("Status: Ready")
            self.lbl_access_status.setStyleSheet("color: #888;")

    # ==========================================
    #   TAB 1: INTERIOR LIGHTING
    # ==========================================
    def _setup_light_config_ui(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("INTERIOR LIGHTING")
        header.setFont(QFont("Segoe UI", 26, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"color: {THEME['accent_cyan']};")
        layout.addWidget(header)

        # Preview box
        self.color_preview = QLabel("PREVIEW")
        self.color_preview.setAlignment(Qt.AlignCenter)
        self.color_preview.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.color_preview.setMinimumHeight(100)
        self.color_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.color_preview, 2)

        # RGB Sliders
        slider_container = QWidget()
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setSpacing(12)
        slider_layout.setContentsMargins(0, 5, 0, 5)

        self.sliders = []
        labels = ["R", "G", "B"]
        colors = ["#ff5555", "#55ff55", "#5555ff"]
        init_rgb = self.storage.interior_rgb

        for i in range(3):
            row = QHBoxLayout()
            lbl = QLabel(labels[i])
            lbl.setFont(QFont("Arial", 22, QFont.Bold))
            lbl.setFixedWidth(50)
            lbl.setStyleSheet(f"color: {colors[i]};")
            row.addWidget(lbl)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(init_rgb[i])
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{ height: 16px; background: #444; border-radius: 8px; }}
                QSlider::handle:horizontal {{
                    background: {colors[i]};
                    width: 32px;
                    height: 32px;
                    margin: -8px 0;
                    border-radius: 16px;
                    border: 3px solid white;
                }}
                QSlider::sub-page:horizontal {{ background: {colors[i]}; border-radius: 8px; }}
            """)
            slider.valueChanged.connect(self._on_slider_changed)
            self.sliders.append(slider)
            row.addWidget(slider)
            slider_layout.addLayout(row)

        layout.addWidget(slider_container, 3)

        # Presets Grid
        grid = QGridLayout()
        grid.setSpacing(12)
        presets = [("ICE", 0, 255, 255), ("RED", 255, 0, 0), ("GRN", 0, 255, 0), ("BLU", 0, 0, 255)]
        for idx, (name, r, g, b) in enumerate(presets):
            btn = QPushButton(name)
            btn.setFont(QFont("Segoe UI", 16, QFont.Bold))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumHeight(65)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgb({r},{g},{b});
                    color: {'black' if (r+g+b)>300 else 'white'};
                    border-radius: 10px;
                    border: 2px solid #999;
                }}
            """)
            btn.clicked.connect(lambda _, r=r, g=g, b=b: self._set_sliders(r, g, b))
            grid.addWidget(btn, 0, idx)
        layout.addLayout(grid, 2)

        # Patterns Row
        p_layout = QHBoxLayout()
        p_layout.setSpacing(12)
        patterns = [("SOLID", "SOLID"), ("PULSE", "BREATHE"), ("RGB", "RAINBOW")]
        saved_mode = self.storage.interior_mode

        for name, mode in patterns:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumHeight(70)
            btn.setFont(QFont("Segoe UI", 16, QFont.Bold))
            if mode == saved_mode:
                btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #ddd;
                    color: #333;
                    border-radius: 10px;
                    border: 2px solid #ccc;
                }}
                QPushButton:checked {{
                    background-color: {THEME['accent_cyan']};
                    color: white;
                    border: 2px solid #005577;
                }}
            """)
            btn.clicked.connect(lambda _, m=mode: self._on_pattern_selected(m))
            p_layout.addWidget(btn)
        layout.addLayout(p_layout, 2)

        self._update_preview(init_rgb[0], init_rgb[1], init_rgb[2])

    def _set_sliders(self, r, g, b):
        self.sliders[0].setValue(r)
        self.sliders[1].setValue(g)
        self.sliders[2].setValue(b)

    def _on_slider_changed(self):
        r = self.sliders[0].value()
        g = self.sliders[1].value()
        b = self.sliders[2].value()
        self._update_preview(r, g, b)
        self.storage.set_interior_rgb(r, g, b)
        self.cb['set_interior_rgb'](r, g, b)

    def _update_preview(self, r, g, b):
        self.color_preview.setStyleSheet(f"""
            background-color: rgb({r},{g},{b});
            color: {'black' if (r+g+b)>300 else 'white'};
            border: 3px solid #333;
            border-radius: 15px;
        """)

    def _on_pattern_selected(self, mode):
        self.storage.set_interior_mode(mode)
        self.cb['set_interior_mode'](mode)

    # ==========================================
    #   TAB 2: ACCESS CONTROL
    # ==========================================
    def _setup_access_config_ui(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("ACCESS CONTROL")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet(f"color: {THEME['accent_green']};")
        layout.addWidget(header)

        self.list_keys = QListWidget()
        self.list_keys.setStyleSheet("background-color: #fff; color: #000; font-size: 16px; border: 1px solid #ccc; padding: 5px;")
        self.refresh_key_list()
        layout.addWidget(self.list_keys)

        self.lbl_access_status = QLabel("Status: Ready")
        self.lbl_access_status.setAlignment(Qt.AlignCenter)
        self.lbl_access_status.setFont(QFont("Segoe UI", 16))
        self.lbl_access_status.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.lbl_access_status)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        btn_add = QPushButton("SCAN NEW KEY")
        btn_add.setFont(QFont("Segoe UI", 16, QFont.Bold))
        btn_add.setStyleSheet(f"background-color: {THEME['accent_cyan']}; color: white; padding: 15px; border-radius: 8px;")
        btn_add.clicked.connect(self._start_scan_key)

        btn_del = QPushButton("DELETE SELECTED")
        btn_del.setFont(QFont("Segoe UI", 16, QFont.Bold))
        btn_del.setStyleSheet("background-color: #ddd; color: #333; padding: 15px; border-radius: 8px; border: 1px solid #bbb;")
        btn_del.clicked.connect(self._delete_selected_key)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

    def refresh_key_list(self):
        self.list_keys.clear()
        for key in self.storage.authorized_keys:
            self.list_keys.addItem(f"Card UID: {key}")

    def _start_scan_key(self):
        self.cb['start_add_key_mode']()
        self.lbl_access_status.setText("WAITING FOR CARD... TAP ON READER")
        self.lbl_access_status.setStyleSheet(f"color: {THEME['accent_amber']}; font-weight: bold; font-size: 16px;")

    def _delete_selected_key(self):
        selected = self.list_keys.selectedItems()
        if not selected:
            return

        key_str = selected[0].text().replace("Card UID: ", "").strip()
        confirm = QMessageBox()
        confirm.setIcon(QMessageBox.Warning)
        confirm.setText(f"Delete authorized key: {key_str}?")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setStyleSheet("background-color: #fff; color: black;")

        if confirm.exec_() == QMessageBox.Yes:
            self.storage.delete_authorized_key(key_str)
            self.refresh_key_list()
            self.lbl_access_status.setText(f"Deleted key {key_str}")
            self.lbl_access_status.setStyleSheet("color: #666;")

    # ==========================================
    #   TAB 3: SYSTEM DIAGNOSTICS
    # ==========================================
    def _setup_diagnostics_ui(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("SYSTEM DIAGNOSTICS")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet(f"color: {THEME['accent_amber']};")
        layout.addWidget(header)

        self.diag_table = QTableWidget()
        self.diag_table.setColumnCount(3)
        self.diag_table.setHorizontalHeaderLabels(["Sensor", "Value", "Status"])
        self.diag_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.diag_table.verticalHeader().setVisible(False)
        self.diag_table.setStyleSheet("""
            QTableWidget {{ background-color: #fff; color: #000; font-size: 15px; border: 1px solid #ccc; }}
            QHeaderView::section {{ background-color: #eee; padding: 6px; font-weight: bold; border: 1px solid #ccc; }}
        """)

        self.diag_rows = list(SENSOR_NAMES) + ["Temperature", "Humidity", "NFC System"]
        self.diag_table.setRowCount(len(self.diag_rows))

        for i, name in enumerate(self.diag_rows):
            self.diag_table.setItem(i, 0, QTableWidgetItem(name))
            self.diag_table.setItem(i, 1, QTableWidgetItem("--"))
            self.diag_table.setItem(i, 2, QTableWidgetItem("Init"))

        layout.addWidget(self.diag_table)

    def update_diagnostics_data(self, distances, temp_data, nfc_online):
        # 8 ultrasonic sensors
        for i in range(min(8, len(distances))):
            dist = distances[i]
            val = f"{dist:.1f} cm"
            if dist == 0.0:
                status = "CLEAR / NO ECHO"
                color = QColor(100, 100, 100)
            elif dist < 30.0:
                status = "CRITICAL"
                color = QColor(220, 0, 0)
            elif dist < 70.0:
                status = "WARNING"
                color = QColor(220, 140, 0)
            else:
                status = "OK"
                color = QColor(0, 160, 0)

            self.diag_table.item(i, 1).setText(val)
            self.diag_table.item(i, 2).setText(status)
            self.diag_table.item(i, 2).setForeground(color)

        # Temperature & Humidity
        t = temp_data.get("t", 0.0)
        h = temp_data.get("h", 0.0)
        self.diag_table.item(8, 1).setText(f"{t:.1f} °C")
        self.diag_table.item(8, 2).setText("OK" if t > 0 else "OFFLINE")
        self.diag_table.item(9, 1).setText(f"{h:.1f} %")
        self.diag_table.item(9, 2).setText("OK" if h > 0 else "OFFLINE")

        # NFC Reader Status
        nfc_stat = "ACTIVE" if nfc_online else "ERROR"
        self.diag_table.item(10, 1).setText("SPI 50kHz")
        self.diag_table.item(10, 2).setText(nfc_stat)
        self.diag_table.item(10, 2).setForeground(QColor(0, 160, 0) if nfc_online else QColor(220, 0, 0))
