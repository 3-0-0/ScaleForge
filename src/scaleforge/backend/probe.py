import numpy as np
from PIL import Image
from .base import BackendBase

def run_preflight_probe(backend: BackendBase) -> dict:
    """Run minimal upscale to determine GPU capabilities"""
    # Create 1x1 pixel test image
    tiny_img = Image.fromarray(np.zeros((1, 1, 3), dtype='uint8'))
    
    # Test max tile size
    max_tile = 512
    while max_tile >= 64:
        try:
            backend.upscale(tiny_img, scale=2, tile_size=max_tile)
            break
        except Exception:
            max_tile //= 2
    
    # Test max resolution (using tile size that worked)
    max_pixels = 8192 * 8192
    while max_pixels >= 1024 * 1024:
        try:
            test_size = int(max_pixels**0.5)
            test_img = Image.new('RGB', (test_size, test_size))
            backend.upscale(test_img, scale=2, tile_size=max_tile)
            break
        except Exception:
            max_pixels //= 4
    
    return {
        'max_tile_size': max_tile,
        'max_pixels': max_pixels
    }
