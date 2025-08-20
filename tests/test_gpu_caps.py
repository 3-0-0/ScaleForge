"""Tests for GPU capability detection and caching."""

from unittest.mock import patch
import pytest
from click.testing import CliRunner
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scaleforge.backend.detector import detect_gpu_caps

@pytest.fixture
def tmp_app_root(tmp_path):
    """Fixture providing temporary APP_ROOT directory."""
    return tmp_path / "app_root"

def test_env_override(tmp_app_root, monkeypatch):
    """Ensure env override influences backend path via the CLI."""
    try:
        from scaleforge.cli.main import cli
    except (SyntaxError, ImportError):
        pytest.skip("CLI import failed")

    runner = CliRunner()
    monkeypatch.setenv("SCALEFORGE_BACKEND", "torch-eager-cpu")

    with patch("scaleforge.backend.detector.detect_backend") as mock_detect:
        result = runner.invoke(cli, ["detect-backend", "--debug"])

    assert result.exit_code == 0
    assert "torch-eager-cpu" in result.output
    mock_detect.assert_not_called()


def _mock_torch(*, cuda=False, cuda_version=None, hip_version=None, mps=False, mps_built=True):
    """Create a minimal torch mock with desired capabilities."""
    torch = types.ModuleType("torch")
    torch.version = types.SimpleNamespace(cuda=cuda_version, hip=hip_version)
    torch.cuda = types.SimpleNamespace(is_available=lambda: cuda)
    torch.backends = types.SimpleNamespace(
        mps=types.SimpleNamespace(
            is_available=lambda: mps,
            is_built=lambda: mps_built,
        )
    )
    return torch


def _caps_with_torch(torch_module):
    with patch.dict(sys.modules, {"scaleforge.backend.selector": None, "torch": torch_module}):
        return detect_gpu_caps()


def test_fallback_cuda():
    caps = _caps_with_torch(_mock_torch(cuda=True, cuda_version="12.0"))
    assert caps["backend"] == "torch-eager-cuda"
    assert caps["vendor"] == "nvidia"
    assert caps["cuda"] and not caps["rocm"] and not caps["mps"]


def test_fallback_rocm():
    caps = _caps_with_torch(_mock_torch(cuda=True, hip_version="5.6"))
    assert caps["backend"] == "torch-eager-rocm"
    assert caps["vendor"] == "amd"
    assert caps["rocm"] and not caps["cuda"] and not caps["mps"]


def test_fallback_mps():
    caps = _caps_with_torch(_mock_torch(mps=True))
    assert caps["backend"] == "torch-eager-mps"
    assert caps["vendor"] == "apple"
    assert caps["mps"] and not caps["cuda"] and not caps["rocm"]


def test_cpu_only():
    with patch.dict(sys.modules, {"scaleforge.backend.selector": None, "torch": None}):
        caps = detect_gpu_caps()
    assert caps["backend"] == "torch-eager-cpu"
    assert caps["vendor"] == "cpu"
    assert not any((caps["cuda"], caps["rocm"], caps["mps"]))
