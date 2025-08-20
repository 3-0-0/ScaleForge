from unittest.mock import patch

import pytest

from scaleforge.backend.selector import get_backend
from scaleforge.backend.torch_backend import TorchBackend
from scaleforge.backend.vulkan_backend import VulkanBackend


@pytest.mark.parametrize(
    "code,expected",
    [
        ("torch-eager-cuda", TorchBackend),
        ("torch-eager-rocm", TorchBackend),
        ("torch-eager-mps", TorchBackend),
        ("torch-eager-cpu", TorchBackend),
        ("ncnn-ncnn-vulkan", VulkanBackend),
    ],
)

def test_detected_backend_mapping(monkeypatch, code, expected):
    monkeypatch.delenv("SCALEFORGE_BACKEND", raising=False)
    monkeypatch.setenv("SF_STUB_UPSCALE", "1")
    with patch("scaleforge.backend.selector.get_backend_alias", return_value=(code, [])):
        backend = get_backend()
    assert isinstance(backend, expected)


@pytest.mark.parametrize(
    "code,expected",
    [
        ("torch-eager-cpu", TorchBackend),
        ("ncnn-ncnn-vulkan", VulkanBackend),
    ],
)

def test_env_override(monkeypatch, code, expected):
    monkeypatch.setenv("SCALEFORGE_BACKEND", code)
    monkeypatch.setenv("SF_STUB_UPSCALE", "1")
    with patch("scaleforge.backend.detector.detect_backend") as mock_detect:
        backend = get_backend()
    assert isinstance(backend, expected)
    mock_detect.assert_not_called()
