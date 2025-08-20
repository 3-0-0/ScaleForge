"""Tests for the `model install` CLI command."""

from __future__ import annotations

from click.testing import CliRunner
from types import SimpleNamespace

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

