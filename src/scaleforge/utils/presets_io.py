
"""Resolution presets I/O utilities for ScaleForge."""
import json
from pathlib import Path
from typing import List, Dict

PRESETS_FILE = Path(".scaleforge/presets.json")

DEFAULT_PRESETS = [
    {"label": "512x512", "width": 512, "height": 512},
    {"label": "1024x1024", "width": 1024, "height": 1024},
    {"label": "1920x1080", "width": 1920, "height": 1080},
    {"label": "3840x2160", "width": 3840, "height": 2160}
]

def load_presets() -> List[Dict]:
    """Load resolution presets from JSON file with error handling."""
    try:
        if not PRESETS_FILE.exists():
            return DEFAULT_PRESETS
            
        with open(PRESETS_FILE) as f:
            presets = json.load(f)
            
        # Validate presets structure
        if not all(isinstance(p, dict) and 
                  {'label', 'width', 'height'}.issubset(p.keys())
                  for p in presets):
            raise ValueError("Invalid presets structure")
            
        return presets
    except (json.JSONDecodeError, IOError, ValueError) as e:
        print(f"Warning: Failed to load presets - {e}. Using defaults.")
        return DEFAULT_PRESETS

def save_presets(presets: List[Dict]) -> None:
    """Save resolution presets to JSON file with error handling."""
    try:
        PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PRESETS_FILE, 'w') as f:
            json.dump(presets, f, indent=2)
    except (IOError, TypeError) as e:
        print(f"Warning: Failed to save presets - {e}")
