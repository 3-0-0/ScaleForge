
"""ScaleForge backend module - handles GPU detection and backend selection."""

from .detector import (
    detect_gpu_vendor,
    detect_gpu_caps,
    detect_backend,
    get_backend_debug_info,
    BackendType
)
from .selector import get_backend

__all__ = [
    'detect_gpu_vendor',
    'detect_gpu_caps',
    'detect_backend',
    'get_backend_debug_info',
    'get_backend',
    'BackendType'
]
