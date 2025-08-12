

"""Tests for GPU capability caching."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from scaleforge.backend.caps import (
    _run_preflight_probe,
    load_cached_caps,
    save_caps_to_cache,
    DEFAULT_CAPS
)

@pytest.fixture
def mock_cache_file(tmp_path):
    """Fixture providing a temporary cache file path."""
    return tmp_path / "gpu_caps.json"

def test_preflight_probe_stub():
    """Test that preflight probe returns the stubbed defaults."""
    assert _run_preflight_probe() == DEFAULT_CAPS

def test_load_cached_caps_missing(mock_cache_file):
    """Test loading when cache file doesn't exist."""
    with patch("scaleforge.backend.caps.CACHE_FILE", mock_cache_file):
        assert load_cached_caps() == DEFAULT_CAPS

def test_load_cached_caps_valid(mock_cache_file):
    """Test loading valid cached capabilities."""
    test_caps = {"max_tile": 1024, "max_pixels": 16384*16384}
    with open(mock_cache_file, "w") as f:
        json.dump(test_caps, f)
    
    with patch("scaleforge.backend.caps.CACHE_FILE", mock_cache_file):
        assert load_cached_caps() == test_caps

def test_load_corrupt_cache(mock_cache_file):
    """Test handling of corrupt cache file."""
    mock_cache_file.write_text("invalid json")
    
    with patch("scaleforge.backend.caps.CACHE_FILE", mock_cache_file):
        assert load_cached_caps() == DEFAULT_CAPS

def test_save_caps(mock_cache_file):
    """Test saving capabilities to cache."""
    test_caps = {"max_tile": 768, "max_pixels": 12288*12288}
    
    with patch("scaleforge.backend.caps.CACHE_FILE", mock_cache_file):
        save_caps_to_cache(test_caps)
        assert mock_cache_file.exists()
        assert json.loads(mock_cache_file.read_text()) == test_caps

