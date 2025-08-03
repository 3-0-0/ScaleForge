
"""Settings I/O utilities for ScaleForge GUI."""
import json
from pathlib import Path
from typing import Dict, Any

SETTINGS_FILE = Path(".scaleforge/settings.json")

DEFAULT_SETTINGS = {
    "output_path": "",
    "input_path": "",
    "resolution": "512x512",
    "dry_run": False,
    "window_size": [800, 600]
}

def load_settings() -> Dict[str, Any]:
    """Load settings from JSON file with error handling."""
    try:
        if not SETTINGS_FILE.exists():
            return DEFAULT_SETTINGS
            
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)
            
        # Validate and merge with defaults
        return {**DEFAULT_SETTINGS, **settings}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load settings - {e}. Using defaults.")
        return DEFAULT_SETTINGS

def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to JSON file with error handling."""
    try:
        SETTINGS_FILE.parent.mkdir(exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except (IOError, TypeError) as e:
        print(f"Warning: Failed to save settings - {e}")
