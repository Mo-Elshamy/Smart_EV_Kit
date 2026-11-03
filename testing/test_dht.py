import time
import board
import adafruit_dht

# --- CONFIGURATION ---
# We are using GPIO 4 (Physical Pin 7)
DHT_PIN = board.D4 

def main():
    print("--- DHT11 TEMPERATURE SENSOR DIAGNOSTICS ---")
    print("Sensor: DHT11")
    print("Pin:    GPIO 4")
    print("--------------------------------------------")
    print("Initializing sensor... (This might take 2 seconds)")

    try:
        # Initialize the DHT device
        # use_pulseio=False is often needed on newer Linux kernels
        dht_device = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
        
        while True:
            try:
                # 1. Read Data
                temperature_c = dht_device.temperature
                humidity = dht_device.humidity
                
                # 2. Print Data
                print(f"Temp: {temperature_c:.1f} °C    Humidity: {humidity}%")
                
            except RuntimeError as error:
                # DHT sensors are tricky; they often fail to read. 
                # This is normal. We just try again.
                print(f"Reading error (retrying): {error.args[0]}")
            except Exception as error:
                dht_device.exit()
                raise error

            # 3. Wait (DHT11 is slow, don't read faster than every 2 seconds)
            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        pass

if __name__ == "__main__":
    main()