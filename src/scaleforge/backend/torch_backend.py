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
import logging
import os
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

from basicsr.archs.rrdbnet_arch import RRDBNet
from PIL import Image

from scaleforge.backend.base import Backend

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover – type hints only
    from scaleforge.core.job import Job  # noqa: F401 – forward reference


MODEL_URLS = {
    'realesr-general-x4v3': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth',
    'realesrgan-x4plus': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
    'realesr-animevideov3': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth'
}

DEFAULT_MODEL = 'realesr-general-x4v3'

class TorchRealESRGANBackend(Backend):
    """Real-ESRGAN back-end powered by PyTorch supporting multiple models."""

    name = "torch-realesrgan"

    def is_available(self) -> bool:
        """Check if backend is available (dependencies installed and models loaded)."""
        return not self.stub and hasattr(self, '_upsampler')

    def description(self) -> str:
        """Return backend description including device info."""
        if self.stub:
            return "Stub mode (no actual upscaling)"
        return f"PyTorch ({self.device}) - {self.model_name}"

    def __init__(self, model_name: str | None = None, stub: bool = False, *, prefer_gpu: bool = True):
        """Initialize backend with model selection and device preferences.
        
        Args:
            model_name: Name of model to load (see MODEL_URLS)
            stub: Whether to run in stub mode (no actual upscaling)
            prefer_gpu: Whether to prefer GPU execution if available
        """
        super().__init__()
        self.model_name = model_name or DEFAULT_MODEL
        self.stub = stub
        
        if not stub:
            torch = self._lazy_import("torch")
            realesrgan_mod = self._lazy_import("realesrgan")


            self.device = "cuda" if prefer_gpu and torch.cuda.is_available() else "cpu"
            self.model_path = self._ensure_model()
            
            # Initialize model
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32)
            state_dict = torch.load(str(self.model_path), map_location='cpu')
            
            # Handle both new and old model formats
            if 'params' in state_dict:
                state_dict = state_dict['params']
            
            # Try loading with strict=False to handle minor key mismatches
            missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
            if missing_keys:
                logger.warning(f"Missing keys in state_dict: {missing_keys}")
            if unexpected_keys:
                logger.warning(f"Unexpected keys in state_dict: {unexpected_keys}")
            if not missing_keys and not unexpected_keys:
                logger.error("Model loading failed - unknown error")
                raise RuntimeError(
                    f"Failed to load model weights. This may indicate a version mismatch. "
                    f"Please verify you have the correct model file for {self.model_name}"
                )
            model.to(self.device)
            self._upsampler = realesrgan_mod.RealESRGANer(
                scale=4,
                model_path=str(self.model_path),
                model=model,
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=False
            )
            self._default_scale = 4

    _MODEL_SHA256 = {
        'realesr-general-x4v3': "8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292",
        'realesrgan-x4plus': "4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1", 
        'realesr-animevideov3': "3a5ca263a93b5c827d6e4a482b8857df6cc8a5c78a9a6065b5e72d4f60b0c7d6"
    }

    def _get_model_file(self) -> str:
        """Return the filename for the current model."""
        return f"{self.model_name}.pth"

    def _get_model_url(self) -> str:
        """Return the download URL for the current model."""
        return MODEL_URLS[self.model_name]

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
            Target scale (2 or 4). Falls back to model default if invalid.
        tile, job
            Reserved for future improvements.
        """
        # Get scale from job metadata if available
        if job and job.metadata and "scale" in job.metadata:
            scale = int(job.metadata["scale"])
        
        # Validate scale
        if scale not in (2, 4):
            logger.warning(f"Invalid scale {scale}, defaulting to {self._default_scale}")
            scale = self._default_scale

        logger.info(f"Upscaling to {scale}x using model '{self.model_name}'")
        img = Image.open(src).convert("RGB")
        result = self._upsampler.predict(img)
        
        # Generate output path with scale suffix if not explicitly provided
        if dst is None:
            suffix = f"_{scale}x.png"
            dst = src.with_name(f"{src.stem}{suffix}")
            logger.debug(f"Auto-generated output path: {dst}")
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        result.save(dst)
        logger.info(f"Saved upscaled image to: {dst}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ensure_model(self) -> Path:
        """Return path to the model file, downloading if missing/invalid."""
        cache_dir = Path(os.getenv("SCALEFORGE_CACHE", "~/.cache/scaleforge/models")).expanduser()
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_path = cache_dir / self._get_model_file()

        if not model_path.exists() or self._sha256(model_path) != self._MODEL_SHA256[self.model_name]:
            from scaleforge.backend.torch_backend import MODEL_URLS
            self._download(MODEL_URLS[self.model_name], model_path)
            if self._sha256(model_path) != self._MODEL_SHA256[self.model_name]:  # pragma: no cover
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



