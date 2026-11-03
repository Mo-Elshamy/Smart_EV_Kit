from hal.lighting import LightingSystem
from hal.sensors import SensorArray
from hal.nfc import NFCManager
from hal.actuators import ActuatorController

try:
    import RPi.GPIO as GPIO
    IS_HARDWARE = True
except ImportError:
    IS_HARDWARE = False


class CarHardware:
    """Unified Facade for all Smart EV hardware components."""

    def __init__(self):
        self.lights = LightingSystem()
        self.sensors = SensorArray()
        self.actuators = ActuatorController()
        self.nfc = NFCManager(on_card_detected=self._on_nfc_scanned)

        self._cached_nfc_id = None

    def _on_nfc_scanned(self, card_id):
        self._cached_nfc_id = card_id
        # Provide auditory feedback on successful card read
        self.beep(0.08)

    @property
    def distances(self):
        return self.sensors.get_distances()

    @property
    def temp_data(self):
        return self.sensors.get_temp_data()

    @property
    def nfc_id(self):
        val = self._cached_nfc_id
        if val is None:
            val = self.nfc.pop_latest_id()
        return val

    @nfc_id.setter
    def nfc_id(self, val):
        self._cached_nfc_id = val

    @property
    def nfc_reader(self):
        return self.nfc.is_connected

    def trigger_sensors(self):
        self.sensors.trigger()

    def set_relay(self, index: int, state: bool):
        self.actuators.set_relay(index, state)

    def set_light(self, name: str, state: bool):
        """Enable or disable lighting zones (Front, Back/Rear, Body/Interior)."""
        self.lights.set_zone(name, state)

    def beep(self, duration=0.08):
        self.actuators.trigger_short_beep(duration)

    def set_buzzer(self, state: bool):
        self.actuators.set_buzzer_direct(state)

    def update_radar_beep(self, min_distance: float):
        self.actuators.set_radar_beep_mode(min_distance)

    def cleanup(self):
        print("Cleaning up hardware components...")
        self.actuators.cleanup()
        self.sensors.cleanup()
        self.lights.stop()
        self.nfc.cleanup()
        if IS_HARDWARE:
            try:
                GPIO.cleanup()
            except Exception:
                pass
        print("Hardware cleanup complete.")

