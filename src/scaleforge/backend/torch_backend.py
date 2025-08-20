"""Real-ESRGAN Torch backend.

This module provides a lightweight wrapper around the `realesrgan` project.
Model weights are downloaded on demand and cached under
``~/.cache/scaleforge/models`` (or ``$SCALEFORGE_CACHE``). Heavy dependencies
such as :mod:`torch` are imported lazily so the module can be imported on
systems without GPU wheels installed.
"""

from __future__ import annotations

import hashlib
import importlib
import logging
import os
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

try:  # pragma: no cover - optional dependency
    from basicsr.archs.rrdbnet_arch import RRDBNet  # type: ignore
except Exception:  # pragma: no cover - basicsr not installed
    RRDBNet = None  # type: ignore[assignment]

from PIL import Image

from scaleforge.backend.base import Backend

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - forward reference only
    from scaleforge.core.job import Job


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

MODEL_URLS = {
    "realesr-general-x4v3": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth",
    "realesrgan-x4plus": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    "realesr-animevideov3": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth",
}

DEFAULT_MODEL = "realesr-general-x4v3"


class TorchRealESRGANBackend(Backend):
    """Real-ESRGAN back-end powered by PyTorch."""

    name = "torch-realesrgan"

    # SHA256 checksums for the supported models. Stored as a class attribute so
    # tests can monkeypatch it easily.
    _MODEL_SHA256 = {
        "realesr-general-x4v3": "8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292",
        "realesrgan-x4plus": "4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1",
        "realesr-animevideov3": "3a5ca263a93b5c827d6e4a482b8857df6cc8a5c78a9a6065b5e72d4f60b0c7d6",
    }

    # ------------------------------------------------------------------
    # Life-cycle
    # ------------------------------------------------------------------
    def __init__(
        self,
        model_name: str | None = None,
        stub: bool = False,
        *,
        prefer_gpu: bool = True,
    ) -> None:
        """Initialise the backend.

        Parameters
        ----------
        model_name:
            Name of the Real-ESRGAN model to load. See :data:`MODEL_URLS`.
        stub:
            When ``True`` heavy dependencies are not imported and no model is
            loaded.  Useful for unit tests.
        prefer_gpu:
            If ``True`` and a CUDA device is available, it will be used.
        """

        super().__init__()
        self.model_name = model_name or DEFAULT_MODEL
        self.stub = stub
        self.device = "cpu"

        if stub:
            self._default_scale = 4
            return

        torch = self._lazy_import("torch")
        realesrgan_mod = self._lazy_import("realesrgan")

        self.device = "cuda" if prefer_gpu and torch.cuda.is_available() else "cpu"
        self.model_path = self._ensure_model()

        if RRDBNet is None:  # pragma: no cover - optional path
            raise ImportError(
                "basicsr not installed; set SF_HEAVY_TESTS=1 and install extras to run this path"
            )

        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
        )

        state_dict = torch.load(str(self.model_path), map_location="cpu")
        if "params" in state_dict:  # handle older checkpoints
            state_dict = state_dict["params"]

        missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
        if missing_keys:
            logger.warning(f"Missing keys in state_dict: {missing_keys}")
        if unexpected_keys:
            logger.warning(f"Unexpected keys in state_dict: {unexpected_keys}")

        model.to(self.device)
        self._upsampler = realesrgan_mod.RealESRGANer(
            scale=4,
            model_path=str(self.model_path),
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=False,
        )
        self._default_scale = 4

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        """Return ``True`` if the backend is ready for use."""

        return not self.stub and hasattr(self, "_upsampler")

    def description(self) -> str:
        """Human readable description for CLI output."""

        if self.stub:
            return "Stub mode (no actual upscaling)"
        return f"PyTorch ({self.device}) - {self.model_name}"

    async def upscale(  # type: ignore[override] - base declares async
        self,
        src: Path,
        dst: Path,
        *,
        scale: int = 4,
        tile: int | None = None,
        job: "Job" | None = None,
    ) -> None:
        """Upscale ``src`` to ``dst`` using the configured model."""

        if job and job.metadata and "scale" in job.metadata:
            scale = int(job.metadata["scale"])

        if scale not in (2, 4):
            logger.warning(f"Invalid scale {scale}, defaulting to {self._default_scale}")
            scale = self._default_scale

        logger.info(f"Upscaling to {scale}x using model '{self.model_name}'")
        img = Image.open(src).convert("RGB")
        result = self._upsampler.predict(img)

        dst.parent.mkdir(parents=True, exist_ok=True)
        result.save(dst)
        logger.info(f"Saved upscaled image to: {dst}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_model_file(self) -> str:
        """Return the filename for the selected model."""

        return f"{self.model_name}.pth"

    def _get_model_url(self) -> str:
        """Return the download URL for the selected model."""

        return MODEL_URLS[self.model_name]

    def _ensure_model(self) -> Path:
        """Ensure the model file is present and passes checksum validation."""

        cache_dir = Path(os.getenv("SCALEFORGE_CACHE", "~/.cache/scaleforge/models")).expanduser()
        cache_dir.mkdir(parents=True, exist_ok=True)

        model_path = cache_dir / self._get_model_file()
        expected = self._MODEL_SHA256[self.model_name]

        if not model_path.exists() or self._sha256(model_path) != expected:
            url = self._get_model_url()
            self._download(url, model_path)
            if self._sha256(model_path) != expected:  # pragma: no cover - network
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
    def _download(url: str, dest: Path) -> None:  # pragma: no cover - network
        tmp = dest.with_suffix(".tmp")
        with urllib.request.urlopen(url) as response, open(tmp, "wb") as fp:
            fp.write(response.read())
        tmp.rename(dest)

    @staticmethod
    def _lazy_import(name: str):
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as exc:  # pragma: no cover - import error path
            raise RuntimeError(
                f"{name} is required for the Torch back-end. Install with `pip install torch realesrgan pillow`."
            ) from exc


# ---------------------------------------------------------------------------
# Backwards-compatibility shim
# ---------------------------------------------------------------------------


class TorchBackend(TorchRealESRGANBackend):  # noqa: D401, N801
    """Alias so legacy import paths keep working during Sprint-3."""

    def __init__(self, stub: bool = False, **kwargs):  # noqa: D401 - simple
        super().__init__(stub=stub, **kwargs)

