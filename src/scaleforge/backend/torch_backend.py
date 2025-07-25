"""Torch backend with optional Pillow stub.

If Real-ESRGAN + general-x2v3 model is available we will use it; otherwise we
fallback to a simple Pillow BICUBIC resize (scale=2) so the rest of the
pipeline can be tested.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from PIL import Image

from scaleforge.backend.base import Backend, BackendError

logger = logging.getLogger(__name__)


class TorchBackend(Backend):
    """Torch Real-ESRGAN backend (with stub)."""

    name = "torch"

    def __init__(self, *, stub: bool = False):
        self._use_stub = stub
        self._realesrgan = None
        if not stub:
            try:
                from realesrgan import RealESRGAN  # noqa: WPS433 (optional import)
                import torch

                self._realesrgan = RealESRGAN(
                    device="cuda" if torch.cuda.is_available() else "cpu",
                    scale=2,
                )
                # Load tiny model – resolves to ~20 MB download on first use
                self._realesrgan.download_weights("v3-small")
                self._realesrgan.model.half()
                logger.info("Real-ESRGAN model loaded")
            except ModuleNotFoundError as exc:
                logger.warning("Real-ESRGAN deps missing – using stub (%s)", exc)
                self._use_stub = True

    async def upscale(self, src: Path, dst: Path, scale: int = 2, tile: int | None = None):  # noqa: D401
        """Upscale single image asynchronously."""
        if self._use_stub or self._realesrgan is None:
            await asyncio.to_thread(self._stub_resize, src, dst)
        else:
            await asyncio.to_thread(self._esrgan_resize, src, dst)

    # ---------------------------------------------------------------------
    # helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _stub_resize(src: Path, dst: Path):
        img = Image.open(src).convert("RGB")
        w, h = img.size
        logger.debug("Stub upscale %s → %s", src, dst)
        resized = img.resize((w * 2, h * 2), Image.BICUBIC)
        resized.save(dst, format="PNG")

    def _esrgan_resize(self, src: Path, dst: Path):
        if self._realesrgan is None:  # pragma: no cover – guard
            raise BackendError("Real-ESRGAN backend not initialised")
        import torch

        img = Image.open(src).convert("RGB")
        sr_image = self._realesrgan.predict(img)
        sr_image.save(dst)
        torch.cuda.empty_cache()
