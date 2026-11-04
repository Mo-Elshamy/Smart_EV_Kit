import sys
from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from PyQt5.QtCore import QTimer, Qt, QDateTime

from config import SYSTEM_TICK_MS
from storage import StorageManager
from hal.controller import CarHardware
from ui.screens.lock_screen import LockScreenPage, PinScreenPage, ConfirmLockPage
from ui.screens.dashboard_screen import DashboardPage
from ui.screens.settings_screen import SettingsHubPage
from ui.screens.jetson_screen import JetsonExplorerPage


class EVSystem(QMainWindow):
    """Main Vehicle Control Unit application window for the Smart EV Kit."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EV Control System")
        # Kiosk mode: Fullscreen + Frameless
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 1. Initialize Storage & Hardware Link
        self.storage = StorageManager()
        self.car = CarHardware()

        self.is_locked = True
        self.add_key_mode = False

        # 2. Setup Screen Navigation Stack
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # Callbacks map for screens
        dash_callbacks = {
            'toggle_main_lights': self.toggle_main_lights,
            'toggle_reverse': self.toggle_reverse,
            'toggle_interior_lights': self.toggle_interior_lights,
            'prompt_lock': lambda: self.central_widget.setCurrentWidget(self.page_confirm),
            'open_settings': lambda: self.central_widget.setCurrentWidget(self.page_config),
            'open_jetson': self.open_jetson_screen,
            'set_turn_signal': self.set_turn_signal
        }

        settings_callbacks = {
            'return_to_dash': lambda: self.central_widget.setCurrentWidget(self.page_dashboard),
            'start_add_key_mode': self._start_add_key,
            'cancel_add_key_mode': self._cancel_add_key,
            'set_interior_rgb': self.car.lights.set_interior_rgb,
            'set_interior_mode': self.car.lights.set_interior_mode
        }

        self.page_locked = LockScreenPage(
            on_enter_pin=lambda: self.central_widget.setCurrentWidget(self.page_password)
        )
        self.page_password = PinScreenPage(
            on_pin_success=self.unlock_system,
            on_cancel=lambda: self.central_widget.setCurrentWidget(self.page_locked),
            get_valid_pin_fn=lambda: self.storage.pin
        )
        self.page_dashboard = DashboardPage(callbacks=dash_callbacks)
        self.page_config = SettingsHubPage(callbacks=settings_callbacks, storage=self.storage)
        self.page_confirm = ConfirmLockPage(
            on_confirm_lock=self.lock_system,
            on_cancel=lambda: self.central_widget.setCurrentWidget(self.page_dashboard)
        )
        self.page_jetson = JetsonExplorerPage(
            on_back=lambda: self.central_widget.setCurrentWidget(self.page_dashboard),
            get_status_fn=self.car.jetson.get_status
        )

        self.central_widget.addWidget(self.page_locked)      # 0
        self.central_widget.addWidget(self.page_password)    # 1
        self.central_widget.addWidget(self.page_dashboard)   # 2
        self.central_widget.addWidget(self.page_config)      # 3
        self.central_widget.addWidget(self.page_confirm)     # 4
        self.central_widget.addWidget(self.page_jetson)      # 5

        self.central_widget.setCurrentWidget(self.page_locked)

        # 3. Heartbeat Timer (50ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system)
        self.timer.start(SYSTEM_TICK_MS)

        # Apply saved lighting preferences
        r, g, b = self.storage.interior_rgb
        self.car.lights.set_interior_rgb(r, g, b)
        self.car.lights.set_interior_mode(self.storage.interior_mode)

        self.showFullScreen()

    # ==========================================
    #   SYSTEM HEARTBEAT LOOP (50ms)
    # ==========================================
    def update_system(self):
        now = QDateTime.currentDateTime()
        clock_str = now.toString("hh:mm")
        if self.page_dashboard.lbl_clock.text() != clock_str:
            self.page_dashboard.lbl_clock.setText(clock_str)

        date_str = now.toString("ddd, MMM d").upper()
        if self.page_dashboard.lbl_date.text() != date_str:
            self.page_dashboard.lbl_date.setText(date_str)

        # If currently on the diagnostics tab, refresh diagnostics table (~4Hz)
        self._diag_tick = getattr(self, "_diag_tick", 0) + 1
        if self.central_widget.currentWidget() == self.page_config:
            if self.page_config.content_stack.currentIndex() == 2 and (self._diag_tick % 5 == 0):
                self.page_config.update_diagnostics_data(
                    self.car.distances, self.car.temp_data, self.car.nfc_reader
                )

        # Update Jetson status telemetry on dashboard & page (~1Hz)
        if self._diag_tick % 20 == 0:
            self.page_dashboard.update_jetson_status(self.car.jetson.get_status())
            if self.central_widget.currentWidget() == self.page_jetson:
                self.page_jetson.refresh_status()

        # Process Scanned NFC Card
        scanned_id = self.car.nfc_id
        if scanned_id:
            if self.add_key_mode:
                if self.storage.add_authorized_key(scanned_id):
                    self.page_config.refresh_key_list()
                    self.page_config.lbl_access_status.setText(f"SUCCESS! Added {scanned_id}")
                    self.page_config.lbl_access_status.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.page_config.lbl_access_status.setText("Card is already authorized!")
                    self.page_config.lbl_access_status.setStyleSheet("color: orange;")
                self.add_key_mode = False

            elif self.is_locked:
                if self.storage.is_key_authorized(scanned_id):
                    self.unlock_system(f"UID: {scanned_id}")
                else:
                    print(f"Access Denied for card: {scanned_id}")

            self.car.nfc_id = None

        if self.is_locked:
            return

        # Active Driving Mode Updates
        self.car.trigger_sensors()
        distances = self.car.distances
        self.page_dashboard.parking_viz.update_sensor_data(distances)

        # Proximity audio alert (Non-blocking progressive rate)
        active_distances = [d for d in distances if d > 0]
        min_dist = min(active_distances, default=999.0)
        self.car.update_radar_beep(min_dist)

        # Update environment telemetry
        t = self.car.temp_data.get("t", 0.0)
        h = self.car.temp_data.get("h", 0.0)
        temp_str = f"{t:.0f}°C  {h:.0f}%"
        if self.page_dashboard.lbl_temp.text() != temp_str:
            self.page_dashboard.lbl_temp.setText(temp_str)

    # ==========================================
    #   SECURITY & VEHICLE STATE MANAGEMENT
    # ==========================================
    def unlock_system(self, user_label="Authorized"):
        self.is_locked = False
        self.central_widget.setCurrentWidget(self.page_dashboard)
        self.page_dashboard.update_jetson_status(self.car.jetson.get_status())

        # Energize Motor Relay 0 (Active Low -> LOW=ON)
        self.car.set_relay(0, True)

        # Welcome cyan flash then return to saved interior settings
        self.car.lights.set_all_zones(False)
        self.car.lights.set_zone("interior", True)
        self.car.lights.set_interior_rgb(0, 255, 255)
        saved_rgb = self.storage.interior_rgb
        QTimer.singleShot(800, lambda: self.car.lights.set_interior_rgb(*saved_rgb))

    def open_jetson_screen(self):
        self.page_jetson.open_dashboard()
        self.central_widget.setCurrentWidget(self.page_jetson)

    def lock_system(self):
        self.is_locked = True
        self.central_widget.setCurrentWidget(self.page_locked)

        # Safely isolate motor and reverse relays
        self.car.set_relay(0, False)
        self.car.set_relay(1, False)

        # Turn off all lighting zones and sound
        self.car.lights.set_all_zones(False)
        self.car.lights.set_turn_signal("OFF")
        self.car.update_radar_beep(999.0)

        # Reset dashboard button states
        self.page_dashboard.reset_controls()

    # ==========================================
    #   VEHICLE CONTROLS
    # ==========================================
    def toggle_main_lights(self, state: bool):
        self.car.set_light("Front", state)
        self.car.set_light("Back", state)

    def toggle_interior_lights(self, state: bool):
        self.car.set_light("Interior", state)

    def toggle_reverse(self, state: bool):
        self.car.set_relay(1, state)

    def set_turn_signal(self, mode: str):
        self.car.lights.set_turn_signal(mode)

    def _start_add_key(self):
        self.add_key_mode = True

    def _cancel_add_key(self):
        self.add_key_mode = False

    def closeEvent(self, event):
        self.car.cleanup()
        event.accept()

