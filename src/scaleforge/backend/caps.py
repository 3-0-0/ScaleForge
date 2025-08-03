import json
from pathlib import Path

class GPUCapabilityCache:
    def __init__(self, app_root: str):
        self.cache_file = Path(app_root) / 'gpu_caps.json'
    
    def save(self, max_tile: int, max_pixels: int):
        """Cache GPU limits after probe"""
        self.cache_file.write_text(json.dumps({
            'max_tile_size': max_tile,
            'max_pixels': max_pixels
        }))
    
    def load(self) -> dict:
        """Load cached capabilities or return None"""
        try:
            return json.loads(self.cache_file.read_text()) if self.cache_file.exists() else None
        except json.JSONDecodeError:
            return None  # Handle corrupt cache
