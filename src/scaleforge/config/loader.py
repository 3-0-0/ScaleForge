"""Configuration loading using Pydantic v2."""

from __future__ import annotations

import os
import pathlib
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # /src/scaleforge/..
DEFAULT_CONFIG_PATH = APP_ROOT / "scaleforge.yaml"

TOKEN_MAP = {
    "${APP_ROOT}": str(APP_ROOT),
    "${USER_HOME}": str(pathlib.Path.home()),
}


def _token_replace(value: str) -> str:
    for token, replacement in TOKEN_MAP.items():
        value = value.replace(token, replacement)
    return value


class AppConfig(BaseModel):
    """Application configuration root model."""

    database_path: pathlib.Path = Field(default_factory=lambda: pathlib.Path("${APP_ROOT}/scaleforge.db"))
    log_dir: pathlib.Path = Field(default_factory=lambda: pathlib.Path("${APP_ROOT}/logs"))
    model_dir: pathlib.Path = Field(default_factory=lambda: pathlib.Path("${APP_ROOT}/models"))

    class Config:
        extra = "ignore"

    @field_validator("database_path", "log_dir", "model_dir", mode="before")
    @classmethod
    def _expand_tokens(cls, v: Any):  # noqa: ANN401
        if isinstance(v, str):
            v = pathlib.Path(_token_replace(v))
        return v

    @model_validator(mode="after")
    def _create_dirs(self):  # noqa: D401
        """Ensure directories exist."""
        if isinstance(self.log_dir, pathlib.Path):
            self.log_dir.mkdir(parents=True, exist_ok=True)
        if isinstance(self.model_dir, pathlib.Path):
            self.model_dir.mkdir(parents=True, exist_ok=True)
        return self


def load_config(path: pathlib.Path | None = None) -> AppConfig:
    """Load configuration from YAML file if present, else defaults."""
    cfg_path = path or DEFAULT_CONFIG_PATH
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as fh:
            data: Dict[str, Any] = yaml.safe_load(fh) or {}
    else:
        data = {}
    return AppConfig(**data)  # type: ignore[arg-type]
