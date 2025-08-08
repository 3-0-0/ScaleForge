
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import os
from .detector import load_caps, detect_gpu_caps, BackendType
from . import detector

def get_backend(force_probe: bool = False) -> Tuple[Any, Dict[str, Any]]:
    """Get the appropriate backend instance with capability info.
    
    Args:
        force_probe: If True, ignores cache and performs fresh detection
        
    Returns:
        Tuple of (backend_instance, capability_info)
        capability_info includes:
            - vendor: str
            - backend: str
            - source: "cached"|"probed"
            - caps: dict of capabilities
    """
    # Resolve APP_ROOT (simplified for now - will enhance with config loader)
    app_root = Path(os.getenv("APP_ROOT", "."))
    
    # Check for environment override
    env_backend = os.getenv("SCALEFORGE_BACKEND") or os.getenv("FORCE_BACKEND")
    if env_backend and env_backend in ["torch-cuda", "torch-rocm", "torch-cpu", "ncnn-vulkan"]:
        backend_type = env_backend
        caps = {
            "vendor": "override",
            "backend": backend_type,
            "source": "env",
            "caps": {}
        }
    else:
        # Load or detect capabilities
        caps_data = load_caps(app_root)
        if force_probe or not caps_data:
            caps_data = detect_gpu_caps(app_root, force_probe=True)
            source = "probed"
        else:
            source = "cached"
        
        backend_type = caps_data["backend"]
        caps = {
            "vendor": caps_data["vendor"],
            "backend": backend_type,
            "source": source,
            "caps": {
                "max_tile_size": caps_data["max_tile_size"],
                "max_megapixels": caps_data["max_megapixels"]
            }
        }
    
    # Instantiate the appropriate backend
    if backend_type == "torch-cuda":
        from .torch_backend import CUDABackend
        backend = CUDABackend()
    elif backend_type == "torch-rocm":
        from .torch_backend import ROCmBackend
        backend = ROCmBackend()
    elif backend_type == "ncnn-vulkan":
        from .ncnn_backend import VulkanBackend
        backend = VulkanBackend()
    else:  # torch-cpu
        from .torch_backend import CPUBackend
        backend = CPUBackend()
    
    return backend, caps
