import os

# ==========================================
#   PATH & FILE CONFIGURATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, "authorized_keys.txt")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# Assets Directory
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PNG_PATH = os.path.join(ASSETS_DIR, "logo.png")
BG_PNG_PATH = os.path.join(ASSETS_DIR, "background.png")
BG_JPG_PATH = os.path.join(ASSETS_DIR, "background.jpg")

# ==========================================
#   LED STRIP CONFIGURATION (WS2811)
# ==========================================
LEDS_FRONT_COUNT    = 6
LEDS_INTERIOR_COUNT = 24
LEDS_BACK_COUNT     = 8
LED_TOTAL           = LEDS_FRONT_COUNT + LEDS_INTERIOR_COUNT + LEDS_BACK_COUNT

LED_FREQ_HZ         = 800000
LED_DMA             = 10
LED_BRIGHTNESS      = 255
LED_INVERT          = False
LED_CHANNEL         = 0

# ==========================================
#   GPIO PIN MAPPING (BCM NUMBERING)
# ==========================================
PIN_LED_DATA = 12  # PWM0 (Physical Pin 32)
PIN_TRIG     = 23  # Shared Ultrasonic Trigger (Physical Pin 16)
PIN_BUZZER   = 13  # Active Piezo Buzzer (Physical Pin 33)
PIN_DHT      = 4   # DHT11 Temp/Humidity Sensor (Physical Pin 7)
PIN_RELAYS   = [14, 15]  # Relay 0: Main Power/Motor (Pin 8), Relay 1: Reverse (Pin 10)
PIN_NFC_RST  = 19  # RC522 NFC Reset Pin (Physical Pin 35)

# Ultrasonic Echo Pins: 4 Front (FL, FML, FMR, FR), 4 Rear (RL, RML, RMR, RR)
PINS_ECHO    = [17, 27, 22, 5, 6, 24, 16, 26]

SENSOR_NAMES = [
    "Front Left (1)", "Front Mid-L (2)", "Front Mid-R (3)", "Front Right (4)",
    "Rear Left (5)", "Rear Mid-L (6)", "Rear Mid-R (7)", "Rear Right (8)"
]

# ==========================================
#   SENSOR & SAFETY THRESHOLDS (60cm Max Range)
# ==========================================
DIST_MIN_VALID_CM             = 4.0   # 4cm min range (rejects transducer ring-down jitter < 4cm)
DIST_MAX_VALID_CM             = 60.0  # Max sensor range capped at 60cm per specification
DIST_CRITICAL_CM              = 20.0  # < 20cm: Critical red arc / solid tone
DIST_WARNING_CM               = 40.0  # 20-40cm: Amber warning arc / fast beep
DIST_SAFE_CM                  = 60.0  # 40-60cm: Green arc / slow beep
SENSOR_TIMEOUT_SEC            = 0.40  # Clear stale readings if no echo received within 400ms

# Ultrasonic Noise Rejection & Filtering
ULTRASONIC_FILTER_WINDOW      = 5     # 5-sample sliding median window to reject noise spikes
ULTRASONIC_EMA_APPROACH       = 0.75  # Fast response when an obstacle is getting closer
ULTRASONIC_EMA_RECEDE         = 0.45  # Smooth smoothing when an obstacle is moving away
ULTRASONIC_MIN_PING_INTERVAL  = 0.065 # 65ms minimum spacing to prevent echo reverberation crosstalk
ULTRASONIC_MISS_CLEAR_COUNT   = 2     # Require 2 consecutive out-of-range (>60cm) samples to clear

NFC_SPI_SAFE_SPEED_HZ  = 50000  # 50kHz safe SPI speed to prevent MISO line noise (0xB2)

# ==========================================
#   SECURITY & UI DEFAULTS
# ==========================================
DEFAULT_PIN            = "1234"
SYSTEM_TICK_MS         = 50

THEME = {
    "bg_dark": "#ffffff",                   # White Background
    "bg_panel": "rgba(240, 240, 240, 220)", # Semi-transparent white panels
    "accent_cyan": "#0088cc",               # Darker Cyan for white background contrast
    "accent_red": "#dd3333",
    "accent_green": "#00aa44",
    "accent_amber": "#ffaa00",
    "text_main": "#111111",                 # Dark Text
    "text_dim": "#555555",
    "menu_bg": "#e0e0e0",
    "menu_sel": "#cccccc"
}

# ==========================================
#   JETSON EXPLORER CONFIGURATION
# ==========================================
JETSON_IP = "192.168.10.112"
JETSON_WEB_PORT = 3000
JETSON_SSH_PORT = 22
JETSON_URL = f"http://{JETSON_IP}:{JETSON_WEB_PORT}"
JETSON_POLL_INTERVAL_SEC = 5.0
JETSON_SSH_USER = "jetson"  # Default user for thermal checks


