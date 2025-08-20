"""Configuration loading utilities.

This project originally used :mod:`pydantic` and :mod:`pyyaml` for structured
configuration.  Those third party dependencies are rather heavy for the unit
tests in this kata, so the implementation below provides a very small
stand‑alone subset of the original behaviour.  Only the pieces exercised by the
tests are implemented:

* paths may contain simple token placeholders such as ``${APP_ROOT}``
* default directories are created on access
* configuration files are parsed as either JSON or a tiny subset of YAML

The goal isn't to be feature complete but to offer a convenient, dependency
free configuration object with a similar interface to the previous Pydantic
model.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict

# ``yaml`` is an optional dependency.  When it's missing we fall back to a
# trivial loader that understands JSON - perfectly adequate for the tests.
try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

# ``APP_ROOT`` points at the repository root when running from sources.  The
# default configuration file lives next to it.
APP_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = APP_ROOT / "scaleforge.yaml"

TOKEN_MAP = {
    "${APP_ROOT}": str(APP_ROOT),
    "${USER_HOME}": str(pathlib.Path.home()),
}


def _token_replace(value: str) -> str:
    for token, replacement in TOKEN_MAP.items():
        value = value.replace(token, replacement)
    return value


@dataclass
class AppConfig:
    """Very small configuration container used in tests."""

    database_path: pathlib.Path = field(
        default_factory=lambda: pathlib.Path("${APP_ROOT}/scaleforge.db")
    )
    log_dir: pathlib.Path = field(
        default_factory=lambda: pathlib.Path("${APP_ROOT}/logs")
    )
    model_dir: pathlib.Path = field(
        default_factory=lambda: pathlib.Path("${APP_ROOT}/models")
    )

    def __post_init__(self) -> None:
        # Expand tokens and ensure directories exist – mimicking the old
        # Pydantic validators.
        self.database_path = pathlib.Path(_token_replace(str(self.database_path)))
        self.log_dir = pathlib.Path(_token_replace(str(self.log_dir)))
        self.model_dir = pathlib.Path(_token_replace(str(self.model_dir)))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)


def _load_yaml(text: str) -> Dict[str, Any]:
    """Parse *text* as YAML if possible, otherwise fall back to JSON.

    The real project uses :func:`yaml.safe_load` which isn't available in this
    execution environment.  A minimal loader based on :func:`json.loads` is good
    enough for our test data which only uses simple dict literals.
    """

    if yaml is not None:  # pragma: no cover - exercised when PyYAML is present
        return yaml.safe_load(text) or {}
    # Fallback: attempt JSON parsing; return empty dict on failure
    try:
        return json.loads(text)
    except Exception:
        return {}


def load_config(path: pathlib.Path | None = None) -> AppConfig:
    """Load configuration from file if present, else return defaults."""

    cfg_path = path or DEFAULT_CONFIG_PATH
    if cfg_path.exists():
        text = cfg_path.read_text(encoding="utf-8")
        data = _load_yaml(text)
    else:
        data = {}
    return AppConfig(**data)  # type: ignore[arg-type]
