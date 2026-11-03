import json
import os
from config import KEY_FILE, SETTINGS_FILE, DEFAULT_PIN


class StorageManager:
    """Manages persistent storage for NFC authorized keys and user preferences."""

    DEFAULT_SETTINGS = {
        "pin": DEFAULT_PIN,
        "interior_rgb": [0, 0, 255],
        "interior_mode": "SOLID",
    }

    def __init__(self, key_file=KEY_FILE, settings_file=SETTINGS_FILE):
        self.key_file = key_file
        self.settings_file = settings_file
        self.authorized_keys = self.load_authorized_keys()
        self.settings = self.load_settings()

    # --- NFC KEY MANAGEMENT ---
    def load_authorized_keys(self):
        keys = []
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "r", encoding="utf-8") as f:
                    for line in f:
                        cleaned = line.strip()
                        if cleaned and cleaned not in keys:
                            keys.append(cleaned)
            except OSError as e:
                print(f"Warning: Could not read {self.key_file}: {e}")
        return keys

    def add_authorized_key(self, new_id):
        key_str = str(new_id).strip()
        if not key_str or key_str in self.authorized_keys:
            return False
        self.authorized_keys.append(key_str)
        self._write_keys()
        return True

    def delete_authorized_key(self, key_to_remove):
        key_str = str(key_to_remove).strip()
        if key_str in self.authorized_keys:
            self.authorized_keys.remove(key_str)
            self._write_keys()
            return True
        return False

    def is_key_authorized(self, scanned_id):
        key_str = str(scanned_id).strip()
        # If no keys exist at all, allow any key for first-time onboarding
        if not self.authorized_keys:
            return True
        return key_str in self.authorized_keys

    def _write_keys(self):
        try:
            with open(self.key_file, "w", encoding="utf-8") as f:
                for k in self.authorized_keys:
                    f.write(f"{k}\n")
        except OSError as e:
            print(f"Error writing {self.key_file}: {e}")

    # --- USER SETTINGS MANAGEMENT ---
    def load_settings(self):
        data = dict(self.DEFAULT_SETTINGS)
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data.update(loaded)
            except (OSError, ValueError) as e:
                print(f"Warning: Could not load settings ({e}), using defaults.")
        return data

    def save_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except OSError as e:
            print(f"Error saving settings: {e}")

    @property
    def pin(self):
        return str(self.settings.get("pin", DEFAULT_PIN))

    def set_pin(self, new_pin):
        self.settings["pin"] = str(new_pin).strip()
        self.save_settings()

    @property
    def interior_rgb(self):
        rgb = self.settings.get("interior_rgb", [0, 0, 255])
        if isinstance(rgb, (list, tuple)) and len(rgb) == 3:
            return tuple(max(0, min(255, int(c))) for c in rgb)
        return (0, 0, 255)

    def set_interior_rgb(self, r, g, b):
        self.settings["interior_rgb"] = [int(r), int(g), int(b)]
        self.save_settings()

    @property
    def interior_mode(self):
        return str(self.settings.get("interior_mode", "SOLID"))

    def set_interior_mode(self, mode):
        self.settings["interior_mode"] = str(mode)
        self.save_settings()

