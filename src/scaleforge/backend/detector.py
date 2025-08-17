from __future__ import annotations

def get_gpu_info() -> dict:
    try:
        from scaleforge.backend.selector import get_gpu_info as _impl  # type: ignore
        return _impl()
    except Exception:
        info = {"vendor": "cpu", "cuda": False, "rocm": False, "mps": False}
        try:
            import torch  # type: ignore
            info["vendor"] = "nvidia" if torch.cuda.is_available() else "cpu"
            info["cuda"] = bool(torch.cuda.is_available())
        except Exception:
            pass
        return info

def detect_backend(debug: bool = False) -> str:
    try:
        from scaleforge.backend.selector import detect_backend as _impl  # type: ignore
        return _impl(debug=debug)
    except Exception:
        info = get_gpu_info()
        if info.get("cuda"): return "torch-cuda"
        if info.get("rocm"): return "torch-rocm" 
        if info.get("mps"):  return "torch-mps"
        return "torch-cpu"

from pathlib import Path
import json

def detect_gpu_vendor() -> str:
    v = get_gpu_info().get("vendor", "cpu")
    return {"nvidia": "nvidia", "amd": "amd", "apple": "apple"}.get(v, v)

def detect_gpu_caps(debug: bool = False) -> dict:
    info = get_gpu_info()
    return {
        "backend": detect_backend(debug),
        "vendor":  info.get("vendor", "cpu"),
        "cuda":    bool(info.get("cuda")),
        "rocm":    bool(info.get("rocm")),
        "mps":     bool(info.get("mps")),
        "source":  "auto" if not debug else "auto-debug",
    }

def load_caps(path: str | Path) -> dict:
    with open(Path(path), "r", encoding="utf-8") as f:
        return json.load(f)

def save_caps(caps: dict, path: str | Path) -> None:
    with open(Path(path), "w", encoding="utf-8") as f:
        json.dump(caps, f, indent=2, sort_keys=True)
