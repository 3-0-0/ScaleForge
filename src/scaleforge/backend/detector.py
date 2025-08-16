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
        msg = f"backend=CPU (fallback) info={info}"
        return ("[debug] " + msg) if debug else msg
