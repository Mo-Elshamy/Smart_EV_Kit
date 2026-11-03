import time
import threading
from config import PIN_BUZZER, PIN_RELAYS

try:
    import RPi.GPIO as GPIO
    IS_HARDWARE = True
except ImportError:
    IS_HARDWARE = False


class ActuatorController:
    """Manages Relays (Active Low) and the non-blocking Piezo Buzzer."""

    def __init__(self):
        self._buzzer_active = False
        self._buzzer_pattern = "OFF"  # "OFF", "SLOW", "MEDIUM", "FAST", "SOLID"
        self._running = True
        self._lock = threading.Lock()

        if IS_HARDWARE:
            self._init_hardware()
            threading.Thread(target=self._buzzer_loop, daemon=True).start()

    def _init_hardware(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_BUZZER, GPIO.OUT, initial=GPIO.LOW)
        # Relays are Active Low: start HIGH (OFF) for safety
        GPIO.setup(PIN_RELAYS, GPIO.OUT, initial=GPIO.HIGH)

    def set_relay(self, index: int, state: bool):
        """Set relay state (Active Low: True=LOW/ON, False=HIGH/OFF)."""
        if 0 <= index < len(PIN_RELAYS):
            if IS_HARDWARE:
                val = GPIO.LOW if state else GPIO.HIGH
                GPIO.output(PIN_RELAYS[index], val)
            else:
                print(f"[MOCK] Relay {index} -> {'ON' if state else 'OFF'}")

    def set_buzzer_direct(self, state: bool):
        """Direct immediate non-blocking state change for the buzzer."""
        if IS_HARDWARE:
            GPIO.output(PIN_BUZZER, GPIO.HIGH if state else GPIO.LOW)

    def trigger_short_beep(self, duration=0.08):
        """Trigger an asynchronous short beep (will not block UI)."""
        def _beep():
            if IS_HARDWARE:
                GPIO.output(PIN_BUZZER, GPIO.HIGH)
                time.sleep(duration)
                GPIO.output(PIN_BUZZER, GPIO.LOW)

        threading.Thread(target=_beep, daemon=True).start()

    def set_radar_beep_mode(self, min_distance_cm: float):
        """Sets progressive non-blocking radar beeping based on closest obstacle."""
        with self._lock:
            if min_distance_cm <= 0 or min_distance_cm >= 150.0:
                self._buzzer_pattern = "OFF"
            elif min_distance_cm < 20.0:
                self._buzzer_pattern = "SOLID"
            elif min_distance_cm < 40.0:
                self._buzzer_pattern = "FAST"
            elif min_distance_cm < 80.0:
                self._buzzer_pattern = "MEDIUM"
            else:
                self._buzzer_pattern = "SLOW"

    def _buzzer_loop(self):
        """Background thread executing non-blocking audio alerts."""
        while self._running:
            with self._lock:
                pattern = self._buzzer_pattern

            if pattern == "OFF":
                GPIO.output(PIN_BUZZER, GPIO.LOW)
                time.sleep(0.05)
            elif pattern == "SOLID":
                GPIO.output(PIN_BUZZER, GPIO.HIGH)
                time.sleep(0.05)
            elif pattern == "FAST":
                GPIO.output(PIN_BUZZER, GPIO.HIGH)
                time.sleep(0.04)
                GPIO.output(PIN_BUZZER, GPIO.LOW)
                time.sleep(0.06)
            elif pattern == "MEDIUM":
                GPIO.output(PIN_BUZZER, GPIO.HIGH)
                time.sleep(0.06)
                GPIO.output(PIN_BUZZER, GPIO.LOW)
                time.sleep(0.18)
            elif pattern == "SLOW":
                GPIO.output(PIN_BUZZER, GPIO.HIGH)
                time.sleep(0.08)
                GPIO.output(PIN_BUZZER, GPIO.LOW)
                time.sleep(0.35)

    def cleanup(self):
        self._running = False
        with self._lock:
            self._buzzer_pattern = "OFF"
        if IS_HARDWARE:
            GPIO.output(PIN_BUZZER, GPIO.LOW)
            # Turn off all relays
            for pin in PIN_RELAYS:
                GPIO.output(pin, GPIO.HIGH)

