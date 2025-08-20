from __future__ import annotations
import hashlib
import os
import sys
import types

import pytest
from PIL import Image

pytestmark = pytest.mark.skipif(
    os.getenv("SF_HEAVY_TESTS") != "1",
    reason="requires basicsr/Real-ESRGAN; gated for smoke",
)


@pytest.fixture(autouse=True)
def stub_heavy_deps(tmp_path, monkeypatch):
    """Stub torch & realesrgan so the test avoids big wheels + network."""

    # torch stub
    torch_stub = types.ModuleType("torch")
    torch_stub.cuda = types.SimpleNamespace(is_available=lambda: False)
    torch_stub.load = lambda path, map_location=None: {}
    monkeypatch.setitem(sys.modules, "torch", torch_stub)

    # realesrgan stub
    class _DummyUpscaler:  # noqa: D401
        def __init__(self, *args, **kwargs):  # noqa: D401
            pass

        def predict(self, img):  # noqa: D401
            return img  # passthrough

    realesrgan_stub = types.ModuleType("realesrgan")
    realesrgan_stub.RealESRGANer = _DummyUpscaler
    monkeypatch.setitem(sys.modules, "realesrgan", realesrgan_stub)

    # basicsr stub
    rrdbnet_stub = types.ModuleType("basicsr.archs.rrdbnet_arch")
    class _DummyRRDBNet:  # noqa: D401
        def __init__(self, *args, **kwargs):  # noqa: D401
            pass

        def load_state_dict(self, state_dict, strict=False):  # noqa: D401
            return [], []

        def to(self, device):  # noqa: D401
            return self

    rrdbnet_stub.RRDBNet = _DummyRRDBNet
    monkeypatch.setitem(sys.modules, "basicsr.archs.rrdbnet_arch", rrdbnet_stub)

    # Fake cached model so download step is skipped
    cache_dir = tmp_path / "models"
    cache_dir.mkdir()
    dummy_model = cache_dir / "realesr-general-x4v3.pth"
    dummy_model.write_bytes(b"dummy")
    monkeypatch.setenv("SCALEFORGE_CACHE", str(cache_dir))

    # Patch expected checksum to match dummy file
    from scaleforge.backend import torch_backend as tb

    monkeypatch.setattr(
        tb.TorchRealESRGANBackend,
        "_MODEL_SHA256",
        {"realesr-general-x4v3": hashlib.sha256(b"dummy").hexdigest()},
        raising=False,
    )


@pytest.mark.asyncio
async def test_upscale_roundtrip(tmp_path):
    """Backend should save an output file without heavy deps."""

    from scaleforge.backend.torch_backend import TorchRealESRGANBackend

    src = tmp_path / "in.png"
    dst = tmp_path / "out.png"
    Image.new("RGB", (8, 8), "white").save(src)

    backend = TorchRealESRGANBackend(prefer_gpu=False)
    await backend.upscale(src, dst)

    assert dst.exists()

