"""Backend auto-selector.

Chooses the most suitable backend based on environment, GPU availability, and
user overrides. For the MVP we only switch between TorchBackend (optionally
stubbed) and a placeholder VulkanBackend.
"""
from __future__ import annotations

import logging
import os

from scaleforge.backend.base import Backend
from scaleforge.backend.vulkan_backend import VulkanBackend
from scaleforge.backend.torch_backend import TorchBackend

logger = logging.getLogger(__name__)

ENV_FORCE = ("FORCE_BACKEND", "SCALEFORGE_BACKEND")


def _env_override() -> str | None:
    for key in ENV_FORCE:
        val = os.getenv(key)
        if val:
            return val.lower()
    return None


def get_backend() -> Backend:
    """Return a Backend instance following the selection rules."""

    use_stub = os.getenv("SF_STUB_UPSCALE", "0") == "1"

    override = _env_override()
    if override in {"torch", "pytorch"}:
        logger.info("Backend forced to Torch (override)")
        return TorchBackend(stub=use_stub)
    if override == "vulkan":
        logger.info("Backend forced to Vulkan (override)")
        return VulkanBackend()

    try:
        import torch  # noqa: WPS433 (dynamic import)

        if torch.cuda.is_available():
            logger.info("Detected CUDA – using Torch backend")
        else:
            logger.info("Torch CPU – using Torch backend")
        return TorchBackend(stub=use_stub)
    except ModuleNotFoundError:  # pragma: no cover – unlikely
        logger.warning("PyTorch not installed – defaulting to Vulkan stub")
        return VulkanBackend()

from .caps import GPUCapabilityCache

def get_backend(config):
    caps_cache = GPUCapabilityCache(config.APP_ROOT)
    cached_caps = caps_cache.load()
    
    if cached_caps:
        return _select_backend_based_on_caps(cached_caps)
    
    # Run minimal probe if no cache
    probe_result = _run_preflight_probe()
    caps_cache.save(probe_result['max_tile'], probe_result['max_pixels'])
    return _select_backend_based_on_caps(probe_result)

from .caps import GPUCapabilityCache

def get_backend(config):
    caps_cache = GPUCapabilityCache(config.APP_ROOT)
    cached_caps = caps_cache.load()
    
    if cached_caps:
        return _select_backend_based_on_caps(cached_caps)
    
    # Run minimal probe if no cache
    probe_result = _run_preflight_probe()
    caps_cache.save(probe_result['max_tile'], probe_result['max_pixels'])
    return _select_backend_based_on_caps(probe_result)
from .probe import run_preflight_probe

def _is_mobile_vulkan_supported():
    """Check for mobile-friendly Vulkan implementation"""
    import platform
    if platform.system() == 'Linux':
        # Check for ARM architecture (common in mobile)
        return 'aarch64' in platform.machine()
    return False
