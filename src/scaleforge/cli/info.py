

from __future__ import annotations

import platform

import click

from scaleforge.backend.selector import get_backend_alias
from .main import _CFG, cli, load_config


@cli.command("info")
def info() -> None:
    """Show system and configuration information."""
    cfg = _CFG
    if cfg is None:
        loader = load_config
        if loader is None:  # pragma: no cover - should be loaded by ``cli``
            from scaleforge.config.loader import load_config as _load_config

            loader = _load_config
        cfg = loader()

    click.echo(f"Detected backend: {get_backend_alias()[0]}")
    if cfg is not None:
        click.echo(f"Database path: {cfg.database_path}")
        click.echo(f"Log dir: {cfg.log_dir}")
        click.echo(f"Model dir: {cfg.model_dir}")

    click.echo(f"Python: {platform.python_version()}")
    click.echo(f"OS: {platform.platform()}")

