#!/usr/bin/env python3
"""LED Strip Calibration & Interactive Diagnostic Utility (software_V2.0).

Allows testing and calibrating Front, Interior, and Rear zones of the WS2811 strip.
Must be run with sudo for direct DMA/PWM access: sudo python3 calibrate_led.py
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hal.lighting import LightingSystem
from config import LEDS_FRONT_COUNT, LEDS_INTERIOR_COUNT, LEDS_BACK_COUNT, LED_TOTAL


def main():
    print("==================================================")
    print("   SMART EV KIT — LED CALIBRATION & TEST TOOL     ")
    print("==================================================")
    print(f"Total LEDs: {LED_TOTAL}")
    print(f"Front Headlights: 0 to {LEDS_FRONT_COUNT - 1} ({LEDS_FRONT_COUNT} LEDs)")
    print(f"Interior Underglow: {LEDS_FRONT_COUNT} to {LEDS_FRONT_COUNT + LEDS_INTERIOR_COUNT - 1} ({LEDS_INTERIOR_COUNT} LEDs)")
    print(f"Rear Taillights: {LEDS_FRONT_COUNT + LEDS_INTERIOR_COUNT} to {LED_TOTAL - 1} ({LEDS_BACK_COUNT} LEDs)")
    print("--------------------------------------------------")

    lights = LightingSystem()

    try:
        while True:
            print("\nSelect a calibration mode:")
            print("  1: Test Front Headlights (Toggle ON/OFF)")
            print("  2: Test Rear Taillights (Toggle ON/OFF)")
            print("  3: Test Left Turn Signal")
            print("  4: Test Right Turn Signal")
            print("  5: Test Hazard Lights")
            print("  6: Test Interior Solid (Red / Green / Blue / White)")
            print("  7: Test Interior Breathing Mode")
            print("  8: Test Interior Rainbow Mode")
            print("  9: Turn All OFF")
            print("  0: Exit")

            choice = input("\nEnter choice [0-9]: ").strip()

            if choice == "1":
                lights.front_enabled = not lights.front_enabled
                print(f"Front Headlights: {'ON' if lights.front_enabled else 'OFF'}")
            elif choice == "2":
                lights.back_enabled = not lights.back_enabled
                print(f"Rear Taillights: {'ON' if lights.back_enabled else 'OFF'}")
            elif choice == "3":
                lights.set_turn_signal("LEFT")
                print("Left Turn Signal blinking (Amber)...")
            elif choice == "4":
                lights.set_turn_signal("RIGHT")
                print("Right Turn Signal blinking (Amber)...")
            elif choice == "5":
                lights.set_turn_signal("HAZARD")
                print("Hazard Signals blinking...")
            elif choice == "6":
                lights.interior_enabled = True
                lights.set_interior_mode("SOLID")
                color_choice = input("Enter RGB color (e.g., '255 0 0' or '0 255 255'): ").strip().split()
                if len(color_choice) == 3:
                    try:
                        r, g, b = map(int, color_choice)
                        lights.set_interior_rgb(r, g, b)
                        print(f"Interior set to RGB({r}, {g}, {b})")
                    except ValueError:
                        print("Invalid RGB numbers.")
                else:
                    lights.set_interior_rgb(0, 0, 255)
                    print("Defaulting to Blue RGB(0, 0, 255)")
            elif choice == "7":
                lights.interior_enabled = True
                lights.set_interior_mode("BREATHE")
                print("Interior Breathing mode active.")
            elif choice == "8":
                lights.interior_enabled = True
                lights.set_interior_mode("RAINBOW")
                print("Interior Rainbow mode active.")
            elif choice == "9":
                lights.set_all_zones(False)
                lights.set_turn_signal("OFF")
                print("All zones turned OFF.")
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        lights.stop()
        print("Calibration tool closed.")


if __name__ == "__main__":
    main()
