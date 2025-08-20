"""Model registry utilities.

The original project defined the registry entries using :mod:`pydantic` models.
For the purposes of the exercises the heavy dependency on Pydantic is avoided
and a small hand written validator is used instead.  Only the behaviour needed
by the tests is implemented: loading JSON/YAML files and performing some basic
validation of model entries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# ``yaml`` is optional; when missing we fall back to a tiny parser based on
# ``json`` which is sufficient for the simple test data.
try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_HEX = set("0123456789abcdefABCDEF")


def _coerce_to_list(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if isinstance(data, dict) and "models" in data:
        models = data["models"]
        if isinstance(models, list):
            return models
        raise ValueError("`models` must be a list")
    if isinstance(data, list):
        return data
    raise ValueError("Expected dict with 'models' or a list of entries")


def _validate_item(idx: int, raw: Dict[str, Any]) -> Optional[str]:
    """Return an error string for *raw* or ``None`` when valid."""

    name = raw.get("name")
    if not isinstance(name, str) or not name:
        return "item %d: name must be a non-empty string" % idx

    sha256 = raw.get("sha256")
    if not (isinstance(sha256, str) and len(sha256) == 64 and all(c in _HEX for c in sha256)):
        return f"item {idx}: sha256 must be 64 hex characters"

    urls = raw.get("urls")
    url = raw.get("url")
    if urls is not None:
        if not isinstance(urls, list) or len(urls) == 0:
            return f"item {idx}: urls must be a non-empty list if provided"
    elif not url:
        return f"item {idx}: must supply either `url` or non-empty `urls`"

    size = raw.get("size_bytes")
    if size is not None and (not isinstance(size, int) or size < 0):
        return f"item {idx}: size_bytes must be a non-negative integer"

    return None


def validate_registry(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Tuple[bool, List[str]]:
    """Validate registry entries returning ``(ok, [errors])``."""

    errors: List[str] = []
    try:
        items = _coerce_to_list(data)
    except Exception as e:  # pragma: no cover - defensive
        return False, [str(e)]

    names_seen: set[str] = set()
    dupes: set[str] = set()

    for idx, raw in enumerate(items):
        err = _validate_item(idx, raw)
        if err:
            errors.append(err)
            continue

        name = raw["name"]
        if name in names_seen:
            dupes.add(name)
        names_seen.add(name)

    if dupes:
        errors.append("duplicate names: " + ", ".join(sorted(dupes)))

    return (len(errors) == 0), errors


# ---------------------------------------------------------------------------
# File loading helpers
# ---------------------------------------------------------------------------


def _load_text(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in (".yml", ".yaml"):
        if yaml is None:
            raise RuntimeError("YAML requested but PyYAML is not installed")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return {"models": _coerce_to_list(data)}


def load_registry_file(path: Path) -> Dict[str, Any]:
    """Load a registry JSON or YAML file and normalise to ``{"models": [...]}``."""

    return _load_text(path)


def load_effective_registry() -> Dict[str, Any]:  # pragma: no cover - trivial
    """Load built-in registry if present, otherwise return an empty registry."""

    here = Path(__file__).resolve().parent
    for name in ("builtins.json", "builtins.yaml", "builtins.yml"):
        p = here / name
        if p.exists():
            try:
                return load_registry_file(p)
            except Exception:
                pass
    return {"models": []}


__all__ = ["validate_registry", "load_registry_file", "load_effective_registry"]

