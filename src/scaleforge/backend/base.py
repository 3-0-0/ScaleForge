"""Backend interface."""

from __future__ import annotations

import abc
from pathlib import Path



class BackendError(RuntimeError):
    pass


class Backend(abc.ABC):
    name: str

    @abc.abstractmethod
    async def upscale(self, src: Path, dst: Path, scale: int = 2, tile: int | None = None) -> None:  # noqa: D401
        """Upscale one image from src to dst."""


class TorchBackend(Backend):
    name = "torch"

    async def upscale(self, src: Path, dst: Path, scale: int = 2, tile: int | None = None):  # noqa: D401
        # TODO: implement actual Real-ESRGAN torch inference
        dst.write_bytes(src.read_bytes())


class VulkanBackend(Backend):
    name = "vulkan"

    async def upscale(self, src: Path, dst: Path, scale: int = 2, tile: int | None = None):  # noqa: D401
        # TODO: call ncnn vulkan executable via asyncio.subprocess
        dst.write_bytes(src.read_bytes())
