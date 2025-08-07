"""Real-ESRGAN Torch back-end.

Downloads the RealESRGAN ×4 model into a cache directory
(`~/.cache/scaleforge/models` or `$SCALEFORGE_CACHE`) and exposes a simple
`upscale()` coroutine.

Heavy dependencies (`torch`, `realesrgan`) are imported lazily so CI can run the
module without installing GPU wheels.
"""
from __future__ import annotations

import hashlib
import importlib
import os
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from scaleforge.backend.base import Backend

if TYPE_CHECKING:  # pragma: no cover – type hints only
    from scaleforge.core.job import Job  # noqa: F401 – forward reference


class TorchRealESRGANBackend(Backend):
    """Real-ESRGAN ×4 back-end powered by PyTorch."""

    name = "torch-realesrgan"

    _MODEL_FILE = "RealESRGAN_x4plus.pth"
    _MODEL_SHA256 = (
        "4df1882840bb64721e0fe63095c049f77b0934d263528b91c04e2193c25e0b70"
    )
    _URL = (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.2.5.0/RealESRGAN_x4plus.pth"
    )

    # ------------------------------------------------------------------
    # Life-cycle
    # ------------------------------------------------------------------
    def __init__(self, *, prefer_gpu: bool = True) -> None:  # noqa: D401 – simple
        torch = self._lazy_import("torch")
        realesrgan_mod = self._lazy_import("realesrgan")

        device = "cuda" if prefer_gpu and torch.cuda.is_available() else "cpu"
        model_path = self._ensure_model()

        self._upsampler = realesrgan_mod.RealESRGAN(device=device, scale=4)
        self._upsampler.load_weights(str(model_path))

    # ------------------------------------------------------------------
    # Backend API – required by :class:`~scaleforge.backend.base.Backend`.
    # ------------------------------------------------------------------
    async def upscale(  # type: ignore[override] – base declares async
        self,
        src: Path,
        dst: Path,
        *,
        scale: int = 4,
        tile: int | None = None,
        job: "Job" | None = None,  # noqa: D401 – future use
    ) -> None:
        """Upscale *src* to *dst*.

        Parameters
        ----------
        src, dst
            Input and output paths.
        scale
            Ignored for now – always ×4 (Real-ESRGAN model is fixed).
        tile, job
            Reserved for future improvements.
        """
        img = Image.open(src).convert("RGB")
        result = self._upsampler.predict(img)
        dst.parent.mkdir(parents=True, exist_ok=True)
        result.save(dst)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ensure_model(self) -> Path:
        """Return path to the model file, downloading if missing/invalid."""
        cache_dir = Path(os.getenv("SCALEFORGE_CACHE", "~/.cache/scaleforge/models")).expanduser()
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_path = cache_dir / self._MODEL_FILE

        if not model_path.exists() or self._sha256(model_path) != self._MODEL_SHA256:
            self._download(self._URL, model_path)
            if self._sha256(model_path) != self._MODEL_SHA256:  # pragma: no cover
                raise RuntimeError("Model checksum verification failed")
        return model_path

    # ------------------------------------------------------------------
    # Static utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _sha256(path: Path) -> str:
        hash_obj = hashlib.sha256()
        with open(path, "rb") as fp:
            for chunk in iter(lambda: fp.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    @staticmethod
    def _download(url: str, dest: Path) -> None:  # pragma: no cover – network
        tmp = dest.with_suffix(".tmp")
        with urllib.request.urlopen(url) as response, open(tmp, "wb") as fp:
            fp.write(response.read())
        tmp.rename(dest)

    @staticmethod
    def _lazy_import(name: str):
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                f"{name} is required for the Torch back-end. Install with "
                "`pip install torch realesrgan pillow`."
            ) from exc

# ------------------------------------------------------------------
# Backwards-compatibility shim – accepts historical ``stub`` argument.
# ------------------------------------------------------------------

class TorchBackend(TorchRealESRGANBackend):  # noqa: D401, N801
    """Alias kept so legacy import paths keep working during Sprint-3.

    The *stub* argument is ignored; tests can still stub heavy dependencies via
    environment variables or monkeypatching.
    """

    def __init__(self, stub: bool = False, **kwargs):  # noqa: D401 – simple
        super().__init__(**kwargs)



