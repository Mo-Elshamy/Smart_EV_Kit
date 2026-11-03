import time
import threading
import random
from config import (
    PIN_TRIG, PINS_ECHO, DIST_MIN_VALID_CM, DIST_MAX_VALID_CM, SENSOR_TIMEOUT_SEC
)

try:
    import RPi.GPIO as GPIO
    from gpiozero import DigitalInputDevice
    import board
    import adafruit_dht
    IS_HARDWARE = True
except ImportError:
    IS_HARDWARE = False


class SensorArray:
    """Manages the 8x HC-SR04 Ultrasonic Sensors and the DHT11 Sensor."""

    def __init__(self):
        self.distances = [0.0] * len(PINS_ECHO)
        self.temp_data = {"t": 24.0, "h": 50.0}
        self.last_echo_times = [0.0] * len(PINS_ECHO)
        self._echo_start_times = [0.0] * len(PINS_ECHO)
        self.echo_devices = []
        self.running = True
        self._lock = threading.Lock()

        if IS_HARDWARE:
            self._init_hardware()
        else:
            self._init_mock()

    def _init_hardware(self):
        try:
            # 1. Ultrasonic Trigger Setup
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PIN_TRIG, GPIO.OUT, initial=GPIO.LOW)

            # 2. Ultrasonic Echo Setup via gpiozero callbacks
            for idx, pin in enumerate(PINS_ECHO):
                device = DigitalInputDevice(pin, pull_up=False)
                device.when_activated = lambda i=idx: self._on_echo_rise(i)
                device.when_deactivated = lambda i=idx: self._on_echo_fall(i)
                self.echo_devices.append(device)
        except Exception as e:
            print(f"Warning: Failed to claim ultrasonic GPIO pins ({e}). Falling back to simulation.")
            self._init_mock()

        # 3. DHT11 Setup
        try:
            self.dht_device = adafruit_dht.DHT11(board.D4, use_pulseio=False)
        except Exception as e:
            print(f"Warning: Failed to initialize DHT11: {e}")
            self.dht_device = None

        # Start background DHT thread
        threading.Thread(target=self._dht_loop, daemon=True).start()

    def _on_echo_rise(self, idx):
        self._echo_start_times[idx] = time.time()

    def _on_echo_fall(self, idx):
        start = self._echo_start_times[idx]
        if start > 0:
            duration = time.time() - start
            dist = (duration * 34300.0) / 2.0  # cm

            # Valid range handling
            with self._lock:
                if dist < DIST_MIN_VALID_CM:
                    # Very close obstacle (< 2cm) - clamp to minimum critical distance
                    self.distances[idx] = DIST_MIN_VALID_CM
                    self.last_echo_times[idx] = time.time()
                elif dist <= DIST_MAX_VALID_CM:
                    self.distances[idx] = round(dist, 1)
                    self.last_echo_times[idx] = time.time()
                else:
                    # Exceeds max range: no obstacle detected
                    self.distances[idx] = 0.0
                    self.last_echo_times[idx] = time.time()

    def trigger(self):
        """Send a 10µs pulse to the shared trigger pin to fire all sensors."""
        if IS_HARDWARE:
            now = time.time()
            with self._lock:
                # Decay stale readings (no echo received within timeout)
                for i in range(len(self.distances)):
                    if self.distances[i] > 0 and (now - self.last_echo_times[i] > SENSOR_TIMEOUT_SEC):
                        self.distances[i] = 0.0

            GPIO.output(PIN_TRIG, True)
            time.sleep(0.00001)  # 10µs pulse
            GPIO.output(PIN_TRIG, False)
        else:
            with self._lock:
                for i in range(len(self.distances)):
                    # Smooth mock sensor values
                    curr = self.distances[i] if self.distances[i] > 0 else 120.0
                    self.distances[i] = max(0.0, min(300.0, round(curr + random.uniform(-3.0, 3.0), 1)))

    def get_distances(self):
        with self._lock:
            return list(self.distances)

    def get_temp_data(self):
        with self._lock:
            return dict(self.temp_data)

    def _dht_loop(self):
        while self.running and self.dht_device:
            try:
                t = self.dht_device.temperature
                h = self.dht_device.humidity
                with self._lock:
                    if t is not None:
                        self.temp_data["t"] = float(t)
                    if h is not None:
                        self.temp_data["h"] = float(h)
            except RuntimeError:
                pass  # DHT sensors occasionally fail reads, retry on next cycle
            except Exception as e:
                print(f"DHT loop error: {e}")
            time.sleep(2.0)

    def _init_mock(self):
        self.distances = [120.0] * len(PINS_ECHO)
        self.temp_data = {"t": 24.5, "h": 52.0}

    def cleanup(self):
        self.running = False
        if IS_HARDWARE and hasattr(self, 'dht_device') and self.dht_device:
            try:
                self.dht_device.exit()
            except Exception:
                pass

