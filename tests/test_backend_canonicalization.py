from __future__ import annotations

import os
import subprocess
import sys
from unittest.mock import patch

from scaleforge.backend.spec import BackendSpec
from scaleforge.backend.selector import get_backend_alias


def test_canonical_round_trip():
    spec = BackendSpec("torch", "eager", "cpu")
    alias, _ = get_backend_alias(spec)
    assert alias == spec.alias


def test_legacy_alias_mapping():
    with patch("scaleforge.backend.detector.detect_backend", return_value=(BackendSpec("torch", "eager", "cpu"), [])):
        alias, _ = get_backend_alias("torch")
    assert alias == "torch-eager-cpu"
    alias_cpu, _ = get_backend_alias("cpu")
    assert alias_cpu == "cpu-pillow"


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv("SCALEFORGE_BACKEND", "ncnn-ncnn-cpu")
    with patch("scaleforge.backend.detector.detect_backend") as mock_detect:
        alias, _ = get_backend_alias()
    assert alias == "ncnn-ncnn-cpu"
    mock_detect.assert_not_called()


def test_cli_detect_backend(monkeypatch):
    env = os.environ.copy()
    env["SCALEFORGE_BACKEND"] = "cpu-pillow"
    result = subprocess.run(
        [sys.executable, "-m", "scaleforge.cli", "detect-backend"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout.strip()
