from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scaleforge.models import downloader as downloader_mod
from scaleforge.models.downloader import ModelDownloader
from scaleforge.errors import ModelChecksumMismatch

def _setup(tmp_path: Path, info: dict, monkeypatch):
    monkeypatch.setattr(
        downloader_mod, 'load_config', lambda: type('cfg', (), {'model_dir': tmp_path})()
    )
    dl = ModelDownloader(model_dir=tmp_path)
    entry = downloader_mod._ResolvedModel(info=info, path=tmp_path / 'out.bin')
    dl._registry = {'m': entry}
    return dl, entry.path

def test_single_file_url_ok(tmp_path, monkeypatch):
    src = tmp_path / 'file.bin'
    data = b'hello'
    src.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    info = {'url': src.as_uri(), 'sha256': sha}
    dl, dest = _setup(tmp_path, info, monkeypatch)
    path = dl.download_model('m')
    assert path == dest
    assert path.read_bytes() == data

def test_urls_fallback(tmp_path, monkeypatch):
    good = tmp_path / 'good.bin'
    data = b'data'
    good.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    bad_url = (tmp_path / 'missing.bin').as_uri()
    info = {'urls': [bad_url, good.as_uri()], 'sha256': sha}
    dl, dest = _setup(tmp_path, info, monkeypatch)
    path = dl.download_model('m')
    assert path.read_bytes() == data
    assert dl.last_url == good.as_uri()

def test_checksum_mismatch_raises(tmp_path, monkeypatch):
    src = tmp_path / 'file.bin'
    src.write_text('bad')
    info = {'url': src.as_uri(), 'sha256': '0' * 64}
    dl, _ = _setup(tmp_path, info, monkeypatch)
    with pytest.raises(ModelChecksumMismatch):
        dl.download_model('m')

def test_idempotent_skip(tmp_path, monkeypatch):
    data = b'hello'
    src = tmp_path / 'src.bin'
    src.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    dest = tmp_path / 'out.bin'
    dest.write_bytes(data)
    info = {'url': src.as_uri(), 'sha256': sha}
    dl, _ = _setup(tmp_path, info, monkeypatch)
    path = dl.download_model('m')
    assert path.read_bytes() == data
