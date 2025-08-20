"""Tests for the `model install` CLI command."""

from __future__ import annotations

from click.testing import CliRunner
from types import SimpleNamespace
import hashlib

from scaleforge.cli.main import cli
from scaleforge.models import downloader as downloader_mod
from scaleforge.models.downloader import ModelDownloader


def test_model_install_unknown(tmp_path, monkeypatch):
    """Unknown models should result in a usage error listing available ones."""

    monkeypatch.setattr(downloader_mod, "load_config", lambda: SimpleNamespace(model_dir=tmp_path))
    monkeypatch.setattr(ModelDownloader, "get_registry", lambda self: {"foo": {}})
    r = CliRunner().invoke(cli, ["model", "install", "bar"])
    assert r.exit_code == 2
    assert "Unknown model: bar" in r.output
    assert "foo" in r.output


def test_model_install_already_downloaded(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader_mod, "load_config", lambda: SimpleNamespace(model_dir=tmp_path))
    monkeypatch.setattr(ModelDownloader, "get_registry", lambda self: {"foo": {}})
    monkeypatch.setattr(ModelDownloader, "is_model_downloaded", lambda self, name: True)
    r = CliRunner().invoke(cli, ["model", "install", "foo"])
    assert r.exit_code == 0
    assert "already downloaded" in r.output


def test_model_install_success(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader_mod, "load_config", lambda: SimpleNamespace(model_dir=tmp_path))
    monkeypatch.setattr(ModelDownloader, "get_registry", lambda self: {"foo": {}})
    monkeypatch.setattr(ModelDownloader, "is_model_downloaded", lambda self, name: False)
    called = {}

    def fake_download(self, name):
        called["name"] = name

    monkeypatch.setattr(ModelDownloader, "download_model", fake_download)
    r = CliRunner().invoke(cli, ["model", "install", "foo"])
    assert r.exit_code == 0
    assert "Installing model: foo" in r.output
    assert "✅ Done." in r.output
    assert called.get("name") == "foo"


def test_model_install_download_error(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader_mod, "load_config", lambda: SimpleNamespace(model_dir=tmp_path))
    monkeypatch.setattr(ModelDownloader, "get_registry", lambda self: {"foo": {}})
    monkeypatch.setattr(ModelDownloader, "is_model_downloaded", lambda self, name: False)

    def boom(self, name):
        raise RuntimeError("network fail")

    monkeypatch.setattr(ModelDownloader, "download_model", boom)
    r = CliRunner().invoke(cli, ["model", "install", "foo"])
    assert r.exit_code == 1
    assert "network fail" in r.output


def _setup_downloader(tmp_path, info, monkeypatch):
    monkeypatch.setattr(downloader_mod, "load_config", lambda: SimpleNamespace(model_dir=tmp_path))
    dl = ModelDownloader(model_dir=tmp_path)
    entry = downloader_mod._ResolvedModel(info=info, path=tmp_path / "foo.bin")
    dl._registry = {"foo": entry}
    return dl


def test_download_model_with_url_dict(tmp_path, monkeypatch):
    data = b"hello"
    sha = hashlib.sha256(data).hexdigest()
    info = {"url": "http://example.com/foo.bin", "sha256": sha}
    dl = _setup_downloader(tmp_path, info, monkeypatch)
    monkeypatch.setattr(ModelDownloader, "_download", lambda self, url, dest: dest.write_bytes(data))
    path = dl.download_model("foo")
    assert path.read_bytes() == data


def test_download_model_with_urls_dict(tmp_path, monkeypatch):
    data = b"world"
    sha = hashlib.sha256(data).hexdigest()
    info = {"urls": ["http://a/foo.bin", "http://b/foo.bin"], "sha256": sha}
    dl = _setup_downloader(tmp_path, info, monkeypatch)
    monkeypatch.setattr(ModelDownloader, "_download", lambda self, url, dest: dest.write_bytes(data))
    path = dl.download_model("foo")
    assert path.read_bytes() == data

