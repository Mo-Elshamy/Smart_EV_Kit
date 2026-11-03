import RPi.GPIO as GPIO
import time

# --- CONFIGURATION ---
# Change this to the pin you want to test
# Useful pins for NFC debugging:
# 8 (SDA), 9 (MISO), 10 (MOSI), 11 (SCK), 25 (RST)
TEST_PIN = 14 

def main():
    print(f"--- GPIO PIN {TEST_PIN} BLINK TEST ---")
    print("1. Disconnect the NFC Reader.")
    print(f"2. Connect an LED (with resistor) to GPIO {TEST_PIN} and GND.")
    print("3. Press CTRL+C to stop.")
    
    # Setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TEST_PIN, GPIO.OUT)
    
    try:
        while True:
            print("ON")
            GPIO.output(TEST_PIN, GPIO.HIGH)
            time.sleep(1)
            
            print("OFF")
            GPIO.output(TEST_PIN, GPIO.LOW)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        GPIO.cleanup()

if __name__ == "__main__":
    main()