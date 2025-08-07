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
    if override in {"torch", "pytorch"}:
        logger.info("Backend forced to Torch (override)")
        return TorchBackend(model_name=model_name, stub=use_stub)
    if override == "vulkan":
        logger.info("Backend forced to Vulkan (override)")
        return VulkanBackend(model_name=model_name)

    try:
        import torch  # noqa: WPS433 (dynamic import)

        if torch.cuda.is_available():
            logger.info("Detected CUDA – using Torch backend")
        else:
            logger.info("Torch CPU – using Torch backend")
        return TorchBackend(model_name=model_name, stub=use_stub)
    except ModuleNotFoundError:  # pragma: no cover – unlikely
        logger.warning("PyTorch not installed – defaulting to Vulkan stub")
        return VulkanBackend(model_name=model_name)
