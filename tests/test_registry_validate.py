
# tests/test_registry_validate.py
from __future__ import annotations

import json
from pathlib import Path
# Cleaned unused imports

from scaleforge.models.registry import validate_registry, load_registry_file


def _write_json(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "reg.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_validate_happy(tmp_path):
    path = _write_json(tmp_path, {"models": [{"name": "x", "url": "https://example.com/m.bin", "sha256": "0" * 64}]})
    data = load_registry_file(path)
    ok, errors = validate_registry(data)
    assert ok
    assert len(errors) == 0


def test_validate_invalid_schema(tmp_path):
    path = _write_json(tmp_path, {"models": [{"url": "https://example.com/m.bin", "sha256": "0" * 64}]})
    data = load_registry_file(path)
    ok, errors = validate_registry(data)
    assert not ok
    assert any("name" in err.lower() for err in errors)


def test_validate_duplicates(tmp_path):
    path = _write_json(
        tmp_path,
        {"models": [
            {"name": "x", "url": "u1", "sha256": "0" * 64},
            {"name": "x", "url": "u2", "sha256": "0" * 64},
        ]},
    )
    data = load_registry_file(path)
    ok, errors = validate_registry(data)
    assert not ok 
    assert any("duplicate" in err.lower() for err in errors)
