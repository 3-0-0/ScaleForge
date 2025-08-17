
# src/scaleforge/models/registry.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # Optional dependency

from pydantic import BaseModel, Field, field_validator


class ModelSchema(BaseModel):
    """Single model entry in the registry."""
    name: str = Field(min_length=1)
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    sha256: str = Field(min_length=64, max_length=64)
    filename: Optional[str] = None
    size_bytes: Optional[int] = Field(default=None, ge=0)

    @field_validator("sha256")
    @classmethod
    def _sha256_hex(cls, v: str) -> str:
        if len(v) != 64 or any(c not in "0123456789abcdefABCDEF" for c in v):
            raise ValueError("sha256 must be 64 hex characters")
        return v.lower()

    @field_validator("urls")
    @classmethod
    def _urls_nonempty(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) == 0:
            raise ValueError("urls must be non-empty if provided")
        return v

    def resolved_urls(self) -> List[str]:
        if self.urls:
            return self.urls
        return [self.url] if self.url else []


def _coerce_to_list(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if isinstance(data, dict) and "models" in data:
        models = data["models"]
        if isinstance(models, list):
            return models
        raise ValueError("`models` must be a list")
    if isinstance(data, list):
        return data
    raise ValueError("Expected dict with 'models' or a list of entries")


def validate_registry(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Tuple[bool, List[str]]:
    """Return (ok, [errors]) after validating every entry and duplicates."""
    errors: List[str] = []
    try:
        items = _coerce_to_list(data)
    except Exception as e:
        return False, [str(e)]

    names_seen: set[str] = set()
    dupes: set[str] = set()

    for idx, raw in enumerate(items):
        try:
            m = ModelSchema.model_validate(raw)
            if not m.resolved_urls():
                raise ValueError("must supply either `url` or non-empty `urls`")
        except Exception as e:
            errors.append(f"item {idx}: {e}")
            continue

        if m.name in names_seen:
            dupes.add(m.name)
        names_seen.add(m.name)

    if dupes:
        errors.append(f"duplicate names: {', '.join(sorted(dupes))}")

    return (len(errors) == 0), errors


def load_registry_file(path: Path) -> Dict[str, Any]:
    """Load a registry JSON or YAML file and normalize to {'models': [...]}."""
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in (".yml", ".yaml"):
        if yaml is None:
            raise RuntimeError("YAML requested but PyYAML is not installed")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return {"models": _coerce_to_list(data)}


def load_effective_registry() -> Dict[str, Any]:
    """
    Load/merge builtins + user registry if present.
    Minimal implementation: look for builtins next to this file; otherwise empty.
    """
    here = Path(__file__).resolve().parent
    for name in ("builtins.json", "builtins.yaml", "builtins.yml"):
        p = here / name
        if p.exists():
            try:
                return load_registry_file(p)
            except Exception:
                # fall through to empty if broken; validation will report parse errors when invoked with --path
                pass
    return {"models": []}
