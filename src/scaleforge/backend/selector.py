"""Backend auto-selector.

Chooses the most suitable backend based on environment, GPU availability, and
user overrides. For the MVP we only switch between TorchBackend (optionally
stubbed) and a placeholder VulkanBackend.
"""
from __future__ import annotations

import logging
import os

from scaleforge.backend.base import Backend, VulkanBackend
from scaleforge.backend.torch_backend import TorchBackend
from scaleforge.capabilities import get_caps

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

    # Handle explicit overrides first
    if override in {"torch", "pytorch"}:
        logger.info("Backend forced to Torch (override)")
        return TorchBackend(stub=use_stub)
    if override == "vulkan":
        logger.info("Backend forced to Vulkan (override)")
        return VulkanBackend()

    # Use capability-aware selection
    caps = get_caps()
    logger.info(f"Detected capabilities: {caps}")

    if caps.device_type == "cuda":
        logger.info("Using CUDA-optimized Torch backend")
        return TorchBackend(stub=use_stub)
    elif caps.device_type == "mps":
        logger.info("Using MPS-optimized Torch backend")
        return TorchBackend(stub=use_stub)
    elif caps.device_type == "vulkan":
        logger.info("Using Vulkan backend")
        return VulkanBackend()
    else:
        logger.info("Using CPU fallback backend")
        return TorchBackend(stub=use_stub)
