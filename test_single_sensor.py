#!/usr/bin/env python3
"""Single Ultrasonic Sensor Diagnostic Test (software_V2.0).

Tests Echo 1 (Front Left, GPIO 17) and Trigger (GPIO 23).
"""
import time
from gpiozero import DistanceSensor
from config import PIN_TRIG, PINS_ECHO

ECHO_PIN = PINS_ECHO[0]  # GPIO 17 (Echo 1, Front Left)
TRIG_PIN = PIN_TRIG      # GPIO 23

print(f"--- TESTING ULTRASONIC SENSOR (Echo: GPIO {ECHO_PIN}, Trig: GPIO {TRIG_PIN}) ---")
print("Press CTRL+C to stop.")

sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN, max_distance=4)

try:
    while True:
        dist_cm = sensor.distance * 100
        print(f"Distance: {dist_cm:.1f} cm")
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\nStopping...")
except Exception as e:
    print(f"Sensor error: {e}")
