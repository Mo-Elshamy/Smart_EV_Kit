import time
import RPi.GPIO as GPIO

# --- CONFIGURATION ---
BUZZER_PIN = 12

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)

def beep(duration, pause_after=0.1):
    """
    Helper to beep the active buzzer for a specific duration.
    """
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(pause_after)

def play_monsters_vs_aliens_rhythm():
    print("--- Playing: Monsters vs. Aliens (Axel F Rhythm) ---")
    print("Since you have an ACTIVE buzzer, this plays the Rhythm only.")
    
    # The President's first song: Axel F (Beverly Hills Cop Theme)
    # Rhythm structure:
    # F ... Ab ... F . F . Bb . F ... Eb
    
    # 1. F (Long)
    beep(0.25, 0.2)
    # 2. Ab (Long)
    beep(0.25, 0.2)
    # 3. F (Long)
    beep(0.25, 0.1)
    # 4. F (Short - the double tap)
    beep(0.12, 0.1)
    # 5. Bb (Long)
    beep(0.25, 0.2)
    # 6. F (Long)
    beep(0.25, 0.2)
    # 7. Eb (Long)
    beep(0.25, 0.4)

    # Second Phrase
    # F ... C ... F . F . Db ... C ... Ab
    beep(0.25, 0.2) # F
    beep(0.25, 0.2) # C
    beep(0.25, 0.1) # F
    beep(0.12, 0.1) # F (Short)
    beep(0.25, 0.2) # Db
    beep(0.25, 0.2) # C
    beep(0.25, 0.4) # Ab

    print("--- Playing: Close Encounters (5 Note Motif) ---")
    # The President's second song: The actual "First Contact" signal
    # Re - Mi - Do - Do(Low) - Sol
    time.sleep(1)
    
    # These are slow, distinct tones
    beep(0.4, 0.1) # Re
    beep(0.4, 0.1) # Mi
    beep(0.4, 0.1) # Do
    beep(0.4, 0.1) # Do (Low)
    beep(0.8, 0.5) # Sol (Long)

def main():
    try:
        setup()
        print(f"Testing Buzzer on GPIO {BUZZER_PIN}")
        
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