import pytest
from unittest.mock import patch, mock_open
from scaleforge.backend.caps import GPUCapabilityCache

def test_cache_save_load(tmp_path):
    cache = GPUCapabilityCache(str(tmp_path))
    test_data = {'max_tile_size': 512, 'max_pixels': 8192*8192}
    
    # Test save and load
    cache.save(**test_data)
    loaded = cache.load()
    assert loaded == test_data
    
    # Test corrupt cache handling
    with patch("pathlib.Path.read_text", return_value="invalid{json"):
        assert cache.load() is None
