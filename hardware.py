"""Hardware Module for Smart EV Kit (software_V2.0).

Exposes CarHardware and LightingSystem for GUI and testing integration.
"""
import time
from hal.controller import CarHardware
from hal.lighting import LightingSystem

__all__ = ["CarHardware", "LightingSystem"]

# --- STANDALONE TEST MODE ---
if __name__ == "__main__":
    print("--- STARTING HARDWARE STANDALONE MODE (V2.0) ---")
    print("Initializing components (LEDs, NFC, Sensors, Relays)...")
    try:
        car = CarHardware()
        print("Hardware initialized successfully.")
        print("Running background loops... Press CTRL+C to exit.")
        while True:
            car.trigger_sensors()
            temp = car.temp_data
            dist = car.distances
            print(f"Temp: {temp['t']:.1f}°C, Hum: {temp['h']:.1f}%, Distances: {dist}")
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping...")
        car.cleanup()
