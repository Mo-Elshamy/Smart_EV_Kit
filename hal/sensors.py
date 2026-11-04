import time
import threading
import random
from collections import deque
import statistics
from config import (
    PIN_TRIG, PINS_ECHO, DIST_MIN_VALID_CM, DIST_MAX_VALID_CM,
    ULTRASONIC_MIN_PING_INTERVAL
)

try:
    import RPi.GPIO as GPIO
    import board
    import adafruit_dht
    IS_HARDWARE = True
except ImportError:
    IS_HARDWARE = False


class RangeConsensusFilter:
    """Consensus filter: rejects any sudden diversion.
    
    Only updates when multiple readings (e.g. 3 of last 4) fall in the exact same range cluster.
    """

    def __init__(self, required_consensus=3, window_size=4, tolerance_cm=4.5):
        self.window = deque(maxlen=window_size)
        self.required_consensus = required_consensus
        self.tolerance_cm = tolerance_cm
        self.current_confirmed = 0.0

    def update(self, raw_cm: float) -> float:
        self.window.append(raw_cm)

        # 1. Check for 'Clear' consensus (3+ zeros in window confirm clear zone)
        zeros = sum(1 for x in self.window if x == 0.0)
        if zeros >= self.required_consensus:
            self.current_confirmed = 0.0
            return 0.0

        # 2. Extract non-zero candidate readings
        non_zeros = [x for x in self.window if x > 0.0]
        if len(non_zeros) < self.required_consensus:
            # Not enough non-zero readings yet -> ignore sudden diversion, keep current confirmed
            return self.current_confirmed

        # 3. Find if there is an agreement cluster of size >= required_consensus
        # where max(cluster) - min(cluster) <= tolerance_cm (or 10% of distance)
        found_cluster = None
        for i in range(len(non_zeros)):
            anchor = non_zeros[i]
            tol = max(self.tolerance_cm, anchor * 0.10)
            cluster = [x for x in non_zeros if abs(x - anchor) <= tol]
            if len(cluster) >= self.required_consensus:
                found_cluster = cluster
                break

        if found_cluster:
            # Multiple readings agree in the same range cluster!
            self.current_confirmed = round(statistics.median(found_cluster), 1)

        return self.current_confirmed


class SensorArray:
    """Manages the 8x HC-SR04 Ultrasonic Sensors with synchronous precision timing & Consensus Filtering."""

    def __init__(self):
        self.distances = [0.0] * len(PINS_ECHO)
        self.temp_data = {"t": 24.0, "h": 50.0}
        self._filters = [RangeConsensusFilter() for _ in range(len(PINS_ECHO))]
        self._last_trigger_time = 0.0

        self.running = True
        self._lock = threading.Lock()

        if IS_HARDWARE:
            self._init_hardware()
        else:
            self._init_mock()

    def _init_hardware(self):
        try:
            # 1. Ultrasonic GPIO Setup
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PIN_TRIG, GPIO.OUT, initial=GPIO.LOW)
            for pin in PINS_ECHO:
                GPIO.setup(pin, GPIO.IN)
        except Exception as e:
            print(f"Warning: Failed to setup ultrasonic GPIO pins ({e}). Falling back to simulation.")
            self._init_mock()

        # 2. DHT11 Setup
        try:
            self.dht_device = adafruit_dht.DHT11(board.D4, use_pulseio=False)
        except Exception as e:
            print(f"Warning: Failed to initialize DHT11: {e}")
            self.dht_device = None

        # Start background DHT thread
        threading.Thread(target=self._dht_loop, daemon=True).start()

    def trigger(self):
        """Send a 10µs pulse to the shared trigger pin and measure up to 60cm synchronously."""
        if IS_HARDWARE:
            now = time.time()
            # Enforce minimum ping spacing to prevent reverberation crosstalk between cycles
            if (now - self._last_trigger_time) < ULTRASONIC_MIN_PING_INTERVAL:
                return
            self._last_trigger_time = now

            # 1. Fire 10µs trigger pulse
            GPIO.output(PIN_TRIG, True)
            time.sleep(0.00001)
            GPIO.output(PIN_TRIG, False)

            t_start = time.perf_counter()
            # In 60cm max range, pulse duration is max 3.5ms (plus 1.0ms margin) = 4.5ms
            t_limit = t_start + 0.0045
            rises = [None] * len(PINS_ECHO)
            falls = [None] * len(PINS_ECHO)

            # High-precision synchronous pulse capture (eliminates OS thread callback skew)
            while time.perf_counter() < t_limit:
                t_cur = time.perf_counter()
                for i, pin in enumerate(PINS_ECHO):
                    if falls[i] is None:
                        val = GPIO.input(pin)
                        if val:
                            if rises[i] is None:
                                rises[i] = t_cur
                        else:
                            if rises[i] is not None:
                                falls[i] = t_cur

            # 2. Process each channel through RangeConsensusFilter
            with self._lock:
                for i in range(len(PINS_ECHO)):
                    raw_d = 0.0
                    if rises[i] is not None and falls[i] is not None:
                        dt = falls[i] - rises[i]
                        d = (dt * 34300.0) / 2.0
                        if DIST_MIN_VALID_CM <= d <= DIST_MAX_VALID_CM:
                            raw_d = round(d, 1)

                    self.distances[i] = self._filters[i].update(raw_d)
        else:
            with self._lock:
                for i in range(len(self.distances)):
                    self.distances[i] = 0.0

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
        self.distances = [0.0] * len(PINS_ECHO)
        self.temp_data = {"t": 24.5, "h": 52.0}

    def cleanup(self):
        self.running = False
        if IS_HARDWARE and hasattr(self, 'dht_device') and self.dht_device:
            try:
                self.dht_device.exit()
            except Exception:
                pass


