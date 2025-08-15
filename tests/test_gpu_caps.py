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

[Previous test functions unchanged until test_env_override]

def test_env_override(tmp_app_root, monkeypatch):
    """Test environment variable backend override."""
    # Import the full CLI module to ensure proper initialization
    import scaleforge.cli.main
    from click.testing import CliRunner
    
    # Print all registered commands for debugging
    print("Registered CLI commands:", [cmd.name for cmd in scaleforge.cli.main.cli.commands.values()])
    
    runner = CliRunner()
    monkeypatch.setenv("SCALEFORGE_BACKEND", "torch-cpu")

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
            result = runner.invoke(scaleforge.cli.main.cli, ["detect-backend", "--debug"], env={"SCALEFORGE_BACKEND": "torch-cpu"})
            if result.exit_code != 0:
                print(f"Command failed with output:\n{result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")
                print(f"Available commands: {[cmd.name for cmd in scaleforge.cli.main.cli.commands.values()]}")
            assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"
            assert '"backend": "torch-cpu"' in result.output
            assert '"source": "env"' in result.output

[Remaining test functions unchanged]
