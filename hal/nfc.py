import time
import threading
from config import PIN_NFC_RST, NFC_SPI_SAFE_SPEED_HZ

try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522, MFRC522
    IS_HARDWARE = True
except ImportError:
    IS_HARDWARE = False


class NFCManager:
    """Manages the RC522 RFID/NFC reader with hardware reset and safe SPI speed."""

    def __init__(self, on_card_detected=None):
        self.on_card_detected = on_card_detected
        self.latest_id = None
        self.reader = None
        self.core = None
        self.running = True
        self.is_connected = False
        self._lock = threading.Lock()

        if IS_HARDWARE:
            self._init_hardware()
            threading.Thread(target=self._read_loop, daemon=True).start()
        else:
            self.is_connected = True

    def _hard_reset(self):
        """Perform a hardware reset pulse via GPIO."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PIN_NFC_RST, GPIO.OUT)
            GPIO.output(PIN_NFC_RST, GPIO.LOW)
            time.sleep(0.15)
            GPIO.output(PIN_NFC_RST, GPIO.HIGH)
            time.sleep(0.15)
        except Exception as e:
            print(f"NFC hard reset error: {e}")

    def _init_hardware(self):
        self._hard_reset()
        try:
            self.core = MFRC522(pin_rst=PIN_NFC_RST)
            # Apply safe SPI speed to prevent 0xB2 MISO line noise
            if hasattr(self.core, 'spi') and self.core.spi:
                self.core.spi.max_speed_hz = NFC_SPI_SAFE_SPEED_HZ

            version = self.core.Read_MFRC522(MFRC522.VersionReg)
            if version in [0x91, 0x92]:
                self.reader = SimpleMFRC522()
                self.reader.READER = self.core
                self.is_connected = True
                print(f"NFC reader initialized successfully (version: {hex(version)}).")
            else:
                print(f"NFC check warning: Unexpected version {hex(version)}.")
                self.reader = None
                self.is_connected = False
        except Exception as e:
            print(f"Error initializing NFC hardware: {e}")
            self.reader = None
            self.is_connected = False

    def _read_loop(self):
        last_scanned = None
        last_scan_time = 0

        while self.running:
            if not self.reader:
                time.sleep(2.0)
                self._init_hardware()
                continue

            try:
                card_id, _ = self.reader.read_no_block()
                now = time.time()
                if card_id:
                    # Debounce duplicate reads within 2 seconds
                    if card_id != last_scanned or (now - last_scan_time > 2.0):
                        last_scanned = card_id
                        last_scan_time = now
                        with self._lock:
                            self.latest_id = str(card_id)
                        if callable(self.on_card_detected):
                            self.on_card_detected(str(card_id))
                time.sleep(0.2)
            except Exception:
                time.sleep(0.5)

    def pop_latest_id(self):
        with self._lock:
            val = self.latest_id
            self.latest_id = None
            return val

    def cleanup(self):
        self.running = False
