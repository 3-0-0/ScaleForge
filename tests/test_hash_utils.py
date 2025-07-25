from pathlib import Path

from scaleforge.utils.hash import hash_params
import os


def test_same_file_same_hash(tmp_path):
    img = tmp_path / "a.png"
    img.write_bytes(b"123")
    h1 = hash_params(img, {"scale": 2})
    h2 = hash_params(img, {"scale": 2})
    assert h1 == h2


def test_params_affect_hash(tmp_path):
    img = tmp_path / "a.png"
    img.write_bytes(b"123")
    h1 = hash_params(img, {"scale": 2})
    h2 = hash_params(img, {"scale": 4})
    assert h1 != h2
