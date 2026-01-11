import time
import argparse
from rpi_ws281x import PixelStrip, Color

# --- CONFIGURATION ---
# WS2811/NeoPixel Configuration
LED_COUNT      = 30      # Number of LED pixels. CHANGE THIS to match your strip length!
LED_PIN        = 12      # GPIO pin (18 is standard for PWM)
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

def setup_strip():
    """Initializes the WS2811 Strip"""
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    return strip

# --- PATTERNS ---

def color_wipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    print(f"Pattern: Wipe Color {color}")
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def police_strobe(strip, duration=5):
    """Flashes half Red, half Blue rapidly"""
    print("Pattern: POLICE STROBE")
    end_time = time.time() + duration
    
    half = strip.numPixels() // 2
    
    while time.time() < end_time:
        # State 1: Left Red, Right Blue
        for i in range(strip.numPixels()):
            if i < half:
                strip.setPixelColor(i, Color(255, 0, 0)) # Red
            else:
                strip.setPixelColor(i, Color(0, 0, 255)) # Blue
        strip.show()
        time.sleep(0.1)
        
        # State 2: Off
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        time.sleep(0.05)

        # State 3: Left Blue, Right Red
        for i in range(strip.numPixels()):
            if i < half:
                strip.setPixelColor(i, Color(0, 0, 255)) # Blue
            else:
                strip.setPixelColor(i, Color(255, 0, 0)) # Red
        strip.show()
        time.sleep(0.1)

def breathing_effect(strip, color_base, duration=5):
    """Smoothly fades brightness up and down"""
    print("Pattern: BREATHING")
    end_time = time.time() + duration
    
    # Fill strip with base color first
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color_base)
    
    while time.time() < end_time:
        # Fade Out
        for b in range(255, 20, -5):
            strip.setBrightness(b)
            strip.show()
            time.sleep(0.02)
        # Fade In
        for b in range(20, 255, 5):
            strip.setBrightness(b)
            strip.show()
            time.sleep(0.02)
            
    # Reset brightness for next mode
    strip.setBrightness(255)

def knight_rider(strip, color, duration=5):
    """Scanner / Cylon effect"""
    print("Pattern: KNIGHT RIDER")
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Forward
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, color)
            # Turn off previous pixel to create trail
            if i > 0:
                strip.setPixelColor(i-1, Color(0,0,0))
            strip.show()
            time.sleep(0.05)
            
        # Backward
        for i in range(strip.numPixels()-1, -1, -1):
            strip.setPixelColor(i, color)
            if i < strip.numPixels()-1:
                strip.setPixelColor(i+1, Color(0,0,0))
            strip.show()
            time.sleep(0.05)

def clear_strip(strip):
    """Turn off all LEDs"""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# --- MAIN ---
if __name__ == '__main__':
    # Verify root (Sudo is required for WS2811 PCM/DMA access)
    try:
        with open('/dev/mem', 'r') as f:
            pass
    except PermissionError:
        print("CRITICAL ERROR: This script requires SUDO.")
        print("Run: sudo python3 test_light_patterns.py")
        exit()

    strip = setup_strip()
    
    print("--- WS2811 LED TEST STARTING ---")
    print(f"Driving {LED_COUNT} pixels on GPIO {LED_PIN}")
    print("Press CTRL+C to stop.")

    try:
        while True:
            # 1. Wipe Green (Check connectivity)
            color_wipe(strip, Color(0, 255, 0)) # Green
            time.sleep(1)
            clear_strip(strip)
            
            # 2. Police Strobe (Red/Blue)
            police_strobe(strip, duration=5)
            clear_strip(strip)
            
            # 3. Breathing (Purple)
            # (255, 0, 255) is Purple
            breathing_effect(strip, Color(255, 0, 255), duration=6)
            
            # 4. Knight Rider (Red scanner)
            knight_rider(strip, Color(255, 0, 0), duration=5)
            clear_strip(strip)

    except KeyboardInterrupt:
        print("\nStopping...")
        clear_strip(strip)
