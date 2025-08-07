from __future__ import annotations

import asyncio
import hashlib
import sys
import types
import pytest
from PIL import Image


@pytest.fixture(autouse=True)
def stub_heavy_deps(tmp_path, monkeypatch):
    """Stub torch & realesrgan so the test avoids big wheels + network."""

    # torch stub
    torch_stub = types.ModuleType("torch")
    torch_stub.cuda = types.SimpleNamespace(is_available=lambda: False)
    monkeypatch.setitem(sys.modules, "torch", torch_stub)

    # realesrgan stub
    class _DummyUpscaler:  # noqa: D401
        def __init__(self, device="cpu", scale=4):  # noqa: D401
            self.device = device
            self.scale = scale

        def load_weights(self, _path):  # noqa: D401
            return None

        def predict(self, img):  # noqa: D401
            return img  # passthrough

    realesrgan_stub = types.ModuleType("realesrgan")
    realesrgan_stub.RealESRGAN = _DummyUpscaler
    monkeypatch.setitem(sys.modules, "realesrgan", realesrgan_stub)

    # Fake cached model so download step is skipped
    cache_dir = tmp_path / "models"
    cache_dir.mkdir()
    dummy_model = cache_dir / "RealESRGAN_x4plus.pth"
    dummy_model.write_bytes(b"dummy")
    monkeypatch.setenv("SCALEFORGE_CACHE", str(cache_dir))

    # Patch expected checksum to match dummy file
    from scaleforge.backend.torch_backend import TorchBackend

    monkeypatch.setattr(
        TorchBackend,
        "_MODEL_SHA256",
        hashlib.sha256(b"dummy").hexdigest(),
        raising=False,
    )


def test_upscale_roundtrip(tmp_path):
    """Backend should save an output file without heavy deps."""

    from scaleforge.backend.torch_backend import TorchBackend

    src = tmp_path / "in.png"
    dst = tmp_path / "out.png"
    Image.new("RGB", (8, 8), "white").save(src)

    backend = TorchBackend(stub=True)
    asyncio.run(backend.upscale(src, dst))

    assert dst.exists()
