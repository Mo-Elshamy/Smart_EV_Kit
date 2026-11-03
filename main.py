import sys
import os
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
                             QStackedWidget, QSlider, QMessageBox, QListWidget, QHeaderView, 
                             QTableWidget, QTableWidgetItem, QInputDialog, QLineEdit, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, QDateTime, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush, QPolygon, QPainterPath, QLinearGradient

# Import our verified Hardware Class
from hardware import CarHardware

# --- GLOBAL PATH CONFIGURATION ---
# This ensures files are found even when running on boot
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, "authorized_keys.txt")

# --- THEME CONFIGURATION (LIGHT MODE) ---
THEME = {
    "bg_dark": "#ffffff",        # White Background
    "bg_panel": "rgba(240, 240, 240, 220)", # Semi-transparent white panels
    "accent_cyan": "#0088cc",    # Darker Cyan for white background contrast
    "accent_red": "#dd3333",
    "accent_green": "#00aa44",
    "accent_amber": "#ffaa00",
    "text_main": "#111111",      # Dark Text
    "text_dim": "#555555",
    "menu_bg": "#e0e0e0",
    "menu_sel": "#cccccc"
}

class ParkingVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.distances = [0.0] * 8
        self.setMinimumSize(300, 400) 
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def update_sensor_data(self, distances):
        self.distances = distances
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # --- 1. DRAW RADAR GRID BACKGROUND ---
        self.draw_grid(painter, w, h)

        # --- 2. SCALING LOGIC ---
        # Adjusted for 7-inch screen proportions
        scene_w = 320
        scene_h = 520
        scale = min(w / scene_w, h / scene_h) * 0.95 # Maximize fill
        
        painter.translate(w / 2, h / 2)
        painter.scale(scale, scale)
        
        cx = 0
        cy = 0
        
        # --- 3. OFF-ROAD BUGGY DIMENSIONS ---
        body_w = 120  
        body_h = 250 
        
        # Suspension
        painter.setPen(QPen(QColor(160, 160, 160), 10)) 
        painter.drawLine(cx - 25, cy - 70, cx - 100, cy - 95) 
        painter.drawLine(cx + 25, cy - 70, cx + 100, cy - 95) 
        painter.drawLine(cx - 25, cy + 70, cx - 100, cy + 90) 
        painter.drawLine(cx + 25, cy + 70, cx + 100, cy + 90) 

        # Tires (Detailed Tread)
        painter.setBrush(QBrush(QColor(20, 20, 20))) 
        painter.setPen(QPen(QColor(5, 5, 5), 2))
        wheel_w = 48 
        wheel_h = 85 
        
        self.draw_tire(painter, cx - 100, cy - 95, -8, wheel_w, wheel_h) # FL
        self.draw_tire(painter, cx + 100, cy - 95, 8, wheel_w, wheel_h)  # FR
        
        # Fixed Rear Wheel Symmetry
        self.draw_tire(painter, cx - 100, cy + 80, 0, wheel_w, wheel_h)  # RL
        self.draw_tire(painter, cx + 100, cy + 80, 0, wheel_w, wheel_h)  # RR

        # Body Gradient (BLACK)
        grad = QLinearGradient(0, -body_h//2, 0, body_h//2)
        grad.setColorAt(0, QColor(60, 60, 60))    # Dark Grey
        grad.setColorAt(1, QColor(10, 10, 10))    # Black
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(0, 0, 0), 4))
        
        # Tub Shape
        poly = QPolygon()
        poly.append(QPoint(cx - 40, cy - body_h//2))      
        poly.append(QPoint(cx + 40, cy - body_h//2))      
        poly.append(QPoint(cx + body_w//2, cy - 45))      
        poly.append(QPoint(cx + body_w//2, cy + 70))      
        poly.append(QPoint(cx + 40, cy + body_h//2))      
        poly.append(QPoint(cx - 40, cy + body_h//2))      
        poly.append(QPoint(cx - body_w//2, cy + 70))      
        poly.append(QPoint(cx - body_w//2, cy - 45))      
        painter.drawPolygon(poly)

        # Roll Cage (Silver/Chrome)
        painter.setPen(QPen(QColor(200, 200, 200), 6)) 
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(cx - 45, cy - 55, 90, 125)
        painter.drawLine(cx - 45, cy - 55, cx + 45, cy + 70)
        painter.drawLine(cx + 45, cy - 55, cx - 45, cy + 70)

        # Spare Tire
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawEllipse(cx - 35, cy + body_h//2 - 50, 70, 70)
        painter.setBrush(QBrush(QColor(150, 150, 150)))
        painter.drawEllipse(cx - 12, cy + body_h//2 - 27, 24, 24)

        # Headlights
        painter.setBrush(QBrush(QColor(240, 240, 255))) # Xenon White
        painter.setPen(QPen(QColor(150, 150, 150), 2))
        painter.drawEllipse(cx - 50, cy - body_h//2 + 12, 22, 22)
        painter.drawEllipse(cx + 28, cy - body_h//2 + 12, 22, 22)

        # --- SENSORS ---
        # Front
        self.draw_radar_arc(painter, cx, cy - body_h//2, -55, self.distances[0]) 
        self.draw_radar_arc(painter, cx, cy - body_h//2, -20, self.distances[1]) 
        self.draw_radar_arc(painter, cx, cy - body_h//2,  20, self.distances[2]) 
        self.draw_radar_arc(painter, cx, cy - body_h//2,  55, self.distances[3]) 
        # Rear
        self.draw_radar_arc(painter, cx, cy + body_h//2, 235, self.distances[4]) 
        self.draw_radar_arc(painter, cx, cy + body_h//2, 200, self.distances[5]) 
        self.draw_radar_arc(painter, cx, cy + body_h//2, 160, self.distances[6]) 
        self.draw_radar_arc(painter, cx, cy + body_h//2, 125, self.distances[7]) 

    def draw_grid(self, painter, w, h):
        pen = QPen(QColor(0, 0, 0, 30)) # Stronger grid for white bg
        pen.setWidth(1)
        painter.setPen(pen)
        step = 50
        for x in range(0, w, step): painter.drawLine(x, 0, x, h)
        for y in range(0, h, step): painter.drawLine(0, y, w, y)
        painter.setPen(QPen(QColor(0, 0, 0, 20), 2))
        center = QPoint(w//2, h//2)
        painter.drawEllipse(center, 100, 100)
        painter.drawEllipse(center, 200, 200)
        painter.drawEllipse(center, 300, 300)

    def draw_tire(self, painter, x, y, angle, w, h):
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)
        painter.drawRoundedRect(-w//2, -h//2, w, h, 8, 8)
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawLine(-w//2 + 5, -h//4, w//2 - 5, -h//4)
        painter.drawLine(-w//2 + 5, 0, w//2 - 5, 0)
        painter.drawLine(-w//2 + 5, h//4, w//2 - 5, h//4)
        painter.restore()

    def draw_radar_arc(self, painter, x, y, angle_deg, distance):
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle_deg - 90)
        
        bars = 0
        color = QColor(100, 100, 100, 50) 
        
        if distance > 0:
            if distance < 30:   
                bars = 3
                color = QColor(255, 50, 50) 
            elif distance < 70: 
                bars = 2
                color = QColor(255, 180, 0) 
            elif distance < 150: 
                bars = 1
                color = QColor(0, 200, 100) 
        
        span = int(35 * 16)
        start = int(-17.5 * 16)
        
        pen = QPen(color, 6, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        d1, d2, d3 = 90, 170, 250
        
        if bars >= 1: painter.drawArc(-d1//2, -d1//2, d1, d1, start, span)
        else: 
            painter.setPen(QPen(QColor(0, 0, 0, 30), 2))
            painter.drawArc(-d1//2, -d1//2, d1, d1, start, span)

        if bars >= 2: 
            painter.setPen(pen)
            painter.drawArc(-d2//2, -d2//2, d2, d2, start, span)
        else:
            painter.setPen(QPen(QColor(0, 0, 0, 30), 2))
            painter.drawArc(-d2//2, -d2//2, d2, d2, start, span)
            
        if bars >= 3: 
            painter.setPen(pen)
            painter.drawArc(-d3//2, -d3//2, d3, d3, start, span)
        else:
            painter.setPen(QPen(QColor(0, 0, 0, 30), 2))
            painter.drawArc(-d3//2, -d3//2, d3, d3, start, span)
            
        painter.restore()

class EVSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # --- WINDOW SETUP ---
        self.setWindowTitle("EV Control System")
        # KIOSK MODE: Fullscreen + No Title Bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # --- HARDWARE ---
        print("Initializing Hardware Link...")
        self.car = CarHardware()
        
        # --- AUTH STATE ---
        self.authorized_keys = self.load_authorized_keys()
        self.add_key_mode = False
        self.pin_buffer = ""
        
        # Variables for Beep Logic
        self.beep_counter = 0 
        self.beep_interval = 0 # 0 = Off
        
        # --- UI ---
        self.central_widget = QStackedWidget() 
        self.setCentralWidget(self.central_widget)
        
        self.setup_locked_screen()
        self.setup_password_screen()
        self.setup_dashboard_screen()
        self.setup_config_screen() 
        self.setup_confirmation_screen()
        
        self.central_widget.setCurrentWidget(self.page_locked)
        self.is_locked = True

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system)
        self.timer.start(50) # 50ms tick
        
        # Show fullscreen LAST to ensure it overrides system defaults
        self.showFullScreen()

    # --- HELPER TO APPLY BACKGROUND ---
    def apply_background(self, widget):
        """Apply PNG/JPG background to a widget if available"""
        widget.setObjectName("bg_widget")
        bg_style = f"background-color: {THEME['bg_dark']};"
        
        # Use BASE_DIR to find images reliably
        png_path = os.path.join(BASE_DIR, "background.png")
        jpg_path = os.path.join(base_dir, "background.jpg") if 'base_dir' in locals() else os.path.join(BASE_DIR, "background.jpg")
        
        if os.path.exists(png_path):
            bg_style += f" border-image: url({png_path.replace(os.sep, '/')}) 0 0 0 0 stretch stretch;"
        elif os.path.exists(jpg_path):
            bg_style += f" border-image: url({jpg_path.replace(os.sep, '/')}) 0 0 0 0 stretch stretch;"
            
        widget.setStyleSheet(f"""
            QWidget#bg_widget {{ {bg_style} }}
            QLabel {{ background: transparent; color: {THEME['text_main']}; font-family: 'Segoe UI'; }}
        """)

    # --- DATA PERSISTENCE ---
    def load_authorized_keys(self):
        keys = []
        try:
            with open(KEY_FILE, "r") as f:
                keys = [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            pass
        return keys

    def save_authorized_key(self, new_id):
        with open(KEY_FILE, "a") as f:
            f.write(f"{new_id}\n")
        self.authorized_keys.append(str(new_id))

    def delete_authorized_key(self, key_to_remove):
        if key_to_remove in self.authorized_keys:
            self.authorized_keys.remove(key_to_remove)
            with open(KEY_FILE, "w") as f:
                for k in self.authorized_keys:
                    f.write(f"{k}\n")

    def setup_locked_screen(self):
        self.page_locked = QWidget()
        self.apply_background(self.page_locked)
        layout = QVBoxLayout(self.page_locked)
        
        # WELCOME MESSAGE - BLACK TEXT
        lbl_welcome = QLabel("Welcome to RQ EV Car")
        lbl_welcome.setAlignment(Qt.AlignCenter)
        lbl_welcome.setFont(QFont("Segoe UI", 36, QFont.Bold))
        lbl_welcome.setStyleSheet("color: black; margin-top: 40px;")
        layout.addWidget(lbl_welcome)
        
        layout.addStretch()

        # Bottom Row for PIN (Left) and Scan (Right)
        bot_row = QHBoxLayout()
        
        # Left: PIN Button
        btn_pass = QPushButton("ENTER PIN")
        btn_pass.setFixedSize(160, 60)
        btn_pass.setFont(QFont("Segoe UI", 14, QFont.Bold))
        btn_pass.setStyleSheet(f"""
            QPushButton {{ background-color: {THEME['bg_panel']}; color: {THEME['text_main']}; border: 2px solid #aaa; border-radius: 10px; }}
            QPushButton:pressed {{ background-color: #ddd; color: black; }}
        """)
        btn_pass.clicked.connect(lambda: self.central_widget.setCurrentWidget(self.page_password))
        
        # Right: Scan Card Label
        lbl_scan = QLabel("SCAN CARD ⬇️")
        lbl_scan.setAlignment(Qt.AlignCenter)
        lbl_scan.setFont(QFont("Segoe UI", 18, QFont.Bold))
        lbl_scan.setStyleSheet("color: black; font-weight: bold; background: rgba(255, 255, 255, 0.7); border-radius: 10px; padding: 10px;")

        bot_row.addSpacing(20)
        bot_row.addWidget(btn_pass)
        bot_row.addStretch()
        bot_row.addWidget(lbl_scan)
        bot_row.addSpacing(20)
        
        layout.addLayout(bot_row)
        layout.addSpacing(30)
        
        self.central_widget.addWidget(self.page_locked)

    def setup_password_screen(self):
        self.page_password = QWidget()
        self.apply_background(self.page_password)
        layout = QVBoxLayout(self.page_password)
        
        self.lbl_pin_display = QLabel("Enter PIN")
        self.lbl_pin_display.setAlignment(Qt.AlignCenter)
        self.lbl_pin_display.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.lbl_pin_display.setStyleSheet(f"color: {THEME['text_main']}; margin: 20px;")
        layout.addWidget(self.lbl_pin_display)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('BACK', 3, 0), ('0', 3, 1), ('OK', 3, 2)
        ]
        
        for text, r, c in keys:
            btn = QPushButton(text)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure buttons expand
            btn.setFont(QFont("Segoe UI", 36, QFont.Bold)) # ENLARGED FONT SIZE
            if text == 'OK':
                btn.setStyleSheet(f"background-color: {THEME['accent_green']}; color: white; border-radius: 10px;")
                btn.clicked.connect(self.check_pin)
            elif text == 'BACK':
                btn.setStyleSheet(f"background-color: {THEME['accent_red']}; color: white; border-radius: 10px;")
                btn.clicked.connect(self.back_to_lock)
            else:
                btn.setStyleSheet(f"background-color: {THEME['bg_panel']}; color: {THEME['text_main']}; border-radius: 10px; border: 1px solid #ccc;")
                btn.clicked.connect(lambda _, t=text: self.add_pin_digit(t))
            grid.addWidget(btn, r, c)
            
        layout.addLayout(grid)
        self.central_widget.addWidget(self.page_password)

    def setup_confirmation_screen(self):
        self.page_confirm = QWidget()
        self.apply_background(self.page_confirm)
        layout = QVBoxLayout(self.page_confirm)
        
        # lbl_q = QLabel("LOCK VEHICLE?")
        # lbl_q.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        # lbl_q.setFont(QFont("Segoe UI", 30, QFont.Bold))
        # lbl_q.setStyleSheet(f"color: {THEME['text_main']};")
        # layout.addStretch()
        # layout.addWidget(lbl_q)
        layout.addStretch()
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        
        btn_yes = QPushButton("YES, LOCK")
        btn_yes.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_yes.setFixedHeight(120)
        btn_yes.setFont(QFont("Segoe UI", 18, QFont.Bold))
        btn_yes.setStyleSheet(f"background-color: {THEME['accent_red']}; color: white; border-radius: 15px;")
        btn_yes.clicked.connect(self.lock_system)
        
        btn_no = QPushButton("CANCEL")
        btn_no.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_no.setFixedHeight(120)
        btn_no.setFont(QFont("Segoe UI", 18, QFont.Bold))
        btn_no.setStyleSheet(f"background-color: {THEME['bg_panel']}; color: {THEME['text_main']}; border-radius: 15px; border: 1px solid #ccc;")
        btn_no.clicked.connect(lambda: self.central_widget.setCurrentWidget(self.page_dashboard))
        
        btn_row.addWidget(btn_no)
        btn_row.addWidget(btn_yes)
        layout.addLayout(btn_row)
        layout.addSpacing(40)
        
        self.central_widget.addWidget(self.page_confirm)

    def setup_dashboard_screen(self):
        self.page_dashboard = QWidget()
        self.apply_background(self.page_dashboard)
        
        root_layout = QVBoxLayout(self.page_dashboard)
        # Reduced spacing/margins to maximize space
        root_layout.setContentsMargins(5, 5, 5, 5)
        root_layout.setSpacing(5)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        self.parking_viz = ParkingVisualizer()
        viz_container = QFrame()
        viz_container.setStyleSheet(f"background-color: {THEME['bg_panel']}; border: 1px solid #ccc; border-radius: 15px;")
        viz_layout = QVBoxLayout(viz_container)
        viz_layout.addWidget(self.parking_viz)
        
        top_row.addWidget(viz_container, 60)

        controls_frame = QFrame()
        controls_frame.setStyleSheet(f"background-color: {THEME['bg_panel']}; border-radius: 15px; border: 1px solid #ccc;")
        right_layout = QVBoxLayout(controls_frame)
        right_layout.setContentsMargins(10, 15, 10, 15) # Reduced margins
        right_layout.setSpacing(10) # Reduced spacing between items
        
        # Info Block - EXPANDING
        self.lbl_clock = QLabel("--:--")
        self.lbl_clock.setAlignment(Qt.AlignCenter)
        self.lbl_clock.setFont(QFont("Segoe UI", 40, QFont.Bold)) # Larger Font
        self.lbl_clock.setStyleSheet(f"color: {THEME['text_main']};")
        self.lbl_clock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Expanding vertically
        
        self.lbl_date = QLabel("--/--")
        self.lbl_date.setAlignment(Qt.AlignCenter)
        self.lbl_date.setFont(QFont("Segoe UI", 16)) # Larger Font
        self.lbl_date.setStyleSheet(f"color: {THEME['accent_cyan']}; letter-spacing: 2px;")
        self.lbl_date.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Expanding vertically
        
        right_layout.addWidget(self.lbl_clock)
        right_layout.addWidget(self.lbl_date)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #ccc;")
        right_layout.addWidget(line)

        self.lbl_temp = QLabel("24°C")
        self.lbl_temp.setAlignment(Qt.AlignCenter)
        self.lbl_temp.setFont(QFont("Segoe UI", 26)) # Larger Font
        self.lbl_temp.setStyleSheet(f"color: {THEME['text_main']};")
        self.lbl_temp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Expanding vertically
        right_layout.addWidget(self.lbl_temp)
        
        self.lbl_user = QLabel("Welcome User")
        self.lbl_user.setAlignment(Qt.AlignCenter)
        self.lbl_user.setFont(QFont("Arial", 16)) # Larger Font
        self.lbl_user.setStyleSheet(f"color: {THEME['accent_green']}; margin-top: 5px;")
        self.lbl_user.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Expanding vertically
        right_layout.addWidget(self.lbl_user)
        
        # Filler to push buttons to bottom, but use less of it
        right_layout.addStretch(1)

        button_grid = QGridLayout()
        button_grid.setSpacing(10)
        # LIGHTS BUTTON - BIG
        self.btn_lights = self.create_icon_button("💡", lambda: self.toggle_main_lights(self.btn_lights))
        self.btn_lights.setFont(QFont("Segoe UI", 48)) 
        self.btn_lights.setMinimumHeight(120) # Balanced Height
        
        # REVERSE BUTTON - BIG
        self.btn_reverse = self.create_icon_button("R", self.toggle_reverse, is_reverse=True) 
        self.btn_reverse.setFont(QFont("Segoe UI", 48)) 
        self.btn_reverse.setMinimumHeight(120)

        # LOCK BUTTON - BIG
        btn_lock = self.create_icon_button("🔒", self.lock_system_confirm, is_red=True)
        btn_lock.setFont(QFont("Segoe UI", 48)) 
        btn_lock.setMinimumHeight(120)

        button_grid.addWidget(self.btn_lights, 0, 0)
        button_grid.addWidget(self.btn_reverse, 0, 1)
        button_grid.addWidget(btn_lock, 1, 0, 1, 2) # Span 2 columns
        
        right_layout.addLayout(button_grid)

        config_row = QHBoxLayout()
        self.btn_body = self.create_button("UNDERGLOW", lambda: self.toggle_light("Body", self.btn_body))
        self.btn_body.setMinimumHeight(100) # Increased Height
        self.btn_body.setFont(QFont("Segoe UI", 22, QFont.Bold)) # Increased Font Size
        self.btn_body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        btn_cfg = QPushButton("⚙")
        btn_cfg.setFixedSize(100, 100) # Increased Size
        btn_cfg.setStyleSheet(f"""
            QPushButton {{ background-color: #ddd; color: #333; border-radius: 8px; font-size: 40px; border: 1px solid #ccc; }}
            QPushButton:pressed {{ background-color: #bbb; }}
        """)
        btn_cfg.clicked.connect(lambda: self.central_widget.setCurrentWidget(self.page_config))
        
        config_row.addWidget(self.btn_body)
        config_row.addWidget(btn_cfg)
        right_layout.addLayout(config_row)

        top_row.addWidget(controls_frame, 40)
        root_layout.addLayout(top_row)

        # --- BOTTOM ROW: TURN SIGNALS (TALLER) ---
        bot_row = QHBoxLayout()
        bot_row.setSpacing(10)
        
        self.btn_left = self.create_turn_button("⬅", lambda: self.toggle_turn("LEFT", self.btn_left))
        self.btn_haz  = self.create_turn_button("⚠", lambda: self.toggle_turn("HAZARD", self.btn_haz), is_hazard=True)
        self.btn_right= self.create_turn_button("➡", lambda: self.toggle_turn("RIGHT", self.btn_right))
        
        bot_row.addWidget(self.btn_left)
        bot_row.addWidget(self.btn_haz)
        bot_row.addWidget(self.btn_right)
        
        root_layout.addLayout(bot_row)
        self.central_widget.addWidget(self.page_dashboard)

    def setup_config_screen(self):
        """New Unified Config Hub"""
        self.page_config = QWidget()
        self.page_config.setStyleSheet(f"background-color: {THEME['bg_dark']}; color: {THEME['text_main']};")
        layout = QHBoxLayout(self.page_config)
        
        # --- LEFT MENU (List of Options) ---
        menu_frame = QFrame()
        menu_frame.setFixedWidth(250) # INCREASED WIDTH
        menu_frame.setStyleSheet(f"background-color: {THEME['menu_bg']}; border-right: 1px solid #ccc;")
        menu_layout = QVBoxLayout(menu_frame)
        
        lbl_settings = QLabel("SETTINGS")
        lbl_settings.setFont(QFont("Segoe UI", 20, QFont.Bold)) # Increased Font
        lbl_settings.setStyleSheet(f"color: {THEME['text_dim']}; margin-bottom: 20px;")
        menu_layout.addWidget(lbl_settings)
        
        self.menu_list = QListWidget()
        self.menu_list.setFont(QFont("Segoe UI", 18, QFont.Bold)) # Increased Font
        self.menu_list.addItem("Light Config")
        self.menu_list.addItem("Access Config")
        self.menu_list.addItem("Diagnostics")
        self.menu_list.setCurrentRow(0)
        self.menu_list.currentRowChanged.connect(self.change_config_page)
        
        self.menu_list.setStyleSheet(f"""
            QListWidget {{ border: none; background: transparent; outline: none; }}
            QListWidget::item {{ padding: 20px; color: {THEME['text_main']}; border-radius: 5px; }}
            QListWidget::item:selected {{ background-color: {THEME['menu_sel']}; color: black; border-left: 6px solid {THEME['accent_cyan']}; }}
        """)
        
        menu_layout.addWidget(self.menu_list)
        
        btn_exit = QPushButton("BACK TO DASH")
        btn_exit.setStyleSheet(f"background-color: #ddd; color: #333; padding: 20px; border-radius: 5px; margin-top: 20px; font-weight: bold; font-size: 16px;")
        btn_exit.clicked.connect(lambda: self.central_widget.setCurrentWidget(self.page_dashboard))
        menu_layout.addWidget(btn_exit)
        
        # --- RIGHT CONTENT (Stacked Pages) ---
        self.config_stack = QStackedWidget()
        
        self.config_light = QWidget()
        self.setup_light_config_ui(self.config_light)
        
        self.config_access = QWidget()
        self.setup_access_config_ui(self.config_access)

        self.config_diag = QWidget()
        self.setup_diagnostics_ui(self.config_diag)
        
        self.config_stack.addWidget(self.config_light)
        self.config_stack.addWidget(self.config_access)
        self.config_stack.addWidget(self.config_diag)
        
        layout.addWidget(menu_frame)
        layout.addWidget(self.config_stack)
        
        self.central_widget.addWidget(self.page_config)

    def change_config_page(self, index):
        self.config_stack.setCurrentIndex(index)
        if index != 1:
            self.add_key_mode = False
            self.lbl_access_status.setText("Status: Ready")
            self.lbl_access_status.setStyleSheet("color: #888;")

    def setup_light_config_ui(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        header = QLabel("INTERIOR LIGHTING")
        header.setFont(QFont("Segoe UI", 28, QFont.Bold)) # Increased font
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"color: {THEME['accent_cyan']};")
        layout.addWidget(header)
        
        # Preview - Make it expanding
        self.color_preview = QLabel("PREVIEW")
        self.color_preview.setAlignment(Qt.AlignCenter)
        self.color_preview.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.color_preview.setMinimumHeight(120)
        self.color_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.color_preview.setStyleSheet("background-color: blue; border: 4px solid #333; border-radius: 15px;")
        layout.addWidget(self.color_preview, 2) # Give it 2x weight
        
        # Sliders Container
        slider_container = QWidget()
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setSpacing(15)
        slider_layout.setContentsMargins(0, 10, 0, 10)
        
        self.sliders = []
        labels = ["R", "G", "B"]
        colors = ["#ff5555", "#55ff55", "#5555ff"]
        
        for i in range(3):
            row = QHBoxLayout()
            lbl = QLabel(labels[i])
            lbl.setFont(QFont("Arial", 24, QFont.Bold)) # Larger label
            lbl.setFixedWidth(60)
            lbl.setStyleSheet(f"color: {colors[i]};")
            row.addWidget(lbl)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(0 if i != 2 else 255)
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            # Thicker slider track and handle
            slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{ height: 16px; background: #444; border-radius: 8px; }}
                QSlider::handle:horizontal {{ background: {colors[i]}; width: 32px; height: 32px; margin: -8px 0; border-radius: 16px; border: 3px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5); }}
                QSlider::sub-page:horizontal {{ background: {colors[i]}; border-radius: 8px; }}
            """)
            slider.valueChanged.connect(self.update_interior_color)
            self.sliders.append(slider)
            row.addWidget(slider)
            slider_layout.addLayout(row)
            
        layout.addWidget(slider_container, 3) # Give it 3x weight
            
        # Presets Grid - Make buttons expanding
        grid = QGridLayout()
        grid.setSpacing(15)
        presets = [("ICE", 0,255,255), ("RED", 255,0,0), ("GRN", 0,255,0), ("BLU", 0,0,255)]
        for idx, (name, r, g, b) in enumerate(presets):
            btn = QPushButton(name)
            btn.setFont(QFont("Segoe UI", 16, QFont.Bold)) # Larger font
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumHeight(70)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: rgb({r},{g},{b}); color: {'black' if (r+g+b)>300 else 'white'}; border-radius: 10px; border: 2px solid #999; }}
                QPushButton:pressed {{ border: 2px solid white; }}
            """)
            btn.clicked.connect(lambda _, r=r, g=g, b=b: self.set_sliders(r, g, b))
            grid.addWidget(btn, 0, idx)
        layout.addLayout(grid, 2) # Give it 2x weight
        
        # Patterns Row - Make buttons expanding
        p_layout = QHBoxLayout()
        p_layout.setSpacing(15)
        patterns = [("SOLID", "SOLID"), ("PULSE", "BREATHE"), ("RGB", "RAINBOW")]
        for name, mode in patterns:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumHeight(80)
            btn.setFont(QFont("Segoe UI", 16, QFont.Bold)) # Larger font
            
            if mode=="SOLID": btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: #ddd; color: #333; border-radius: 10px; border: 2px solid #ccc; }}
                QPushButton:checked {{ background-color: {THEME['accent_cyan']}; color: white; border: 2px solid #005577; }}
                QPushButton:pressed {{ background-color: #bbb; }}
            """)
            btn.clicked.connect(lambda _, m=mode: self.set_pattern(m))
            p_layout.addWidget(btn)
        layout.addLayout(p_layout, 2) # Give it 2x weight

    def setup_access_config_ui(self, parent):
        layout = QVBoxLayout(parent)
        
        header = QLabel("ACCESS CONTROL")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.setStyleSheet(f"color: {THEME['accent_green']};")
        layout.addWidget(header)
        
        self.list_keys = QListWidget()
        self.list_keys.setStyleSheet(f"background-color: #fff; color: #000; font-size: 14px; border: 1px solid #ccc;")
        self.refresh_key_list()
        layout.addWidget(self.list_keys)
        
        self.lbl_access_status = QLabel("Status: Ready")
        self.lbl_access_status.setAlignment(Qt.AlignCenter)
        self.lbl_access_status.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.lbl_access_status)
        
        btn_row = QHBoxLayout()
        
        btn_add = QPushButton("SCAN NEW KEY")
        btn_add.setStyleSheet(f"background-color: {THEME['accent_cyan']}; color: white; font-weight: bold; padding: 15px; border-radius: 5px;")
        btn_add.clicked.connect(self.start_add_key)
        
        btn_del = QPushButton("DELETE SELECTED")
        btn_del.setStyleSheet("background-color: #ddd; color: #333; font-weight: bold; padding: 15px; border-radius: 5px;")
        btn_del.clicked.connect(self.delete_selected_key)
        
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

    def setup_diagnostics_ui(self, parent):
        layout = QVBoxLayout(parent)
        
        header = QLabel("SYSTEM DIAGNOSTICS")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.setStyleSheet(f"color: {THEME['accent_amber']};")
        layout.addWidget(header)

        self.diag_table = QTableWidget()
        self.diag_table.setColumnCount(3)
        self.diag_table.setHorizontalHeaderLabels(["Sensor", "Value", "Status"])
        self.diag_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.diag_table.verticalHeader().setVisible(False)
        self.diag_table.setStyleSheet(f"""
            QTableWidget {{ background-color: #fff; color: #000; font-size: 14px; border: 1px solid #ccc; }}
            QHeaderView::section {{ background-color: #eee; padding: 5px; border: 1px solid #ccc; }}
        """)
        
        self.diag_rows = [
            "Front Left (1)", "Front Mid-L (2)", "Front Mid-R (3)", "Front Right (4)",
            "Rear Left (5)", "Rear Mid-L (6)", "Rear Mid-R (7)", "Rear Right (8)",
            "Temperature", "Humidity", "NFC System"
        ]
        self.diag_table.setRowCount(len(self.diag_rows))
        
        for i, name in enumerate(self.diag_rows):
            self.diag_table.setItem(i, 0, QTableWidgetItem(name))
            self.diag_table.setItem(i, 1, QTableWidgetItem("--"))
            self.diag_table.setItem(i, 2, QTableWidgetItem("Init"))
            
        layout.addWidget(self.diag_table)

    def update_diagnostics(self):
        for i in range(8):
            dist = self.car.distances[i]
            val = f"{dist:.1f} cm"
            status = "OK"
            color = QColor(0, 150, 0)
            
            if dist == 0.0:
                status = "NO SIGNAL"
                color = QColor(150, 0, 0)
            elif dist < 30:
                status = "CRITICAL"
                color = QColor(200, 0, 0)
            
            self.diag_table.item(i, 1).setText(val)
            self.diag_table.item(i, 2).setText(status)
            self.diag_table.item(i, 2).setForeground(color)

        t = self.car.temp_data["t"]
        h = self.car.temp_data["h"]
        self.diag_table.item(8, 1).setText(f"{t:.1f} °C")
        self.diag_table.item(9, 1).setText(f"{h:.1f} %")
        
        nfc_stat = "ACTIVE" if self.car.nfc_reader else "ERROR"
        self.diag_table.item(10, 2).setText(nfc_stat)
        self.diag_table.item(10, 2).setForeground(QColor(0, 150, 0) if nfc_stat == "ACTIVE" else QColor(200,0,0))

    def add_pin_digit(self, digit):
        if len(self.pin_buffer) < 4:
            self.pin_buffer += digit
            self.lbl_pin_display.setText("•" * len(self.pin_buffer))

    def back_to_lock(self):
        self.pin_buffer = ""
        self.lbl_pin_display.setText("Enter PIN")
        self.central_widget.setCurrentWidget(self.page_locked)

    def check_pin(self):
        if self.pin_buffer == "1234":
            self.unlock_system("MANUAL_PIN")
            self.pin_buffer = ""
            self.lbl_pin_display.setText("Enter PIN")
        else:
            self.lbl_pin_display.setText("WRONG!")
            QTimer.singleShot(1000, lambda: self.lbl_pin_display.setText("Enter PIN"))
            self.pin_buffer = ""

    def refresh_key_list(self):
        self.list_keys.clear()
        for key in self.authorized_keys:
            self.list_keys.addItem(f"Key ID: {key}")

    def start_add_key(self):
        self.add_key_mode = True
        self.lbl_access_status.setText("WAITING FOR CARD... TAP NOW")
        self.lbl_access_status.setStyleSheet(f"color: {THEME['accent_amber']}; font-weight: bold; font-size: 16px;")

    def delete_selected_key(self):
        selected_items = self.list_keys.selectedItems()
        if not selected_items: return
        
        key_text = selected_items[0].text().replace("Key ID: ", "")
        
        confirm = QMessageBox()
        confirm.setIcon(QMessageBox.Warning)
        confirm.setText(f"Delete Key {key_text}?")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setStyleSheet("background-color: #fff; color: black;")
        
        if confirm.exec_() == QMessageBox.Yes:
            self.delete_authorized_key(key_text)
            self.refresh_key_list()

    def update_interior_color(self):
        r = self.sliders[0].value()
        g = self.sliders[1].value()
        b = self.sliders[2].value()
        self.color_preview.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 3px solid #333; border-radius: 20px;")
        self.car.lights.set_interior_rgb(r, g, b)

    def set_sliders(self, r, g, b):
        self.sliders[0].setValue(r)
        self.sliders[1].setValue(g)
        self.sliders[2].setValue(b)

    def set_pattern(self, mode):
        self.car.lights.set_interior_mode(mode)
        if mode == "SOLID": self.update_interior_color()

    def unlock_via_password(self):
        self.central_widget.setCurrentWidget(self.page_password)

    def update_system(self):
        now = QDateTime.currentDateTime()
        self.lbl_clock.setText(now.toString("hh:mm"))
        self.lbl_date.setText(now.toString("ddd, MMM d").upper())

        if self.central_widget.currentWidget() == self.page_config and self.config_stack.currentWidget() == self.config_diag:
            self.update_diagnostics()

        if self.car.nfc_id:
            scanned_id = str(self.car.nfc_id)
            
            if self.add_key_mode:
                if scanned_id not in self.authorized_keys:
                    self.save_authorized_key(scanned_id)
                    self.refresh_key_list()
                    self.lbl_access_status.setText(f"SUCCESS! Added {scanned_id}")
                    self.lbl_access_status.setStyleSheet(f"color: {THEME['accent_green']};")
                else:
                    self.lbl_access_status.setText("Key already exists!")
                
                self.add_key_mode = False
                
            elif self.is_locked:
                if not self.authorized_keys or scanned_id in self.authorized_keys:
                    self.unlock_system(scanned_id)
                else:
                    print(f"Access Denied: {scanned_id}")
            
            self.car.nfc_id = None

        if self.is_locked: return

        self.car.trigger_sensors()
        self.parking_viz.update_sensor_data(self.car.distances)

        min_dist = min([d for d in self.car.distances if d > 0], default=999)
        if min_dist < 30: self.car.beep(0.05)

        t = self.car.temp_data["t"]
        h = self.car.temp_data["h"]
        self.lbl_temp.setText(f"{t:.0f}°C  {h:.0f}%")

    def unlock_system(self, user_id):
        self.is_locked = False
        self.central_widget.setCurrentWidget(self.page_dashboard)
        self.lbl_user.setText(f"ID: {user_id}")
        self.car.set_relay(0, True)
        self.car.lights.set_interior_rgb(0, 255, 255) # Cyan Flash
        QTimer.singleShot(800, lambda: self.car.lights.set_interior_rgb(0, 0, 255))

    def lock_system_confirm(self):
        # NEW: Direct switch to integrated confirmation page
        self.central_widget.setCurrentWidget(self.page_confirm)

    def lock_system(self):
        self.is_locked = True
        self.central_widget.setCurrentWidget(self.page_locked)
        self.car.set_relay(0, False)
        self.car.set_relay(1, False)
        self.btn_lights.setChecked(False)
        self.toggle_main_lights(self.btn_lights)
        self.btn_body.setChecked(False)
        self.toggle_light("Body", self.btn_body)

    def create_button(self, text, function):
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn.setCheckable(True)
        btn.setStyleSheet(f"""
            QPushButton {{ 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ddd, stop:1 #bbb); 
                color: {THEME['text_main']}; border-radius: 8px; padding: 15px; border: 1px solid #999; 
            }}
            QPushButton:checked {{ 
                background: qlineargradient(x1:0, y1:0, x2:lbl_q.setAlignment(Qt.AlignTop | Qt.AlignHCenter)0, y2:1, stop:0 {THEME['accent_cyan']}, stop:1 #008899); 
                color: white; border: 1px solid {THEME['accent_cyan']}; 
            }}
        """)
        btn.clicked.connect(function)
        return btn
        
    def create_icon_button(self, icon_text, function, is_red=False, is_reverse=False):
        btn = QPushButton(icon_text)
        btn.setFont(QFont("Segoe UI", 48)) # Increase icon font size
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure button expands
        btn.setMinimumSize(80, 80)
        btn.setCheckable(True if not is_red else False) 
        base_color = "#444"
        
        # Determine active color
        if is_red:
            active_color = THEME['accent_red']
        elif is_reverse:
            active_color = THEME['accent_amber'] # Amber/Orange for Reverse if desired, or keep standard cyan
        else:
            active_color = THEME['accent_cyan']

        btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {base_color}; color: white; 
                border-radius: 15px; border: 2px solid #666; 
            }}
            QPushButton:checked {{ 
                background-color: {active_color}; color: black; border: 2px solid white;
            }}
            QPushButton:pressed {{ background-color: #666; }}
        """)
        btn.clicked.connect(function)
        return btn
        
    def create_turn_button(self, text, function, is_hazard=False):
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 24, QFont.Bold))
        btn.setMinimumHeight(120) # Increased height
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn.setCheckable(True)
        
        color = THEME['accent_red'] if is_hazard else THEME['accent_amber']
        text_color = "#cc0000" if is_hazard else "#cc8800" 
        
        btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: rgba(255,255,255,0.6); color: {text_color}; 
                border-radius: 10px; border: 2px solid {text_color}; 
            }}
            QPushButton:checked {{ 
                background-color: {color}; color: white; 
            }}
        """)
        btn.clicked.connect(function)
        return btn

    def toggle_light(self, name, btn): self.car.set_light(name, btn.isChecked())
    def toggle_main_lights(self, btn):
        state = btn.isChecked()
        self.car.set_light("Front", state)
        self.car.set_light("Back", state)
        
    def toggle_reverse(self):
        state = self.sender().isChecked()
        self.car.set_relay(1, state) # Relay 2 is Reverse

    def toggle_turn(self, mode, btn):
        if mode == "LEFT":
            self.btn_right.setChecked(False)
            self.btn_haz.setChecked(False)
        elif mode == "RIGHT":
            self.btn_left.setChecked(False)
            self.btn_haz.setChecked(False)
        elif mode == "HAZARD":
            self.btn_left.setChecked(False)
            self.btn_right.setChecked(False)
        
        if btn.isChecked(): self.car.lights.set_turn_signal(mode)
        else: self.car.lights.set_turn_signal("OFF")

    def closeEvent(self, event):
        self.car.cleanup()
        event.accept()

if __name__ == "__main__":
    if os.environ.get("DISPLAY") is None:
        os.environ["DISPLAY"] = ":0"

    app = QApplication(sys.argv)
    window = EVSystem()
    window.show()
    sys.exit(app.exec_())