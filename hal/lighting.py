import time
import threading
import math
from config import (
    LEDS_FRONT_COUNT, LEDS_INTERIOR_COUNT, LEDS_BACK_COUNT, LED_TOTAL,
    PIN_LED_DATA, LED_FREQ_HZ, LED_DMA, LED_BRIGHTNESS, LED_INVERT, LED_CHANNEL
)

class MockPixelStrip:
    def __init__(self, num=LED_TOTAL, *args, **kwargs):
        self.n = num
        self._pixels = [(0, 0, 0)] * num

    def begin(self):
        pass

    def setPixelColor(self, index, color):
        if 0 <= index < self.n:
            self._pixels[index] = color

    def show(self):
        pass

    def numPixels(self):
        return self.n

    def setBrightness(self, b):
        pass

try:
    from rpi_ws281x import PixelStrip, Color, ws
    IS_HARDWARE = True
except ImportError:
    IS_HARDWARE = False
    PixelStrip = MockPixelStrip

    class Color:
        def __new__(cls, r, g, b):
            return (r, g, b)

    class ws:
        WS2811_STRIP_RGB = 0


class LightingSystem:
    """Manages the 3-zone WS2811 Addressable LED strip:
    - Front Headlights & Indicators (White / Amber)
    - Interior Underglow & Ambient (Solid / Breathe / Rainbow)
    - Rear Taillights & Indicators (Red / Amber)
    """

    def __init__(self):
        strip_type = getattr(ws, "WS2811_STRIP_RGB", 0)
        self.strip = PixelStrip(
            LED_TOTAL, PIN_LED_DATA, LED_FREQ_HZ, LED_DMA, LED_INVERT,
            LED_BRIGHTNESS, LED_CHANNEL, strip_type
        )
        if IS_HARDWARE:
            try:
                self.strip.begin()
            except RuntimeError as e:
                print(f"Warning: ws2811_init failed ({e}). Running LED in simulation mode (run with sudo for hardware access).")
                self.strip = MockPixelStrip(LED_TOTAL)

        # Zone enable states (linked to dashboard buttons)
        self.front_enabled = False
        self.interior_enabled = False
        self.back_enabled = False

        # States & animation
        self.turn_signal_state = "OFF"  # "OFF", "LEFT", "RIGHT", "HAZARD"
        self.interior_color = (0, 0, 255)
        self.interior_mode = "SOLID"
        self.running = True
        self.anim_step = 0
        self._lock = threading.Lock()

        self.anim_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.anim_thread.start()

    def set_zone(self, zone_name, state: bool):
        """Enable or disable a specific lighting zone."""
        name = zone_name.lower()
        with self._lock:
            if name in ["front", "headlights"]:
                self.front_enabled = bool(state)
            elif name in ["interior", "body", "underglow"]:
                self.interior_enabled = bool(state)
            elif name in ["back", "rear", "taillights"]:
                self.back_enabled = bool(state)

    def set_all_zones(self, state: bool):
        """Turn on or off all zones (e.g. on vehicle lock/unlock)."""
        with self._lock:
            self.front_enabled = bool(state)
            self.interior_enabled = bool(state)
            self.back_enabled = bool(state)

    def set_turn_signal(self, mode: str):
        """Set turn signal mode: 'OFF', 'LEFT', 'RIGHT', 'HAZARD'."""
        with self._lock:
            self.turn_signal_state = mode.upper() if mode else "OFF"

    def set_interior_rgb(self, r: int, g: int, b: int):
        with self._lock:
            self.interior_color = (max(0, min(255, int(r))),
                                  max(0, min(255, int(g))),
                                  max(0, min(255, int(b))))

    def set_interior_mode(self, mode: str):
        with self._lock:
            self.interior_mode = mode.upper()

    def _animation_loop(self):
        blink_state = False
        while self.running:
            with self._lock:
                self._render_front(blink_state)
                self._render_interior()
                self._render_back(blink_state)
            if IS_HARDWARE and not isinstance(self.strip, MockPixelStrip):
                try:
                    self.strip.show()
                except Exception:
                    pass

            blink_state = not blink_state
            self.anim_step = (self.anim_step + 1) % 256
            time.sleep(0.35)

    def _render_front(self, blink):
        start = 0
        end = LEDS_FRONT_COUNT
        turn = self.turn_signal_state
        amber = Color(255, 150, 0)
        white = Color(255, 255, 255)
        off = Color(0, 0, 0)

        for i in range(start, end):
            is_left = (i == start)
            is_right = (i == end - 1)

            if is_left and turn in ["LEFT", "HAZARD"]:
                self.strip.setPixelColor(i, amber if blink else off)
            elif is_right and turn in ["RIGHT", "HAZARD"]:
                self.strip.setPixelColor(i, amber if blink else off)
            else:
                self.strip.setPixelColor(i, white if self.front_enabled else off)

    def _render_interior(self):
        start = LEDS_FRONT_COUNT
        end = start + LEDS_INTERIOR_COUNT
        off = Color(0, 0, 0)

        if not self.interior_enabled:
            for i in range(start, end):
                self.strip.setPixelColor(i, off)
            return

        r, g, b = self.interior_color
        if self.interior_mode == "SOLID":
            c = Color(r, g, b)
            for i in range(start, end):
                self.strip.setPixelColor(i, c)
        elif self.interior_mode == "BREATHE":
            factor = (math.sin(self.anim_step * 0.15) + 1.0) / 2.0
            c = Color(int(r * factor), int(g * factor), int(b * factor))
            for i in range(start, end):
                self.strip.setPixelColor(i, c)
        elif self.interior_mode == "RAINBOW":
            span = max(1, end - start)
            for i in range(start, end):
                pixel_hue = ((i - start) * 256 // span) + (self.anim_step * 6)
                self.strip.setPixelColor(i, self._wheel(pixel_hue & 255))

    def _render_back(self, blink):
        start = LEDS_FRONT_COUNT + LEDS_INTERIOR_COUNT
        end = LED_TOTAL
        turn = self.turn_signal_state
        amber = Color(255, 150, 0)
        red = Color(255, 0, 0)
        off = Color(0, 0, 0)

        for i in range(start, end):
            is_left = (i < start + 2)
            is_right = (i >= end - 2)

            if is_left and turn in ["LEFT", "HAZARD"]:
                self.strip.setPixelColor(i, amber if blink else off)
            elif is_right and turn in ["RIGHT", "HAZARD"]:
                self.strip.setPixelColor(i, amber if blink else off)
            else:
                self.strip.setPixelColor(i, red if self.back_enabled else off)

    def _wheel(self, pos):
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    def stop(self):
        self.running = False
        if IS_HARDWARE and not isinstance(self.strip, MockPixelStrip):
            try:
                off = Color(0, 0, 0)
                for i in range(self.strip.numPixels()):
                    self.strip.setPixelColor(i, off)
                self.strip.show()
            except Exception:
                pass
