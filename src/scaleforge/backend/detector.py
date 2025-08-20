from __future__ import annotations

from scaleforge.backend.spec import BackendSpec
from pathlib import Path
import json


def get_gpu_info() -> dict:
    try:
        from scaleforge.backend.selector import get_gpu_info as _impl  # type: ignore
        return _impl()
    except ImportError:
        info = {"vendor": "cpu", "cuda": False, "rocm": False, "mps": False}
        try:
            import torch  # type: ignore

            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_built() and torch.backends.mps.is_available():
                info["vendor"] = "apple"
                info["mps"] = True
            elif getattr(torch.version, "hip", None) and torch.cuda.is_available():
                info["vendor"] = "amd"
                info["rocm"] = True
            elif getattr(torch.version, "cuda", None) and torch.cuda.is_available():
                info["vendor"] = "nvidia"
                info["cuda"] = True
            info["torch"] = True
        except (ImportError, AttributeError, RuntimeError):
            info["torch"] = False
        return info


def detect_backend(debug: bool = False) -> tuple[BackendSpec, list[str]]:
    """Detect the most appropriate backend and return ``BackendSpec`` and reasons."""
    info = get_gpu_info()
    reasons: list[str] = []

    has_torch = info.get("torch", False)
    if has_torch and info.get("cuda"):
        reasons.append("CUDA available")
        return BackendSpec("torch", "eager", "cuda"), reasons
    if has_torch and info.get("rocm"):
        reasons.append("ROCm available")
        return BackendSpec("torch", "eager", "rocm"), reasons
    if has_torch and info.get("mps"):
        reasons.append("MPS available")
        return BackendSpec("torch", "eager", "mps"), reasons

    try:
        from scaleforge.backend.vulkan_backend import VulkanBackend

        if VulkanBackend().is_available():
            reasons.append("Vulkan binary available")
            return BackendSpec("ncnn", "ncnn", "vulkan"), reasons
        reasons.append("Vulkan binary not found")
    except Exception:  # pragma: no cover - rare
        reasons.append("Vulkan check failed")

    if has_torch:
        reasons.append("No GPU found; using CPU")
        return BackendSpec("torch", "eager", "cpu"), reasons

    reasons.append("torch not installed; falling back to Pillow")
    return BackendSpec("cpu", "pillow"), reasons

def detect_gpu_vendor() -> str:
    v = get_gpu_info().get("vendor", "cpu")
    return {"nvidia": "nvidia", "amd": "amd", "apple": "apple"}.get(v, v)


def detect_gpu_caps(debug: bool = False) -> dict:
    info = get_gpu_info()
    spec, _reasons = detect_backend(debug)
    return {
        "backend": spec.alias,
        "vendor": info.get("vendor", "cpu"),
        "cuda": bool(info.get("cuda")),
        "rocm": bool(info.get("rocm")),
        "mps": bool(info.get("mps")),
        "source": "auto-debug" if debug else "auto",
    }

def load_caps(path: str | Path) -> dict:
    with open(Path(path), "r", encoding="utf-8") as f:
        return json.load(f)

def save_caps(caps: dict, path: str | Path) -> None:
    with open(Path(path), "w", encoding="utf-8") as f:
        json.dump(caps, f, indent=2, sort_keys=True)
