
"""GPU/CPU capability detection and caching."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch

logger = logging.getLogger(__name__)

@dataclass
class DeviceCapabilities:
    """Stores detected hardware capabilities."""
    device_type: str  # 'cuda', 'mps', 'vulkan', 'cpu'
    vram_mb: int
    max_tile_size: int
    half_precision: bool

def detect_capabilities() -> DeviceCapabilities:
    """Detect current system's capabilities."""
    if torch.cuda.is_available():
        return _detect_cuda_capabilities()
    elif getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available():
        return _detect_mps_capabilities()
    elif torch.backends.vulkan.is_available():
        return _detect_vulkan_capabilities()
    return _detect_cpu_capabilities()

def _detect_cuda_capabilities() -> DeviceCapabilities:
    """Detect CUDA GPU capabilities."""
    vram_mb = torch.cuda.get_device_properties(0).total_memory // (1024**2)
    return DeviceCapabilities(
        device_type='cuda',
        vram_mb=vram_mb,
        max_tile_size=_calculate_max_tile_size(vram_mb),
        half_precision=torch.cuda.is_bf16_supported()
    )

def _detect_mps_capabilities() -> DeviceCapabilities:
    """Detect MPS (Apple Silicon) capabilities."""
    return DeviceCapabilities(
        device_type='mps',
        vram_mb=16384,  # Conservative estimate
        max_tile_size=2048,
        half_precision=True
    )

def _detect_vulkan_capabilities() -> DeviceCapabilities:
    """Detect Vulkan capabilities."""
    return DeviceCapabilities(
        device_type='vulkan',
        vram_mb=4096,  # Conservative estimate
        max_tile_size=1024,
        half_precision=False
    )

def _detect_cpu_capabilities() -> DeviceCapabilities:
    """Detect CPU fallback capabilities."""
    return DeviceCapabilities(
        device_type='cpu',
        vram_mb=0,
        max_tile_size=512,
        half_precision=False
    )

def _calculate_max_tile_size(vram_mb: int) -> int:
    """Heuristic to determine max tile size based on VRAM."""
    if vram_mb >= 16000: return 4096
    if vram_mb >= 8000: return 2048
    if vram_mb >= 4000: return 1024
    return 512

def get_caps(
    base_dir: Optional[str] = None,
    prefer: str = "auto",
    force_redetect: bool = False
) -> DeviceCapabilities:
    """Get cached capabilities or detect fresh if needed/forced."""
    cache_path = _get_cache_path(base_dir)
    
    if not force_redetect and cache_path.exists():
        try:
            with open(cache_path) as f:
                data = json.load(f)
                return DeviceCapabilities(**data)
        except Exception as e:
            logger.warning(f"Failed to load capabilities cache: {e}")

    caps = detect_capabilities()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(caps.__dict__, f)
    return caps

def _get_cache_path(base_dir: Optional[str] = None) -> Path:
    """Get path to capabilities cache file."""
    cache_dir = Path(base_dir or os.getenv("SCALEFORGE_CACHE", "~/.cache/scaleforge"))
    return cache_dir.expanduser() / "gpu_caps.json"
