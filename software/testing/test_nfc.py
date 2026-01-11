import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522, MFRC522
import time

# --- CONFIGURATION ---
PIN_NFC_RST = 19 # Matches your hardware.py config

def hard_reset():
    """Manually reset the NFC module via GPIO"""
    print(f"Performing Hard Reset on GPIO {PIN_NFC_RST}...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_NFC_RST, GPIO.OUT)
    GPIO.output(PIN_NFC_RST, GPIO.LOW)  # Hold in Reset
    time.sleep(0.5)                 # Long wait
    GPIO.output(PIN_NFC_RST, GPIO.HIGH) # Release Reset
    time.sleep(0.5)                 # Long wait for boot
    print("Reset Complete.")

def main():
    print("--- NFC DIAGNOSTIC TOOL v3.0 (Integrated) ---")
    
    # Suppress GPIO warnings
    GPIO.setwarnings(False)
    
    # 1. Force Hardware Reset
    hard_reset()

    # 2. Initialize Reader
    try:
        # Standard init (Speed defaults to 1MHz)
        # We use the low-level MFRC522 class first to configure pins/speed
        reader = MFRC522(pin_rst=PIN_NFC_RST)
        
        # 3. Apply Ultra-Safe Mode Speed
        # If your wires are long or loose, 1MHz is too fast.
        # We lower it to 50kHz for maximum stability.
        if hasattr(reader, 'spi'):
            reader.spi.max_speed_hz = 50000 
            print(f"SPI Speed set to: {reader.spi.max_speed_hz} Hz (Safe Mode)")
            
    except Exception as e:
        print(f"Error initializing: {e}")
        return

    print("-----------------------------")
    print("Reading Chip Version...")
    print("Target: 0x91 or 0x92")
    print("Press CTRL+C to stop.")
    print("-----------------------------")

    try:
        while True:
            # Read version register to verify communication
            version = reader.Read_MFRC522(MFRC522.VersionReg)
            hex_ver = hex(version)

            if version == 0x91 or version == 0x92:
                print(f"✅ SUCCESS: {hex_ver} (Hardware OK)")
                # Test Card Read
                status, TagType = reader.MFRC522_Request(MFRC522.PICC_REQIDL)
                if status == MFRC522.MI_OK:
                    print("   >>> CARD DETECTED! <<<")
                    # Try to read UID
                    (status, uid) = reader.MFRC522_Anticoll()
                    if status == MFRC522.MI_OK:
                        print(f"   UID: {uid}")
            
            elif version == 0xb2:
                 # 0x92 is 10010010
                 # 0xB2 is 10110010 (Bit 5 is flipped high)
                 print(f"⚠️  ERROR 0xB2: MISO Line Noise.")
                 print("    -> The MISO wire (Pin 21) is likely loose or cold-soldered.")
            
            elif version == 0x00:
                print(f"❌ DEAD (0x00): Check Power (3.3V) and Ground.")
            
            elif version == 0xFF:
                 print(f"❌ ERROR (0xFF): Check Wiring (SDA, SCK, MOSI).")

            else:
                print(f"⚠️  Noise: {hex_ver}")

            time.sleep(1.0) # Slow polling

    except KeyboardInterrupt:
        print("\nStopping...")
        GPIO.cleanup()

if __name__ == "__main__":
    main()