
"""GPU capability caching and preflight checks."""
import json
import logging
from pathlib import Path

CACHE_FILE = Path("${APP_ROOT}") / "data" / "gpu_caps.json"
DEFAULT_CAPS = {
    "max_tile": 512,
    "max_pixels": 8192 * 8192
}

def _run_preflight_probe() -> dict:
    """Run GPU capability probe and return cached/stubbed results."""
    logging.info("Running GPU preflight probe")
    return DEFAULT_CAPS

def load_cached_caps() -> dict:
    """Load cached GPU capabilities with fallback to probe."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Failed to load GPU cache: {e}")
    
    return _run_preflight_probe()

def save_caps_to_cache(caps: dict):
    """Save GPU capabilities to cache file."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(caps, f)
    except IOError as e:
        logging.error(f"Failed to save GPU cache: {e}")
