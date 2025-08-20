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
