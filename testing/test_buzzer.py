#!/usr/bin/env python3
"""Active Piezo Buzzer Diagnostic & Rhythm Test (software_V2.0).

Verifies buzzer functionality on GPIO 13 (Physical Pin 33).
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import RPi.GPIO as GPIO
from config import PIN_BUZZER as BUZZER_PIN


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)


def beep(duration, pause_after=0.1):
    """Helper to beep the active buzzer for a specific duration."""
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(pause_after)


def play_monsters_vs_aliens_rhythm():
    print("--- Playing: Monsters vs. Aliens (Axel F Rhythm) ---")
    beep(0.25, 0.2)
    beep(0.25, 0.2)
    beep(0.25, 0.1)
    beep(0.12, 0.1)
    beep(0.25, 0.2)
    beep(0.25, 0.2)
    beep(0.25, 0.4)

    # Second Phrase
    beep(0.25, 0.2)
    beep(0.25, 0.2)
    beep(0.25, 0.1)
    beep(0.12, 0.1)
    beep(0.25, 0.2)
    beep(0.25, 0.2)
    beep(0.25, 0.4)


def main():
    try:
        setup()
        print(f"Testing Buzzer on GPIO {BUZZER_PIN} (Physical Pin 33)")
        while True:
            play_monsters_vs_aliens_rhythm()
            print("Replaying in 3 seconds... (CTRL+C to stop)")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
