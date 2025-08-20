"""ScaleForge CLI entrypoint.

This module provides the main :func:`cli` group used by tests and by
developer-facing tooling.  It keeps imports light at module import time and
pulls in heavy dependencies lazily inside the commands themselves.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import click

# Global development-mode flag used by subcommands
DEV_MODE = False


from importlib import metadata as im


def _sf_version() -> str:
    try:
        return im.version("scaleforge")
    except Exception:
        try:
            from scaleforge import __version__  # type: ignore
            return __version__
        except Exception:
            return "0.0.0"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--dev", is_flag=True, help="Enable developer mode (debug logging, console, etc)")
@click.version_option(version=_sf_version(), message="ScaleForge %(version)s")
def cli(dev: bool) -> None:
    """ScaleForge command line interface."""
    global DEV_MODE
    DEV_MODE = dev
    if dev:
        click.echo("🛠️  Developer mode enabled")

    # Environment setup occurs lazily here so that importing this module is
    # inexpensive.  Helpers such as ``load_config`` are imported once and kept
    # available for subcommands through the global ``_CFG`` variable.
    from scaleforge.config.loader import load_config
    from scaleforge.db.models import get_conn, init_db

    global _CFG
    _CFG = load_config()
    with get_conn(_CFG.database_path) as conn:
        init_db(conn)


# ---------------------------------------------------------------------------
# Subcommands


@cli.command("detect-backend")
@click.option("--debug", is_flag=True, help="Verbose backend detection.")
def detect_backend(debug: bool) -> None:
    """Detect the best compute backend and print the decision."""
    try:
        try:
            from scaleforge.backend.selector import detect_backend as _detect  # type: ignore
        except Exception:
            from scaleforge.backend.detector import detect_backend as _detect  # type: ignore
    except Exception as e:  # pragma: no cover - import error path
        click.echo(f"[detect-backend] import error: {e}", err=True)
        raise SystemExit(2)

    click.echo(_detect(debug=debug))


@cli.group("model")
def model_cmd() -> None:
    """Manage models (install, hash, etc)."""


@model_cmd.command("install")
@click.argument("model", required=True)
def model_install(model: str) -> None:
    """Install a model from the registry."""
    from scaleforge.models.downloader import ModelDownloader

    downloader = ModelDownloader()
    registry = downloader.get_registry()
    if model not in registry:
        available = "\n".join(f" • {name}" for name in registry.keys())
        raise click.BadParameter(
            f"Unknown model: {model}\nAvailable models:\n{available}"
        )

    if downloader.is_model_downloaded(model):
        click.echo(f"✅ Model already downloaded: {model}")
        return

    click.echo(f"📦 Installing model: {model}")
    try:
        downloader.download_model(model)
    except Exception as exc:  # pragma: no cover - network/IO errors
        raise click.ClickException(str(exc)) from exc
    click.echo("✅ Done.")


@model_cmd.command("hash")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def model_hash(path: Path) -> None:
    """Compute SHA256 hash of a model file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    click.echo(f"🔢 SHA256: {sha256.hexdigest()}")


@cli.command()
def gui() -> None:
    """Launch the ScaleForge GUI."""
    from scaleforge.gui.app import ScaleForgeApp

    ScaleForgeApp().run()


@cli.command("run")
@click.argument("input_path", type=click.Path(exists=True, path_type=str))
@click.option("--output", "-o", type=click.Path(path_type=str), required=True, help="Output directory")
@click.option("--scale", type=float, default=2.0, show_default=True, help="Upscale factor")
@click.option("--dry-run", is_flag=True, help="Check pipeline without running heavy steps")
@click.option("--resume", is_flag=True, help="Resume if partial outputs exist")
@click.option("--verbose", is_flag=True, help="Verbose logging")
def run_cmd(
    input_path: str,
    output: str,
    scale: float,
    dry_run: bool,
    resume: bool,
    verbose: bool,
) -> None:
    """Run the ScaleForge pipeline."""
    from pathlib import Path

    Path(output).mkdir(parents=True, exist_ok=True)
    if dry_run:
        click.echo(
            f"[dry-run] input={input_path} output={output} scale={scale} resume={resume} verbose={verbose}"
        )
        return

    try:
        from scaleforge.pipeline.entry import run_pipeline  # type: ignore
    except Exception as e:  # pragma: no cover - import error path
        click.echo(f"[run] pipeline import error: {e}", err=True)
        raise SystemExit(2)

    ok = run_pipeline(
        input_path=input_path,
        output_dir=output,
        scale=scale,
        resume=resume,
        verbose=verbose,
    )
    raise SystemExit(0 if ok else 1)


# Global configuration populated during ``cli`` invocation
_CFG = None


__all__ = ["cli"]

