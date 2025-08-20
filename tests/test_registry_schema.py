from __future__ import annotations

from scaleforge.models.registry import validate_registry


def test_valid_registry_passes():
    reg = {"models": {"m": {"info": {"url": "file:///tmp/x", "sha256": "0" * 64}}}}
    ok, errors = validate_registry(reg)
    assert ok
    assert errors == []


def test_missing_sha256_fails():
    reg = {"models": {"m": {"info": {"url": "file:///tmp/x"}}}}
    ok, errors = validate_registry(reg)
    assert not ok
    assert errors


def test_neither_url_nor_urls_fails():
    reg = {"models": {"m": {"info": {"sha256": "0" * 64}}}}
    ok, errors = validate_registry(reg)
    assert not ok
    assert errors
