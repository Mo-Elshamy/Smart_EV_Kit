import time
import threading
import random
import math

# --- HARDWARE DETECTION & IMPORTS ---
try:
    import RPi.GPIO as GPIO
    from gpiozero import DigitalInputDevice 
    from mfrc522 import SimpleMFRC522, MFRC522 
    from rpi_ws281x import PixelStrip, Color
    import board
    import adafruit_dht
    IS_RASPBERRY_PI = True
except ImportError:
    print("⚠️ Hardware libraries not found. Running in MOCK (Simulation) Mode.")
    IS_RASPBERRY_PI = False
    
    # Mock classes
    class PixelStrip: 
        def __init__(self, num, *args): self.n = num
        def begin(self): pass
        def setPixelColor(self, *args): pass
        def show(self): pass
        def numPixels(self): return self.n
        def setBrightness(self, b): pass
    class Color: 
        def __init__(self, r,g,b): pass
    class DigitalInputDevice:
        def __init__(self, pin, pull_up=False): pass

# ==========================================
#   USER CONFIGURATION
# ==========================================
# LED Counts (Edit these to match your actual strips)
LEDS_FRONT_COUNT    = 6
LEDS_INTERIOR_COUNT = 24
LEDS_BACK_COUNT     = 8
LED_TOTAL = LEDS_FRONT_COUNT + LEDS_INTERIOR_COUNT + LEDS_BACK_COUNT

# GPIO Pins (BCM Mode)
PIN_LED_DATA = 12  # PWM0 (Physical Pin 32) - Check your board label!
PIN_TRIG     = 23  # Shared Ultrasonic Trigger
PIN_BUZZER   = 13  # Active Buzzer
PIN_DHT      = 4   # Temp Sensor
PIN_RELAYS   = [14, 15] # Relay 1 (Motor), Relay 2 (Aux)
PIN_NFC_RST  = 19  # <--- UPDATED: NFC Reset Pin (Physical Pin 35)

# Ultrasonic Echo Pins (4 Front, 4 Rear)
# Swapped 13->24 and 19->16 previously
PINS_ECHO = [17, 27, 22, 5, 6, 24, 16, 26] 

# ==========================================
#   SUB-SYSTEM: LIGHTING
# ==========================================
class LightingSystem:
    def __init__(self):
        self.strip = PixelStrip(LED_TOTAL, PIN_LED_DATA, 800000, 10, False, 255)
        if IS_RASPBERRY_PI:
            self.strip.begin()
        
        self.turn_signal_state = "OFF" 
        self.interior_color = (0, 0, 255)
        self.interior_mode = "SOLID"
        self.brake_active = False
        self.running = True
        self.anim_step = 0
        
        self.anim_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.anim_thread.start()

    def _animation_loop(self):
        blink_state = False
        while self.running:
            if IS_RASPBERRY_PI:
                self._render_front(blink_state)
                self._render_interior(blink_state)
                self._render_back(blink_state)
                self.strip.show()
            
            blink_state = not blink_state
            self.anim_step = (self.anim_step + 1) % 256
            time.sleep(0.1)

    def _render_front(self, blink):
        start = 0
        end = LEDS_FRONT_COUNT
        for i in range(start, end):
            if i < start + 5 and self.turn_signal_state in ["LEFT", "HAZARD"] and blink:
                self.strip.setPixelColor(i, Color(255, 150, 0))
            elif i >= end - 5 and self.turn_signal_state in ["RIGHT", "HAZARD"] and blink:
                self.strip.setPixelColor(i, Color(255, 150, 0))
            else:
                self.strip.setPixelColor(i, Color(255, 255, 255))

    def _render_interior(self, blink):
        start = LEDS_FRONT_COUNT
        end = start + LEDS_INTERIOR_COUNT
        r, g, b = self.interior_color

        if self.interior_mode == "SOLID":
            c = Color(r, g, b)
            for i in range(start, end): self.strip.setPixelColor(i, c)
        elif self.interior_mode == "BREATHE":
            factor = (math.sin(self.anim_step * 0.1) + 1) / 2
            c = Color(int(r * factor), int(g * factor), int(b * factor))
            for i in range(start, end): self.strip.setPixelColor(i, c)
        elif self.interior_mode == "RAINBOW":
            for i in range(start, end):
                pixel_hue = (i * 256 // (end-start)) + self.anim_step * 5
                c = self._wheel(pixel_hue & 255)
                self.strip.setPixelColor(i, c)

    def _render_back(self, blink):
        start = LEDS_FRONT_COUNT + LEDS_INTERIOR_COUNT
        end = LED_TOTAL
        # Use Red for rear lights (RGB: 255, 0, 0)
        base_color = Color(0, 255, 0) if self.brake_active else Color(0, 255, 0) 
        
        for i in range(start, end):
            if i < start + 5 and self.turn_signal_state in ["LEFT", "HAZARD"] and blink:
                self.strip.setPixelColor(i, Color(255, 150, 0))
            elif i >= end - 5 and self.turn_signal_state in ["RIGHT", "HAZARD"] and blink:
                self.strip.setPixelColor(i, Color(255, 150, 0))
            else:
                self.strip.setPixelColor(i, base_color)

    def _wheel(self, pos):
        if pos < 85: return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170: pos -= 85; return Color(255 - pos * 3, 0, pos * 3)
        else: pos -= 170; return Color(0, pos * 3, 255 - pos * 3)

    def set_turn_signal(self, mode): self.turn_signal_state = mode
    def set_brakes(self, is_active): self.brake_active = is_active
    def set_interior_rgb(self, r, g, b): self.interior_color = (r, g, b)
    def set_interior_mode(self, mode): self.interior_mode = mode

# ==========================================
#   MAIN HARDWARE CONTROLLER
# ==========================================
class CarHardware:
    def __init__(self):
        self.distances = [0.0] * 8
        self.nfc_id = None
        self.nfc_text = None
        self.temp_data = {"t": 0.0, "h": 0.0}
        self.running = True
        self.echo_devices = []
        
        self.lights = LightingSystem()
        
        if IS_RASPBERRY_PI:
            self._init_gpio()
            self._start_threads()
        else:
            self._init_mock()

    def _init_gpio(self):
        # 1. Output Pins (Use RPi.GPIO for outputs)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN_TRIG, GPIO.OUT)
        GPIO.setup(PIN_BUZZER, GPIO.OUT)
        # Relays Active Low: Start HIGH (OFF)
        GPIO.setup(PIN_RELAYS, GPIO.OUT, initial=GPIO.HIGH)

        # 2. Input Pins (Use gpiozero for robust reading on Bookworm)
        # We manually attach the callbacks using gpiozero's backend
        for idx, pin in enumerate(PINS_ECHO):
            # pull_up=False is critical because you have voltage dividers!
            sensor = DigitalInputDevice(pin, pull_up=False)
            
            # Using lambdas to capture the index 'i' correctly
            sensor.when_activated = lambda i=idx: self._on_echo_rise(i)
            sensor.when_deactivated = lambda i=idx: self._on_echo_fall(i)
            
            self.echo_devices.append(sensor)

        # 3. DHT11
        self.dht_device = adafruit_dht.DHT11(board.D4, use_pulseio=False)
        
        # 4. NFC
        try:
            self.nfc_core = MFRC522(pin_rst=PIN_NFC_RST)
            version = self.nfc_core.Read_MFRC522(MFRC522.VersionReg)
            
            if version in [0x91, 0x92]: 
                self.nfc_reader = SimpleMFRC522()
                self.nfc_reader.READER = self.nfc_core
                print(f"NFC Initialized (Ver: {hex(version)})")
            else:
                print(f"NFC Check Failed: {hex(version)}")
                self.nfc_reader = None
                
        except Exception as e:
            print(f"Error initializing NFC: {e}")
            self.nfc_reader = None
            
        self._echo_start_times = [0.0] * 8

    def _start_threads(self):
        threading.Thread(target=self._nfc_loop, daemon=True).start()
        threading.Thread(target=self._temp_loop, daemon=True).start()

    # --- UPDATED SENSOR LOGIC (Using gpiozero callbacks) ---
    def _on_echo_rise(self, idx):
        """Called when Echo goes HIGH"""
        self._echo_start_times[idx] = time.time()

    def _on_echo_fall(self, idx):
        """Called when Echo goes LOW"""
        if self._echo_start_times[idx] > 0:
            duration = time.time() - self._echo_start_times[idx]
            dist = (duration * 34300) / 2
            if 20 < dist < 400:
                self.distances[idx] = round(dist, 1)

    def trigger_sensors(self):
        if IS_RASPBERRY_PI:
            GPIO.output(PIN_TRIG, True)
            time.sleep(0.00001)
            GPIO.output(PIN_TRIG, False)
        else:
            for i in range(8): self.distances[i] = max(0, min(300, self.distances[i] + random.uniform(-2, 2)))

    def set_relay(self, index, state):
        if IS_RASPBERRY_PI:
            if 0 <= index < len(PIN_RELAYS):
                # Active Low: LOW=ON, HIGH=OFF
                val = GPIO.LOW if state else GPIO.HIGH
                GPIO.output(PIN_RELAYS[index], val)
        else:
            print(f"MOCK: Relay {index} -> {state}")

    def set_light(self, name, state):
        pass 

    def beep(self, duration=0.1):
        if IS_RASPBERRY_PI:
            GPIO.output(PIN_BUZZER, True)
            time.sleep(duration)
            GPIO.output(PIN_BUZZER, False)
        else: pass
    
    def set_buzzer(self, state):
        if IS_RASPBERRY_PI:
            GPIO.output(PIN_BUZZER, GPIO.HIGH if state else GPIO.LOW)
        else:
            if state: print("MOCK: Buzzer ON")

    def _nfc_loop(self):
        while self.running and self.nfc_reader:
            try:
                id, text = self.nfc_reader.read()
                self.nfc_id = id; self.nfc_text = text
                self.beep(0.1)
                time.sleep(2)
            except: time.sleep(0.5)

    def _temp_loop(self):
        while self.running:
            if IS_RASPBERRY_PI:
                try:
                    t = self.dht_device.temperature; h = self.dht_device.humidity
                    if t: self.temp_data["t"] = t
                    if h: self.temp_data["h"] = h
                except: pass
            time.sleep(2.0)

    def cleanup(self):
        self.running = False
        self.lights.running = False
        if IS_RASPBERRY_PI:
            if hasattr(self, 'dht_device'): self.dht_device.exit()
            GPIO.cleanup()
            for i in range(self.lights.strip.numPixels()):
                self.lights.strip.setPixelColor(i, Color(0,0,0))
            self.lights.strip.show()

    def _init_mock(self):
        self.distances = [120.0] * 8
        self.temp_data = {"t": 24.5, "h": 50}
        threading.Timer(5.0, lambda: setattr(self, 'nfc_id', 999999)).start()

# --- STANDALONE TEST MODE ---
if __name__ == "__main__":
    print("--- STARTING HARDWARE STANDALONE MODE ---")
    print("Initializing components (LEDs, NFC, Sensors, Relays)...")
    try:
        car = CarHardware()
        print("Hardware initialized successfully.")
        print("Running background threads... Press CTRL+C to exit.")
        while True:
            # Trigger ultrasonic sensors to keep data flowing
            car.trigger_sensors()
            # Print status every 2 seconds
            print(f"Temp: {car.temp_data['t']:.1f}C, Dist[0]: {car.distances[0]:.1f}cm")
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        car.cleanup()