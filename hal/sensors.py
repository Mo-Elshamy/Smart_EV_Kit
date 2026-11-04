import time
import threading
import random
from collections import deque
import statistics
from config import (
    PIN_TRIG, PINS_ECHO, DIST_MIN_VALID_CM, DIST_MAX_VALID_CM, DIST_CRITICAL_CM,
    SENSOR_TIMEOUT_SEC, ULTRASONIC_FILTER_WINDOW, ULTRASONIC_EMA_APPROACH,
    ULTRASONIC_EMA_RECEDE, ULTRASONIC_MIN_PING_INTERVAL, ULTRASONIC_MISS_CLEAR_COUNT
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
    """Manages the 8x HC-SR04 Ultrasonic Sensors with Median + EMA noise filtering and DHT11."""

    def __init__(self):
        self.distances = [0.0] * len(PINS_ECHO)
        self.temp_data = {"t": 24.0, "h": 50.0}
        self.last_echo_times = [0.0] * len(PINS_ECHO)
        self._echo_start_times = [0.0] * len(PINS_ECHO)

        # Digital noise filter state (window of 5 per sensor)
        self._history = [deque(maxlen=ULTRASONIC_FILTER_WINDOW) for _ in range(len(PINS_ECHO))]
        self._miss_counts = [0] * len(PINS_ECHO)
        self._critical_counts = [0] * len(PINS_ECHO)
        self._last_trigger_time = 0.0

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
            now = time.time()

            with self._lock:
                # Valid physical range check (within 60cm max range)
                if DIST_MIN_VALID_CM <= dist <= DIST_MAX_VALID_CM:
                    self._history[idx].append(dist)
                    self._miss_counts[idx] = 0
                    self.last_echo_times[idx] = now

                    # Critical obstacle fast-path (< 20cm)
                    # 2 consecutive critical samples immediately confirm close obstacle for safety
                    if dist < DIST_CRITICAL_CM:
                        self._critical_counts[idx] += 1
                        if self._critical_counts[idx] >= 2:
                            self.distances[idx] = round(dist, 1)
                            return
                    else:
                        self._critical_counts[idx] = 0

                    # 5-sample median filter: completely rejects isolated spikes and electrical glitches
                    med = statistics.median(self._history[idx])

                    # Exponential Moving Average (EMA) smoothing for rock-solid radar display
                    prev = self.distances[idx]
                    if prev <= 0.0:
                        self.distances[idx] = round(med, 1)
                    else:
                        alpha = ULTRASONIC_EMA_APPROACH if med < prev else ULTRASONIC_EMA_RECEDE
                        self.distances[idx] = round(alpha * med + (1.0 - alpha) * prev, 1)
                else:
                    # Outside 60cm range: count towards clear decay
                    self._miss_counts[idx] += 1
                    if self._miss_counts[idx] >= ULTRASONIC_MISS_CLEAR_COUNT:
                        self._history[idx].clear()
                        self._critical_counts[idx] = 0
                        self.distances[idx] = 0.0

    def trigger(self):
        """Send a 10µs pulse to the shared trigger pin (enforces min interval to prevent reverberations)."""
        if IS_HARDWARE:
            now = time.time()
            # Enforce minimum ping spacing to prevent reverberation crosstalk between cycles
            if (now - self._last_trigger_time) < ULTRASONIC_MIN_PING_INTERVAL:
                return

            with self._lock:
                # Clear stale readings only after consecutive missed echos (prevents UI flicker)
                for i in range(len(self.distances)):
                    if self.distances[i] > 0 and (now - self.last_echo_times[i] > SENSOR_TIMEOUT_SEC):
                        self._miss_counts[i] += 1
                        if self._miss_counts[i] >= ULTRASONIC_MISS_CLEAR_COUNT:
                            self._history[i].clear()
                            self._critical_counts[i] = 0
                            self.distances[i] = 0.0

            GPIO.output(PIN_TRIG, True)
            time.sleep(0.00001)  # 10µs pulse
            GPIO.output(PIN_TRIG, False)
            self._last_trigger_time = now
        else:
            with self._lock:
                for i in range(len(self.distances)):
                    # Smooth mock sensor values
                    curr = self.distances[i] if self.distances[i] > 0 else 120.0
                    self.distances[i] = max(0.0, min(300.0, round(curr + random.uniform(-1.0, 1.0), 1)))

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

