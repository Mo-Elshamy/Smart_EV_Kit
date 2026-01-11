# RQ EV Car Control System

**Version:** 1.0.0 **Platform:** Raspberry Pi 4 Model B (Bookworm OS)

## 1. Project Overview

The **RQ EV Car Control System** is a centralized Vehicle Control Unit (VCU) designed for electric buggies and educational EV platforms. Built on the Raspberry Pi 4 architecture, it integrates safety sensors, access control, and lighting management into a single, cohesive system.

This project replaces traditional analog car switches with a modern, 7-inch touchscreen interface (`PyQt5`), offering a digital driving experience similar to modern commercial electric vehicles.

### Key Features

* **Keyless Authentication:** Secure NFC/RFID access control prevents the vehicle from starting without an authorized key card.
* **Intelligent Safety System:** An 8-sensor ultrasonic array provides real-time parking assistance with visual radar feedback and variable frequency audio warnings.
* **Dynamic Lighting:** Controls addressable WS2811 LED strips for Headlights, Taillights, Turn Signals, and animated Interior Underglow.
* **Digital Dashboard:** A high-contrast, touch-friendly GUI displays speed (simulated), temperature, humidity, time, and system status.
* **Motor Interlock:** Hardware relays physically isolate the motor control circuits until software authentication is verified.

## 2. Hardware Configuration

### Bill of Materials (BOM)

* **Controller:** Raspberry Pi 4 Model B (4GB or 8GB recommended).
* **Display:** 7-inch HDMI Touchscreen (Waveshare or similar).
* **Power System:**
  * 48V Main Battery Pack.
  * 48V to 12V Buck Converter (for LED Strips).
  * 48V to 5V Buck Converter (for Pi, Sensors, Relays).
* **Sensors:**
  * 8x HC-SR04 Ultrasonic Distance Sensors.
  * 1x RC522 NFC/RFID Reader Module.
  * 1x DHT11 Temperature & Humidity Sensor.
* **Actuators:**
  * WS2811 Addressable LED Strip (12V).
  * 2-Channel 5V Relay Module (Active Low).
  * Active Piezo Buzzer.
* **Circuit Components:**
  * Resistors: 1kΩ and 2kΩ (for 16x Voltage Dividers on Ultrasonic Echo lines).
  * Breadboard or PCB for signal distribution.

### Master Pinout Map (BCM Numbering)

*Note: This configuration corresponds to `hardware.py`.*

| Component                 | Function                | GPIO Pin          | Physical Pin | Notes                                      |
| ------------------------- | ----------------------- | ----------------- | ------------ | ------------------------------------------ |
| **Ultrasonic (x8)** | **TRIG (Shared)** | **GPIO 23** | **16** | One trigger fires all sensors.             |
| **Front Sensors**   | Echo 1 (Front Left)     | **GPIO 17** | 11           | Voltage Divider Required!                  |
|                           | Echo 2 (Front Mid-L)    | **GPIO 27** | 13           | Voltage Divider Required!                  |
|                           | Echo 3 (Front Mid-R)    | **GPIO 22** | 15           | Voltage Divider Required!                  |
|                           | Echo 4 (Front Right)    | **GPIO 5**  | 29           | Voltage Divider Required!                  |
| **Rear Sensors**    | Echo 5 (Rear Left)      | **GPIO 6**  | 31           | Voltage Divider Required!                  |
|                           | Echo 6 (Rear Mid-L)     | **GPIO 24** | 18           | Voltage Divider Required!                  |
|                           | Echo 7 (Rear Mid-R)     | **GPIO 16** | 36           | Voltage Divider Required!                  |
|                           | Echo 8 (Rear Right)     | **GPIO 26** | 37           | Voltage Divider Required!                  |
| **NFC (RC522)**     | SDA (Chip Select)       | **GPIO 8**  | 24           | SPI Interface (3.3V Only).                 |
|                           | SCK (Clock)             | **GPIO 11** | 23           |                                            |
|                           | MOSI                    | **GPIO 10** | 19           |                                            |
|                           | MISO                    | **GPIO 9**  | 21           |                                            |
|                           | RST (Reset)             | **GPIO 19** | 35           | Custom pin assignment.                     |
| **Lighting**        | Data Input              | **GPIO 12** | 32           | **PWM0**Channel required for WS2811. |
| **Relays**          | Relay 1 (Main Power)    | **GPIO 14** | 8            | Active Low Logic.                          |
|                           | Relay 2 (Reverse)       | **GPIO 15** | 10           | Active Low Logic.                          |
| **Audio**           | Active Buzzer           | **GPIO 13** | 33           |                                            |
| **Environment**     | DHT11 Data              | **GPIO 4**  | 7            | Requires Pull-up resistor.                 |

## 3. Software Installation

This project runs on  **Raspberry Pi OS (Bookworm)** . Older versions (Bullseye/Buster) may require different GPIO libraries.

### A. System Preparation

1. Update the system:
   ```
   sudo apt update && sudo apt upgrade -y
   ```
2. Enable hardware interfaces:
   * Run `sudo raspi-config`
   * Navigate to  **Interface Options** .
   * Enable **SPI** (for NFC).
   * Enable **SSH** (for remote access).
   * Enable **VNC** (optional, for remote desktop).
3. Reboot the Pi.

### B. Install Dependencies

Install the required system packages and Python libraries. Note the use of `rpi-lgpio` for Bookworm compatibility.

```
# 1. System Libraries
sudo apt install -y python3-rpi-lgpio python3-pip python3-pyqt5 python3-spidev git libgpiod2

# 2. Python Drivers (using break-system-packages is necessary on Bookworm for hardware access)
sudo pip3 install mfrc522 adafruit-circuitpython-dht rpi_ws281x gpiozero --break-system-packages
```

### C. Enable Kiosk Mode (Autostart)

To make the dashboard launch automatically in full screen when the car turns on:

1. Create the autostart directory:
   ```
   mkdir -p ~/.config/autostart
   ```
2. Create a desktop entry file:
   ```
   nano ~/.config/autostart/ev_dashboard.desktop
   ```
3. Paste the following configuration:
   ```
   [Desktop Entry]
   Type=Application
   Name=EV Dashboard
   Exec=sudo -E python3 /home/rqev/EV_Dashboard/main.py
   Terminal=false
   Hidden=false
   X-GNOME-Autostart-enabled=true
   ```
4. **Important:** Configure display permissions for root:
   * Edit `.bashrc`: `nano ~/.bashrc`
   * Add to the bottom: `xhost +local:root`


## 4. Software Architecture & Code Reference

The system is split into two primary distinct layers: the **Hardware Abstraction Layer (HAL)** and the  **User Interface (GUI)** .

### A. Low-Level Control: `hardware.py`

This module acts as the "Body" of the car. It abstracts complex electrical signals (PWM, SPI, GPIO Interrupts) into simple, high-level commands. It runs background threads to ensure critical features (like brake lights or sensor readings) never lag, even if the GUI is busy.

#### Class: `LightingSystem`

Manages the WS2811 Addressable LED strip. It treats the single physical strip as three logical zones.

* **Key Logic:**
  * **Animation Loop:** A background thread (`_animation_loop`) updates the strip every 0.4s to handle blinking turn signals without blocking the main processor.
  * **Zones:**
    * **Front:** Pixels `0` to `LEDS_FRONT_COUNT`. (White, flashes Amber).
    * **Interior:** Middle section. Supports "Solid", "Breathe", and "Rainbow" modes.
    * **Rear:** Last section. (Red, flashes Amber).
* **Function Reference:**
  * `__init__(self)`: Initializes the strip with correct PWM frequency (800kHz) and starts the animation thread.
  * `_animation_loop(self)`: The background worker that calculates blink timing and renders frames to the LEDs.
  * `_render_front(self, blink)`, `_render_interior(self, blink)`, `_render_back(self, blink)`: Internal helpers that draw the specific color logic for each zone.
  * `set_turn_signal(mode)`: Sets signal state. Mode can be 'LEFT', 'RIGHT', 'HAZARD', or 'OFF'.
  * `set_brakes(active)`: Boolean toggle. If True, rear lights brighten.
  * `set_interior_rgb(r, g, b)`: Sets the base color for the interior zone.
  * `set_interior_mode(mode)`: Sets the pattern ('SOLID', 'BREATHE', 'RAINBOW').

#### Class: `CarHardware`

The main controller class that aggregates all sensors and actuators.

* **Sensors:**
  * **Ultrasonic:** Uses `gpiozero.DigitalInputDevice` with callbacks (`_on_echo_rise`, `_on_echo_fall`) to measure pulse width efficiently.
  * **NFC:** Runs in a dedicated thread (`_nfc_loop`) to poll for cards without freezing the app. Checks for hardware presence on boot (Verifies Chip Version).
  * **DHT11:** Runs in a dedicated thread (`_temp_loop`) reading every 2 seconds.
* **Actuators:**
  * **Relays:** Controls Motor (Relay 1) and Reverse (Relay 2) using Active Low logic (Low = ON).
  * **Buzzer:** Non-blocking control via `set_buzzer()`.
* **Function Reference:**
  * `_init_gpio(self)`: Sets up BCM mode, pin directions, and attaches interrupt callbacks for ultrasonic sensors.
  * `_start_threads(self)`: Launches the NFC and Temperature monitoring threads.
  * `trigger_sensors(self)`: Sends a 10µs pulse to the shared Trigger pin to fire all ultrasonic sensors.
  * `set_relay(index, state)`: Controls physical relays (Active Low logic). Index 0 = Main, 1 = Reverse.
  * `set_buzzer(state)`: Turns the active buzzer on or off immediately.
  * `beep(duration)`: Blocking call to beep for a specific duration (use sparingly).
  * `cleanup(self)`: Safely closes threads and resets GPIO pins on exit.

### B. High-Level Interface: `main.py`

This module is the "Brain" of the car. It uses **PyQt5** to render the touchscreen interface and manages the system state (Locked vs. Unlocked).

#### Class: `ParkingVisualizer` (Custom Widget)

A highly optimized graphical widget that draws the car state using `QPainter`.

* **Dynamic Scaling:** Automatically scales the car graphics to fit any screen size while maintaining aspect ratio.
* **Rendering:** Draws a vector-style "Off-Road Buggy" with suspension, chunky tires, and roll cage.
* **Radar:** Visualizes ultrasonic data as color-coded "WiFi-style" arcs (Green/Yellow/Red) around the car.
* **Function Reference:**
  * `update_sensor_data(distances)`: Accepts a list of 8 floats (cm) and triggers a repaint.
  * `paintEvent(event)`: The main drawing loop. Handles coordinate translation, scaling, and drawing the car model.
  * `draw_radar_arc(...)`: Helper to draw the curved signal bars based on distance proximity.
  * `draw_tire(...)`: Helper to draw rotated tires relative to the car body.

#### Class: `EVSystem` (Main Window)

The main application window that manages the screens (`QStackedWidget`).

* **Screens:**
  1. **Locked:** Security screen with PIN pad (Pass: `1234`) and NFC scanning prompt.
  2. **Dashboard:** The driving mode. Displays speed, clock, temp, and controls for Lights, Reverse, and Lock.
  3. **Config:** Settings hub for "Interior Lighting", "Access Control", and "Diagnostics".
  4. **Confirmation:** Safety prompt before locking the vehicle.
* **System Loop (`update_system`):**
  * Runs every  **50ms** .
  * Polls `CarHardware` for new sensor data.
  * Updates the `ParkingVisualizer`.
  * Calculates safety logic: If any object is `< 30cm`, it triggers the high-frequency alarm.
* **Persistence:**
  * Loads/Saves authorized NFC Key IDs to `authorized_keys.txt` so keys are remembered after reboot.
  * Detects the environment (`BASE_DIR`) to ensure assets like `background.png` load correctly on startup.
* **Function Reference:**
  * **Initialization:**
    * `__init__`: Sets up window, hardware link, and starts the heartbeat timer.
    * `apply_background(widget)`: Finds background images and applies them via stylesheet.
  * **Logic:**
    * `update_system()`: The main 50ms loop. Handles NFC checks, sensor triggering, visualizer updates, and beeping logic.
    * `unlock_system(user_id)`: Transitions to Dashboard, turns on Relay 1 (Main Power), and plays welcome animation.
    * `lock_system()`: Transitions to Lock Screen, turns OFF all relays and lights.
  * **Access Control:**
    * `load_authorized_keys()` / `save_authorized_key()`: File I/O for key management.
    * `check_pin()`: Validates the manual PIN entry (Default: "1234").
  * **Configuration:**
    * `update_interior_color()`: Reads RGB sliders and updates the `LightingSystem`.
    * `set_pattern(mode)`: Changes the interior lighting effect mode.
    * `update_diagnostics()`: Populates the diagnostics table with raw sensor data for debugging.

### C. Logic Flow

1. **Boot:** System initializes `hardware.py`. Relays start OFF. NFC reader performs a handshake.
2. **Lock State:** GUI shows Lock Screen. NFC thread waits for a known card ID.
3. **Unlock:** Valid card or PIN -> Relays Energize (Motor ON) -> GUI switches to Dashboard.
4. **Drive:**
   * Ultrasonic sensors update 20 times/second.
   * User toggles "Left Turn" -> `main.py` tells `hardware.py` -> LED Thread blinks specific pixels.
5. **Shutdown/Lock:** User presses Lock -> Relays Cut Power -> System returns to Lock Screen.



## 5. Troubleshooting & Common Issues

This section covers specific errors encountered during development and their solutions.

### A. Display / GUI Errors

**Error:** `qt.qpa.xcb: could not connect to display`

* **Cause:** Trying to run the GUI from an SSH terminal without specifying the display output.
* **Solution:**
  1. Export the display variable: `export DISPLAY=:0`
  2. Grant root permission to screen: `xhost +local:root`
  3. Run with environment preservation: `sudo -E python3 main.py`

### B. NFC Reader Issues

**Error:** `0xb2` or `Warning: Reader returned strange version`

* **Cause:** Data corruption on the MISO line (Bit flipping). Usually caused by loose wiring or "Safe Mode" speed required.
* **Solution:**
  1. Check connections on **GPIO 9 (MISO)** and  **GPIO 11 (SCK)** .
  2. Ensure the reader is powered by **3.3V** (NOT 5V).
  3. The software includes a "Handshake" check on startup. If it fails, check physical soldering on the blue module headers.

### C. Ultrasonic Sensors

**Error:** `RuntimeError: Failed to add edge detection`

* **Cause:** Conflict between the old `RPi.GPIO` library and the new Raspberry Pi OS (Bookworm) kernel.
* **Solution:** The project uses `gpiozero` and `rpi-lgpio` internally to bypass this. Do not uninstall these libraries.

**Issue:** Readings are always 0.0cm.

* **Cause:** Voltage divider resistors (1kΩ/2kΩ) might be loose, or the sensor is not powered with 5V.
* **Check:** Ensure the **VCC** of the sensor goes to  **5V** , but the **Echo** goes through the resistors before hitting the Pi's **3.3V** pin.

### D. LED Issues

**Issue:** LEDs colors are swapped (e.g., Red is Green).

* **Solution:** The strip type is set in `hardware.py`.
  * Current setting: `ws.WS2811_STRIP_RGB`
  * If you change strips, edit the `PixelStrip` initialization line to `STRIP_GRB` or `STRIP_BRG`.

**Issue:** LEDs flicker randomly.

* **Cause:** Missing Common Ground.
* **Solution:** Ensure the **Black Wire** (GND) from the 12V Buck Converter connects to **BOTH** the LED Strip and the Raspberry Pi Pin 6/9/14.

### E. Relays

**Issue:** Relays start ON when the system boots.

* **Cause:** Most relay modules are "Active Low" (Low signal = ON).
* **Solution:** The code initializes pins to `GPIO.HIGH` (OFF) on boot to prevent this. If you change relay modules, check if they are Active High or Low.

## 6. How to Edit

To adjust settings without rewriting code, edit the top section of `hardware.py`:

```
# ==========================================
#   USER CONFIGURATION
# ==========================================
LEDS_FRONT_COUNT    = 6   # Change LED counts here
LEDS_INTERIOR_COUNT = 24
LEDS_BACK_COUNT     = 8

PIN_LED_DATA = 12         # Change GPIO pins here

```

## 7. Notes and Future Adjustments

This section documents critical bugs fixed during initial development to prevent regression in future updates.

### Resolved Critical Bugs

1. **Light Control Failure:**
   * **Problem:** The GUI buttons for lights and interior patterns were unresponsive, and the lights remained stuck in the "ON" state.
   * **Fix:** The `hardware.py` logic was updated to correctly map GUI toggle signals to the LED animation loop.
2. **Unintended Motion (Safety Critical):**
   * **Problem:** Upon system boot or unlock, the Motor Relay (Relay 1) would energize immediately, potentially causing the car to move before the software was ready.
   * **Fix:** The relay logic was inverted (Active Low) and the initialization state was explicitly set to `GPIO.HIGH` (OFF) to ensure the car remains stationary until the user explicitly engages it.

**Project Completed.**
