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
    """Consensus filter: rejects sudden diversions and isolated noise spikes.
    
    Requires 3 consistent readings within tolerance to confirm an obstacle.
    Promptly clears when no obstacle is detected (prevents stuck alerts).
    """

    def __init__(self, required_consensus=3, window_size=4, tolerance_cm=10.0):
        self.window = deque(maxlen=window_size)
        self.required_consensus = required_consensus
        self.tolerance_cm = tolerance_cm
        self.current_confirmed = 0.0

    def update(self, raw_cm: float) -> float:
        self.window.append(raw_cm)

        # 1. Clear immediately if recent readings are clear (0.0)
        # If >= 2 zeros in the window of 4, the path is clear.
        zeros = sum(1 for x in self.window if x == 0.0)
        if zeros >= 2:
            self.current_confirmed = 0.0
            return 0.0

        # 2. Extract non-zero readings
        non_zeros = [x for x in self.window if x > 0.0]
        if len(non_zeros) < self.required_consensus:
            # Not enough non-zero readings to form consensus -> clear immediately (do not latch)
            self.current_confirmed = 0.0
            return 0.0

        # 3. Find if there is an agreement cluster of size >= required_consensus
        # where readings agree within tolerance_cm
        found_cluster = None
        for anchor in reversed(non_zeros):
            tol = max(self.tolerance_cm, anchor * 0.15)
            cluster = [x for x in non_zeros if abs(x - anchor) <= tol]
            if len(cluster) >= self.required_consensus:
                found_cluster = cluster
                break

        if found_cluster:
            self.current_confirmed = round(statistics.median(found_cluster), 1)
        else:
            # Divergent / scattered readings -> reject as noise
            self.current_confirmed = 0.0

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

        # Start background threads for ultrasonic array and DHT11
        threading.Thread(target=self._ultrasonic_loop, daemon=True).start()
        threading.Thread(target=self._dht_loop, daemon=True).start()

    def _ultrasonic_loop(self):
        """Dedicated background loop for synchronous microsecond-accurate ultrasonic capture."""
        while self.running and IS_HARDWARE:
            try:
                # 1. Wait until all previous long-range echoes have returned LOW (prevents echo overlap)
                t_wait = time.perf_counter()
                while any(GPIO.input(p) for p in PINS_ECHO) and (time.perf_counter() - t_wait < 0.050):
                    time.sleep(0.001)

                # 2. Acoustic quiet interval (25ms) so room reverberations decay completely
                time.sleep(0.025)

                # 3. Fire clean 15µs trigger pulse on shared PIN_TRIG
                GPIO.output(PIN_TRIG, True)
                t_hi = time.perf_counter()
                while (time.perf_counter() - t_hi) < 0.000015:
                    pass
                GPIO.output(PIN_TRIG, False)

                t0 = time.perf_counter()

                # Sleep 10ms: saves CPU and completely ignores any pre-echo trigger/electrical noise
                time.sleep(0.010)

                rises = [None] * len(PINS_ECHO)
                falls = [None] * len(PINS_ECHO)

                # On this hardware, ECHO rises at ~12.2ms after TRIG falls.
                # An obstacle at 60cm has a pulse duration of 3.5ms (falling by ~15.7ms).
                # Poll continuously from t0 + 10ms to t0 + 16.5ms.
                t_limit = t0 + 0.0165
                while time.perf_counter() < t_limit:
                    tc = time.perf_counter()
                    for i, pin in enumerate(PINS_ECHO):
                        val = GPIO.input(pin)
                        if val:
                            if rises[i] is None:
                                rises[i] = tc
                            elif falls[i] is not None:
                                # Pin went HIGH again -> previous low was an electrical noise dip!
                                falls[i] = None
                        else:
                            if rises[i] is not None and falls[i] is None:
                                falls[i] = tc

                # 4. Post-window validation and consensus update:
                # If an obstacle is <= 60cm, its echo pulse MUST be finished and LOW by t_limit.
                # If the pin is STILL HIGH at t_limit, the sound wave is traveling out in open space
                # (> 60cm or timeout). Any candidate fall was motor/vibration noise.
                with self._lock:
                    for i in range(len(PINS_ECHO)):
                        raw_d = 0.0
                        pin_still_high = GPIO.input(pin)

                        if rises[i] is not None and falls[i] is not None and not pin_still_high:
                            dt = falls[i] - rises[i]
                            d = (dt * 34300.0) / 2.0
                            if DIST_MIN_VALID_CM <= d <= DIST_MAX_VALID_CM:
                                raw_d = round(d, 1)

                        self.distances[i] = self._filters[i].update(raw_d)
            except Exception as e:
                print(f"Ultrasonic loop error: {e}")
                time.sleep(0.1)

    def trigger(self):
        """Non-blocking trigger hook (ultrasonic array is continuously polled in _ultrasonic_loop)."""
        if not IS_HARDWARE:
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


