

"""Tests for GPU capability detection and caching."""


from unittest.mock import patch, MagicMock
import pytest
from datetime import datetime
from click.testing import CliRunner

from scaleforge.backend.detector import (
    detect_gpu_vendor,
    detect_gpu_caps,
    load_caps,
    save_caps
)

@pytest.fixture
def tmp_app_root(tmp_path):
    """Fixture providing temporary APP_ROOT directory."""
    return tmp_path / "app_root"

def test_vendor_detection_windows_nvidia(tmp_app_root, monkeypatch):
    """Test Windows NVIDIA detection via wmic."""
    monkeypatch.setattr("platform.system", lambda: "Windows")
    mock_run = MagicMock()
    mock_run.return_value.stdout = "NVIDIA GeForce RTX 3080"
    monkeypatch.setattr("subprocess.run", mock_run)
    
    assert detect_gpu_vendor() == "nvidia"
    mock_run.assert_called_once_with(
        ["wmic", "path", "win32_VideoController", "get", "name"],
        capture_output=True,
        text=True,
        check=True
    )

def test_vendor_detection_linux_amd(tmp_app_root, monkeypatch):
    """Test Linux AMD detection via lspci."""
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("subprocess.run", 
                       MagicMock(side_effect=[
                           Exception("nvidia-smi missing"),
                           MagicMock(stdout="VGA compatible controller: Advanced Micro Devices [AMD/ATI]")
                       ]))
    assert detect_gpu_vendor() == "amd"

def test_caps_caching(tmp_app_root):
    """Test capabilities caching roundtrip."""
    test_caps = {
        "vendor": "nvidia",
        "backend": "torch-cuda",
        "max_tile_size": 256,
        "max_megapixels": 120.0,
        "detected_at": datetime.now().isoformat()
    }
    
    # Test save and load
    save_caps(tmp_app_root, test_caps)
    loaded = load_caps(tmp_app_root)
    assert loaded == test_caps
    
    # Test detect_gpu_caps uses cache when available
    with patch("scaleforge.backend.detector.detect_gpu_vendor") as mock_detect:
        caps = detect_gpu_caps(tmp_app_root)
        mock_detect.assert_not_called()
        assert caps == test_caps

def test_force_probe(tmp_app_root, monkeypatch):
    """Test force_probe ignores cache."""
    # Create directory and dummy cache
    tmp_app_root.mkdir(parents=True, exist_ok=True)
    (tmp_app_root / "gpu_caps.json").write_text("{}")
    
    with patch("scaleforge.backend.detector.detect_gpu_vendor") as mock_detect:
        mock_detect.return_value = "amd"
        caps = detect_gpu_caps(tmp_app_root, force_probe=True)
        mock_detect.assert_called_once()
        assert caps["vendor"] == "amd"

def test_env_override(tmp_app_root, monkeypatch):
    """Test environment variable backend override."""
    monkeypatch.setenv("SCALEFORGE_BACKEND", "torch-cpu")
    
    # Mock the entire backend module to avoid heavy dependencies
    with patch.dict('sys.modules', {
        'scaleforge.backend.selector': MagicMock(),
        'scaleforge.backend.torch_backend': MagicMock(),
        'scaleforge.backend.vulkan_backend': MagicMock()
    }):
        mock_backend = MagicMock()
        mock_get = MagicMock(return_value=(
            mock_backend,
            {
                "vendor": "override",
                "backend": "torch-cpu",
                "source": "env"
            }
        ))
        
        with patch('scaleforge.backend.selector.get_backend', mock_get):
            from scaleforge.cli.main import detect_backend
            with patch("click.echo") as mock_echo:
                detect_backend(debug=True)
                output = mock_echo.call_args[0][0]
                assert '"backend": "torch-cpu"' in output
                assert '"source": "env"' in output

# These imports are already present at the top of the file
def test_cli_detect_backend_smoke(monkeypatch, tmp_path):
    # Make APP_ROOT point at tmp dir
    monkeypatch.setenv("APP_ROOT", str(tmp_path))
    (tmp_path).mkdir(parents=True, exist_ok=True)

    # Stub selector.get_backend → avoid importing heavy deps
    with patch("scaleforge.backend.selector.get_backend", return_value=(MagicMock(), {
        "vendor": "nvidia",
        "backend": "torch-cuda",
        "source": "cached",
        "caps": {"max_tile_size": 512, "max_megapixels": 64}
    })):
        from scaleforge.cli.main import cli  # import AFTER patch
        runner = CliRunner()
        result = runner.invoke(cli, ["detect-backend"])
        assert result.exit_code == 0
        assert "torch-cuda" in result.output
        assert "nvidia" in result.output
