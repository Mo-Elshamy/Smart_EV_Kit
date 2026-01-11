from gpiozero import DistanceSensor
from time import sleep

# Define Pins (GPIO Numbers)
# Echo=17, Trigger=23
sensor = DistanceSensor(echo=19, trigger=23, max_distance=4)

print("--- TESTING SENSOR (GPIO ZERO) ---")
print("Press CTRL+C to stop")

while True:
    try:
        # Distance is in meters, convert to cm
        dist_cm = sensor.distance * 100
        print(f"Distance: {dist_cm:.1f} cm")
        sleep(0.1)
    except Exception as e:
        print(f"Error: {e}")
        sleep(0.5)
