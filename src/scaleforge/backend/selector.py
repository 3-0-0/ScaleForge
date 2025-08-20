"""Backend auto-selector.
Chooses the most suitable backend based on environment, GPU availability,
and user overrides. For the MVP we only switch between TorchBackend (optionally
stubbed) and a placeholder VulkanBackend.
"""
from __future__ import annotations

import logging
import os
import warnings

from scaleforge.backend.base import Backend
from scaleforge.backend.spec import BackendSpec, parse_alias
from scaleforge.backend.torch_backend import TorchBackend
from scaleforge.backend.vulkan_backend import VulkanBackend

logger = logging.getLogger(__name__)

LEGACY_MAP = {
    "cpu": "cpu-pillow",
    "torch-cpu": "torch-eager-cpu",
    "torch-cuda": "torch-eager-cuda",
    "torch-rocm": "torch-eager-rocm",
    "torch-mps": "torch-eager-mps",
    "ncnn": "ncnn-ncnn-cpu",
    "ncnn-vulkan": "ncnn-ncnn-vulkan",
}


def _alias_to_spec(alias: str, debug: bool) -> tuple[BackendSpec, list[str]]:
    alias = alias.lower()
    reasons: list[str] = []
    if alias == "torch":
        warnings.warn("Legacy backend alias 'torch'", DeprecationWarning, stacklevel=2)
        from scaleforge.backend.detector import detect_backend as _detect

        spec, det_reasons = _detect(debug=debug)
        reasons.append("legacy alias 'torch'")
        reasons.extend(det_reasons)
        return spec, reasons
    if alias in LEGACY_MAP:
        warnings.warn(f"Legacy backend alias '{alias}'", DeprecationWarning, stacklevel=2)
        canonical = LEGACY_MAP[alias]
        reasons.append(f"legacy '{alias}' -> '{canonical}'")
        return parse_alias(canonical), reasons
    return parse_alias(alias), reasons


def get_backend_alias(backend: str | BackendSpec | None = None, *, debug: bool = False) -> tuple[str, list[str]]:
    """Return canonical backend alias and reasons."""
    reasons: list[str] = []
    env_backend = os.getenv("SCALEFORGE_BACKEND")
    if env_backend:
        spec, r = _alias_to_spec(env_backend, debug)
        reasons.append(f"SCALEFORGE_BACKEND={env_backend}")
        reasons.extend(r)
        return spec.alias, reasons

    if backend is not None:
        if isinstance(backend, BackendSpec):
            spec = backend
        else:
            spec, r = _alias_to_spec(backend, debug)
            reasons.extend(r)
    else:
        from scaleforge.backend.detector import detect_backend as _detect

        spec, det_reasons = _detect(debug=debug)
        reasons.extend(det_reasons)

    device_override = os.getenv("SCALEFORGE_DEVICE")
    if device_override:
        spec = BackendSpec(spec.vendor, spec.engine, device_override)
        reasons.append(f"SCALEFORGE_DEVICE={device_override}")

    return spec.alias, reasons


def detect_backend(debug: bool = False) -> tuple[BackendSpec, list[str]]:
    alias, reasons = get_backend_alias(debug=debug)
    return parse_alias(alias), reasons


def get_backend(
    model_name: str | None = None,
    backend: str | BackendSpec | None = None,
) -> Backend:
    """Return a Backend instance following the selection rules."""
    use_stub = os.getenv("SF_STUB_UPSCALE", "0") == "1"
    alias, _reasons = get_backend_alias(backend)
    if alias.startswith("torch-"):
        logger.info("Using Torch backend (%s)", alias)
        return TorchBackend(model_name=model_name, stub=use_stub)
    if "vulkan" in alias or alias.startswith("ncnn-"):
        logger.info("Using Vulkan backend (%s)", alias)
        return VulkanBackend()
    logger.warning("Unknown backend '%s' – defaulting to Vulkan backend", alias)
    return VulkanBackend()
