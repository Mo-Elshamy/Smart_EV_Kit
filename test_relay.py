#!/usr/bin/env python3
"""2-Channel Relay Diagnostic Test (software_V2.0).

Tests:
  - Relay 1: Motor / Main Power (GPIO 14, Physical Pin 8)
  - Relay 2: Reverse (GPIO 15, Physical Pin 10)
Note: Active Low Logic (LOW = ON / Energized, HIGH = OFF / Isolated)
"""
import time
import RPi.GPIO as GPIO
from config import PIN_RELAYS


def main():
    print("--- 2-CHANNEL RELAY TEST (Active Low) ---")
    print(f"Relay 1 (Motor):   GPIO {PIN_RELAYS[0]} (Physical Pin 8)")
    print(f"Relay 2 (Reverse): GPIO {PIN_RELAYS[1]} (Physical Pin 10)")
    print("Press CTRL+C to stop.\n")

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Start in safe OFF state (HIGH)
    GPIO.setup(PIN_RELAYS, GPIO.OUT, initial=GPIO.HIGH)

    try:
        while True:
            # Test Relay 1
            print(">> Energizing Relay 1 (Motor ON)...")
            GPIO.output(PIN_RELAYS[0], GPIO.LOW)
            time.sleep(2)
            print(">> De-energizing Relay 1 (Motor OFF)...")
            GPIO.output(PIN_RELAYS[0], GPIO.HIGH)
            time.sleep(1)

            # Test Relay 2
            print(">> Energizing Relay 2 (Reverse ON)...")
            GPIO.output(PIN_RELAYS[1], GPIO.LOW)
            time.sleep(2)
            print(">> De-energizing Relay 2 (Reverse OFF)...")
            GPIO.output(PIN_RELAYS[1], GPIO.HIGH)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Guarantee relays are left OFF
        GPIO.output(PIN_RELAYS, GPIO.HIGH)
        GPIO.cleanup()
        print("Relays safely disengaged.")


if __name__ == "__main__":
    main()
