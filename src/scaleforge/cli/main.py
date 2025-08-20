"""ScaleForge CLI entrypoint.

This module provides the main :func:`cli` group used by tests and by
developer-facing tooling.  It keeps imports light at module import time and
pulls in heavy dependencies lazily inside the commands themselves.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from importlib import metadata as im

import click

# Global development-mode flag used by subcommands
DEV_MODE = False

# Placeholder for lazy config loader; tests monkeypatch this attribute
load_config = None  # type: ignore[assignment]


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
    global DEV_MODE, load_config, _CFG
    DEV_MODE = dev
    if dev:
        click.echo("🛠️  Developer mode enabled")

    # Environment setup occurs lazily here so that importing this module is
    # inexpensive.  ``load_config`` is imported once and exposed as a module
    # attribute so tests can monkeypatch it.
    if load_config is None:
        from scaleforge.config.loader import load_config as _load_config
        load_config = _load_config
    from scaleforge.db.models import get_conn, init_db

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
        from scaleforge.backend.selector import get_backend_alias
    except Exception as e:  # pragma: no cover - import error path
        click.echo(f"[detect-backend] import error: {e}", err=True)
        raise SystemExit(2)

    alias, reasons = get_backend_alias(debug=debug)
    if debug:
        click.echo(alias)
        for r in reasons:
            click.echo(f"- {r}")
    else:
        click.echo(alias)


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


# ---------------------------------------------------------------------------
# Demo commands


@cli.command("demo-upscale")
@click.option("-i", "--input", required=True, type=click.Path(exists=True), help="Input image path")
@click.option("-o", "--output", required=True, help="Output image path")
@click.option("-s", "--scale", type=float, default=2.0, show_default=True, help="Upscale factor")
@click.option(
    "--mode",
    type=click.Choice(["nearest", "bilinear", "bicubic", "lanczos"]),
    default="lanczos",
    show_default=True,
    help="Upsampling mode",
)
def demo_upscale(input: str, output: str, scale: float, mode: str) -> None:
    """Demo command for single image upscaling using Pillow"""
    from scaleforge.demo.upscale import upscale_image

    try:
        upscale_image(input_path=input, output_path=output, scale=scale, mode=mode)
    except Exception as e:  # pragma: no cover - runtime error path
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command("demo-batch")
@click.option("-i", "--input-dir", required=True, type=click.Path(exists=True), help="Input directory")
@click.option("-o", "--output-dir", required=True, help="Output directory")
@click.option("-s", "--scale", type=float, default=2.0, show_default=True, help="Upscale factor")
@click.option(
    "--mode",
    type=click.Choice(["nearest", "bilinear", "bicubic", "lanczos"]),
    default="lanczos",
    show_default=True,
    help="Upsampling mode",
)
@click.option("--suffix", default="@scaled", show_default=True, help="Filename suffix for outputs")
@click.option("--include", multiple=True, help="Glob pattern for files to include")
@click.option("--exclude", multiple=True, help="Glob pattern for files to exclude")
@click.option("--limit", type=int, help="Maximum number of files to process")
@click.option("--dry-run", is_flag=True, help="Preview changes without processing")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output files")
def demo_batch(
    input_dir: str,
    output_dir: str,
    scale: float,
    mode: str,
    suffix: str,
    include: tuple[str],
    exclude: tuple[str],
    limit: int,
    dry_run: bool,
    overwrite: bool,
) -> None:
    """Batch process images with demo upscaling"""
    from scaleforge.demo.upscale import batch_upscale

    try:
        batch_upscale(
            input_dir=input_dir,
            output_dir=output_dir,
            scale=scale,
            mode=mode,
            suffix=suffix,
            include_patterns=include,
            exclude_patterns=exclude,
            limit=limit,
            dry_run=dry_run,
            overwrite=overwrite,
        )
    except Exception as e:  # pragma: no cover - runtime error path
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


# Global configuration populated during ``cli`` invocation
_CFG = None


__all__ = ["cli"]

