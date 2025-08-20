"""Model registry utilities."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

_HEX_RE = re.compile(r"^[a-f0-9]{64}$")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _manual_validate(reg: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    models = reg.get("models")
    if not isinstance(models, dict):
        return ["'models' must be an object"]
    for name, entry in models.items():
        if not isinstance(entry, dict):
            errors.append(f"{name}: entry must be an object")
            continue
        info = entry.get("info")
        if not isinstance(info, dict):
            errors.append(f"{name}: missing info object")
            continue
        sha = info.get("sha256")
        if not (isinstance(sha, str) and _HEX_RE.match(sha)):
            errors.append(f"{name}: info.sha256 must be 64 hex characters")
        urls = info.get("urls")
        url = info.get("url")
        if urls is not None:
            if not (
                isinstance(urls, list)
                and len(urls) > 0
                and all(isinstance(u, str) for u in urls)
            ):
                errors.append(
                    f"{name}: info.urls must be a non-empty list of strings"
                )
        elif not isinstance(url, str):
            errors.append(
                f"{name}: info must include 'url' or non-empty 'urls'"
            )
    return errors


def validate_registry(reg: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate registry mapping using JSON Schema when available."""

    try:  # pragma: no cover - optional dependency
        import jsonschema  # type: ignore
        from importlib import resources

        schema_text = (
            resources.files(__package__)
            .joinpath("registry.schema.json")
            .read_text("utf-8")
        )
        schema = json.loads(schema_text)
        validator = jsonschema.Draft7Validator(schema)
        errors = [e.message for e in validator.iter_errors(reg)]
        return len(errors) == 0, errors
    except Exception:
        errors = _manual_validate(reg)
        return len(errors) == 0, errors


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
    return data


def load_registry_file(path: Path) -> Dict[str, Any]:
    """Load a registry JSON or YAML file."""

    return _load_text(path)


def load_effective_registry() -> Dict[str, Any]:  # pragma: no cover - trivial
    """Load built-in registry if present, otherwise return an empty registry."""

    here = Path(__file__).resolve().parent
    for name in ("builtins.json", "builtins.yaml", "builtins.yml"):
        p = here / name
        if p.exists():
            try:
                data = load_registry_file(p)
            except Exception:
                data = {"models": {}}
            meta: Dict[str, Any] = {}
            try:  # pragma: no cover - optional dependency
                import jsonschema  # type: ignore  # noqa: F401
            except Exception:
                meta["warning"] = "registry validation skipped: jsonschema not installed"
            else:
                ok, errors = validate_registry(data)
                if not ok:
                    meta["errors"] = errors
            if meta:
                data.setdefault("_meta", {}).update(meta)
            return data
    return {"models": {}}


__all__ = ["validate_registry", "load_registry_file", "load_effective_registry"]

