
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
import platform
import subprocess
from datetime import datetime

def detect_gpu_vendor() -> str:
    """Detect GPU vendor (nvidia/amd/intel)."""
    system = platform.system()
    if system == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True,
                text=True,
                check=True
            )
            if "nvidia" in result.stdout.lower():
                return "nvidia"
            if "amd" in result.stdout.lower():
                return "amd"
        except Exception:
            pass
    elif system == "Linux":
        try:
            # First try nvidia-smi
            subprocess.run(["nvidia-smi"], capture_output=True, check=True)
            return "nvidia"
        except Exception:
            try:
                # Fall back to lspci for AMD detection
                result = subprocess.run(
                    ["lspci"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if "amd" in result.stdout.lower() or "ati" in result.stdout.lower():
                    return "amd"
            except Exception:
                pass
    return "unknown"

def detect_gpu_caps(app_root: Path, force_probe: bool = False) -> Dict[str, Any]:
    """Detect GPU capabilities with optional caching."""
    if not force_probe:
        cached = load_caps(app_root)
        if cached:
            return cached
            
    vendor = detect_gpu_vendor()
    return {
        "vendor": vendor,
        "backend": "torch-cpu",  # Default fallback
        "max_tile_size": 256,
        "max_megapixels": 64.0,
        "detected_at": datetime.now().isoformat()
    }

def load_caps(app_root: Path) -> Dict[str, Any]:
    """Load cached GPU capabilities."""
    cache_file = app_root / "gpu_caps.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            pass
    return {}

def save_caps(app_root: Path, caps: Dict[str, Any]) -> None:
    """Save GPU capabilities to cache."""
    app_root.mkdir(parents=True, exist_ok=True)
    (app_root / "gpu_caps.json").write_text(json.dumps(caps))

__all__ = ["detect_gpu_vendor", "detect_gpu_caps", "load_caps", "save_caps"]
