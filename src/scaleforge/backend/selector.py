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


def get_backend(model_name: str | None = None) -> Backend:
    """Return a Backend instance following the selection rules.
    
    Args:
        model_name: Optional model name to load. Supported values:
            - 'realesr-general-x4v3' (default)
            - 'realesrgan-x4plus'
            - 'realesr-animevideov3'
    """

    use_stub = os.getenv("SF_STUB_UPSCALE", "0") == "1"

    override = _env_override()
    if override:
        backend_name = override
        logger.info("Backend forced to %s (override)", backend_name)
    else:
        from scaleforge.backend.detector import detect_backend

        backend_name = detect_backend()
        logger.info("Auto-detected backend %s", backend_name)

    torch_backends = {"torch-cuda", "torch-rocm", "torch-mps", "torch-cpu"}
    if backend_name in torch_backends:
        logger.info("Using Torch backend (%s)", backend_name)
        return TorchBackend(model_name=model_name, stub=use_stub)

    if "vulkan" in backend_name:
        logger.info("Using Vulkan backend (%s)", backend_name)
        return VulkanBackend()

    logger.warning("Unknown backend '%s' – defaulting to Vulkan backend", backend_name)
    return VulkanBackend()
