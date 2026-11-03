from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QListWidget, QSlider, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from config import THEME, SENSOR_NAMES


class SettingsHubPage(QWidget):
    """Unified Settings Hub (Lighting, Access Control, Diagnostics) — Enlarged for 1080p."""

    def __init__(self, callbacks, storage, parent=None):
        super().__init__(parent)
        self.cb = callbacks
        self.storage = storage

        self.setStyleSheet(f"background-color: {THEME['bg_dark']}; color: {THEME['text_main']};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # --- LEFT MENU (Enlarged) ---
        menu_frame = QFrame()
        menu_frame.setFixedWidth(340)
        menu_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['menu_bg']};
                border-radius: 16px;
                border: 2px solid #ccc;
            }}
        """)
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setContentsMargins(15, 25, 15, 25)
        menu_layout.setSpacing(18)

        lbl_settings = QLabel("SETTINGS")
        lbl_settings.setAlignment(Qt.AlignCenter)
        lbl_settings.setFont(QFont("Segoe UI", 30, QFont.Bold))
        lbl_settings.setStyleSheet(f"color: {THEME['text_dim']}; margin-bottom: 15px;")
        menu_layout.addWidget(lbl_settings)

        self.menu_list = QListWidget()
        self.menu_list.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.menu_list.addItem("Light Config")
        self.menu_list.addItem("Access Config")
        self.menu_list.addItem("Diagnostics")
        self.menu_list.setCurrentRow(0)
        self.menu_list.currentRowChanged.connect(self._change_page)
        self.menu_list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background: transparent;
                outline: none;
            }}
            QListWidget::item {{
                padding: 24px 18px;
                color: {THEME['text_main']};
                border-radius: 12px;
                margin-bottom: 10px;
            }}
            QListWidget::item:selected {{
                background-color: {THEME['menu_sel']};
                color: black;
                border-left: 10px solid {THEME['accent_cyan']};
            }}
        """)
        menu_layout.addWidget(self.menu_list)

        btn_exit = QPushButton("⬅ BACK TO DASH")
        btn_exit.setFont(QFont("Segoe UI", 22, QFont.Bold))
        btn_exit.setMinimumHeight(95)
        btn_exit.setStyleSheet("""
            QPushButton {{
                background-color: #ddd;
                color: #222;
                border-radius: 14px;
                border: 2px solid #bbb;
            }}
            QPushButton:pressed {{
                background-color: #bbb;
            }}
        """)
        btn_exit.clicked.connect(self.cb['return_to_dash'])
        menu_layout.addWidget(btn_exit)

        # --- RIGHT CONTENT STACK ---
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
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(16)

        header = QLabel("INTERIOR LIGHTING")
        header.setFont(QFont("Segoe UI", 32, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"color: {THEME['accent_cyan']};")
        layout.addWidget(header)

        # Preview box (Taller & cleaner)
        self.color_preview = QLabel("PREVIEW")
        self.color_preview.setAlignment(Qt.AlignCenter)
        self.color_preview.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.color_preview.setMinimumHeight(130)
        self.color_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.color_preview, 2)

        # RGB Sliders (Chunky touch-friendly track & handles)
        slider_container = QWidget()
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setSpacing(16)
        slider_layout.setContentsMargins(0, 5, 0, 5)

        self.sliders = []
        labels = ["R", "G", "B"]
        colors = ["#ff4444", "#44cc44", "#4444ff"]
        init_rgb = self.storage.interior_rgb

        for i in range(3):
            row = QHBoxLayout()
            lbl = QLabel(labels[i])
            lbl.setFont(QFont("Arial", 28, QFont.Bold))
            lbl.setFixedWidth(60)
            lbl.setStyleSheet(f"color: {colors[i]};")
            row.addWidget(lbl)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(init_rgb[i])
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    height: 24px;
                    background: #444;
                    border-radius: 12px;
                }}
                QSlider::handle:horizontal {{
                    background: {colors[i]};
                    width: 48px;
                    height: 48px;
                    margin: -12px 0;
                    border-radius: 24px;
                    border: 4px solid white;
                }}
                QSlider::sub-page:horizontal {{
                    background: {colors[i]};
                    border-radius: 12px;
                }}
            """)
            slider.valueChanged.connect(self._on_slider_changed)
            self.sliders.append(slider)
            row.addWidget(slider)
            slider_layout.addLayout(row)

        layout.addWidget(slider_container, 3)

        # Presets Grid (Enlarged)
        grid = QGridLayout()
        grid.setSpacing(14)
        presets = [("ICE", 0, 255, 255), ("RED", 255, 0, 0), ("GRN", 0, 255, 0), ("BLU", 0, 0, 255)]
        for idx, (name, r, g, b) in enumerate(presets):
            btn = QPushButton(name)
            btn.setFont(QFont("Segoe UI", 22, QFont.Bold))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumHeight(95)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgb({r},{g},{b});
                    color: {'black' if (r+g+b)>300 else 'white'};
                    border-radius: 14px;
                    border: 3px solid #777;
                }}
                QPushButton:pressed {{
                    border: 3px solid white;
                }}
            """)
            btn.clicked.connect(lambda _, r=r, g=g, b=b: self._set_sliders(r, g, b))
            grid.addWidget(btn, 0, idx)
        layout.addLayout(grid, 2)

        # Patterns Row (Enlarged)
        p_layout = QHBoxLayout()
        p_layout.setSpacing(14)
        patterns = [("SOLID", "SOLID"), ("PULSE", "BREATHE"), ("RGB", "RAINBOW")]
        saved_mode = self.storage.interior_mode

        for name, mode in patterns:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumHeight(95)
            btn.setFont(QFont("Segoe UI", 22, QFont.Bold))
            if mode == saved_mode:
                btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #ddd;
                    color: #333;
                    border-radius: 14px;
                    border: 2px solid #ccc;
                }}
                QPushButton:checked {{
                    background-color: {THEME['accent_cyan']};
                    color: white;
                    border: 3px solid #005577;
                }}
                QPushButton:pressed {{
                    background-color: #bbb;
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
            border: 4px solid #333;
            border-radius: 18px;
        """)

    def _on_pattern_selected(self, mode):
        self.storage.set_interior_mode(mode)
        self.cb['set_interior_mode'](mode)

    # ==========================================
    #   TAB 2: ACCESS CONTROL (Enlarged)
    # ==========================================
    def _setup_access_config_ui(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header = QLabel("ACCESS CONTROL")
        header.setFont(QFont("Segoe UI", 36, QFont.Bold))
        header.setStyleSheet(f"color: {THEME['accent_green']};")
        layout.addWidget(header)

        self.list_keys = QListWidget()
        self.list_keys.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.list_keys.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                color: #111111;
                font-size: 28px;
                font-weight: bold;
                border: 3px solid #94a3b8;
                border-radius: 16px;
                padding: 12px;
            }
            QListWidget::item {
                padding: 24px 20px;
                border-bottom: 2px solid #e2e8f0;
                min-height: 50px;
            }
            QListWidget::item:selected {
                background-color: #0284c7;
                color: #ffffff;
                border-radius: 12px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 26px;
                border-radius: 13px;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                min-height: 40px;
                border-radius: 13px;
            }
        """)
        self.refresh_key_list()
        layout.addWidget(self.list_keys, 1)

        self.lbl_access_status = QLabel("Status: Ready")
        self.lbl_access_status.setAlignment(Qt.AlignCenter)
        self.lbl_access_status.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.lbl_access_status.setStyleSheet("color: #334155; background-color: #f1f5f9; border-radius: 14px; border: 2px solid #cbd5e1; padding: 12px;")
        self.lbl_access_status.setMinimumHeight(75)
        layout.addWidget(self.lbl_access_status)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        btn_add = QPushButton("SCAN NEW KEY ⬆️")
        btn_add.setFont(QFont("Segoe UI", 24, QFont.Bold))
        btn_add.setMinimumHeight(100)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_cyan']};
                color: white;
                border-radius: 16px;
                border: 2px solid #006699;
                padding: 15px;
            }}
            QPushButton:pressed {{
                background-color: #006699;
            }}
        """)
        btn_add.clicked.connect(self._start_scan_key)

        btn_del = QPushButton("DELETE SELECTED 🗑️")
        btn_del.setFont(QFont("Segoe UI", 24, QFont.Bold))
        btn_del.setMinimumHeight(100)
        btn_del.setStyleSheet("""
            QPushButton {{
                background-color: #e2e8f0;
                color: #1e293b;
                border-radius: 16px;
                border: 2px solid #94a3b8;
                padding: 15px;
            }}
            QPushButton:pressed {{
                background-color: #cbd5e1;
            }}
        """)
        btn_del.clicked.connect(self._delete_selected_key)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

    def refresh_key_list(self):
        self.list_keys.clear()
        font = QFont("Segoe UI", 28, QFont.Bold)
        for key in self.storage.authorized_keys:
            from PyQt5.QtWidgets import QListWidgetItem
            item = QListWidgetItem(f"💳   Card UID:   {key}")
            item.setFont(font)
            self.list_keys.addItem(item)

    def _start_scan_key(self):
        self.cb['start_add_key_mode']()
        self.lbl_access_status.setText("WAITING FOR CARD... TAP ON READER ⬆️")
        self.lbl_access_status.setStyleSheet(f"color: {THEME['accent_amber']}; background-color: #fef3c7; border: 2px solid #f59e0b; border-radius: 14px; font-weight: bold; font-size: 26px; padding: 12px;")

    def _delete_selected_key(self):
        selected = self.list_keys.selectedItems()
        if not selected:
            return

        key_str = selected[0].text().replace("💳   Card UID:   ", "").strip()
        confirm = QMessageBox()
        confirm.setIcon(QMessageBox.Warning)
        confirm.setText(f"Delete authorized key:\n\n{key_str}?")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setStyleSheet("background-color: #fff; color: black; font-size: 24px; font-weight: bold;")

        if confirm.exec_() == QMessageBox.Yes:
            self.storage.delete_authorized_key(key_str)
            self.refresh_key_list()
            self.lbl_access_status.setText(f"Deleted key: {key_str}")
            self.lbl_access_status.setStyleSheet("color: #475569; background-color: #f1f5f9; border-radius: 14px; border: 2px solid #cbd5e1; font-size: 24px; padding: 12px;")

    # ==========================================
    #   TAB 3: SYSTEM DIAGNOSTICS (Enlarged)
    # ==========================================
    def _setup_diagnostics_ui(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        header = QLabel("SYSTEM DIAGNOSTICS")
        header.setFont(QFont("Segoe UI", 36, QFont.Bold))
        header.setStyleSheet(f"color: {THEME['accent_amber']};")
        layout.addWidget(header)

        self.diag_table = QTableWidget()
        self.diag_table.setColumnCount(3)
        self.diag_table.setHorizontalHeaderLabels(["Sensor / Module", "Measured Value", "Status"])
        self.diag_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.diag_table.horizontalHeader().setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.diag_table.verticalHeader().setVisible(False)
        self.diag_table.verticalHeader().setDefaultSectionSize(65)
        self.diag_table.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.diag_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #111111;
                font-size: 26px;
                font-weight: bold;
                border: 3px solid #94a3b8;
                border-radius: 16px;
                gridline-color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #e2e8f0;
                color: #0f172a;
                padding: 14px;
                font-size: 26px;
                font-weight: bold;
                border: 1px solid #94a3b8;
            }
            QTableWidget::item {
                padding: 8px 14px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 26px;
                border-radius: 13px;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                min-height: 40px;
                border-radius: 13px;
            }
        """)

        self.diag_rows = list(SENSOR_NAMES) + ["Temperature", "Humidity", "NFC System"]
        self.diag_table.setRowCount(len(self.diag_rows))

        font_name = QFont("Segoe UI", 24, QFont.Bold)
        font_val = QFont("Segoe UI", 26, QFont.Bold)

        for i, name in enumerate(self.diag_rows):
            item_name = QTableWidgetItem(f"  {name}")
            item_name.setFont(font_name)

            item_val = QTableWidgetItem("--")
            item_val.setFont(font_val)
            item_val.setTextAlignment(Qt.AlignCenter)

            item_stat = QTableWidgetItem("Init")
            item_stat.setFont(font_val)
            item_stat.setTextAlignment(Qt.AlignCenter)

            self.diag_table.setItem(i, 0, item_name)
            self.diag_table.setItem(i, 1, item_val)
            self.diag_table.setItem(i, 2, item_stat)

        layout.addWidget(self.diag_table)

    def update_diagnostics_data(self, distances, temp_data, nfc_online):
        font_val = QFont("Segoe UI", 26, QFont.Bold)

        # 8 ultrasonic sensors
        for i in range(min(8, len(distances))):
            dist = distances[i]
            val = f"{dist:.1f} cm"
            if dist == 0.0:
                status = "CLEAR"
                color = QColor(100, 116, 139)
            elif dist < 30.0:
                status = "CRITICAL"
                color = QColor(220, 38, 38)
            elif dist < 70.0:
                status = "WARNING"
                color = QColor(217, 119, 6)
            else:
                status = "OK"
                color = QColor(22, 163, 74)

            item_val = self.diag_table.item(i, 1)
            item_val.setText(val)
            item_val.setFont(font_val)

            item_stat = self.diag_table.item(i, 2)
            item_stat.setText(status)
            item_stat.setFont(font_val)
            item_stat.setForeground(color)

        # Temperature & Humidity
        t = temp_data.get("t", 0.0)
        h = temp_data.get("h", 0.0)

        item_t = self.diag_table.item(8, 1)
        item_t.setText(f"{t:.1f} °C")
        item_t.setFont(font_val)

        item_stat_t = self.diag_table.item(8, 2)
        item_stat_t.setText("ONLINE" if t > 0 else "OFFLINE")
        item_stat_t.setFont(font_val)
        item_stat_t.setForeground(QColor(22, 163, 74) if t > 0 else QColor(220, 38, 38))

        item_h = self.diag_table.item(9, 1)
        item_h.setText(f"{h:.1f} %")
        item_h.setFont(font_val)

        item_stat_h = self.diag_table.item(9, 2)
        item_stat_h.setText("ONLINE" if h > 0 else "OFFLINE")
        item_stat_h.setFont(font_val)
        item_stat_h.setForeground(QColor(22, 163, 74) if h > 0 else QColor(220, 38, 38))

        # NFC Reader Status
        nfc_stat = "READY" if nfc_online else "ERROR"
        item_nfc_v = self.diag_table.item(10, 1)
        item_nfc_v.setText("SPI 50kHz")
        item_nfc_v.setFont(font_val)

        item_nfc_s = self.diag_table.item(10, 2)
        item_nfc_s.setText(nfc_stat)
        item_nfc_s.setFont(font_val)
        item_nfc_s.setForeground(QColor(22, 163, 74) if nfc_online else QColor(220, 38, 38))
