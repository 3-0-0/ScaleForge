from __future__ import annotations

import click

from .main import cli


@cli.group("demo")
def demo() -> None:  # pragma: no cover - simple wrapper
    """Demo commands."""


@demo.command("upscale")
@click.option("--in", "in_path", required=True, type=click.Path(exists=True, dir_okay=False), help="Input image")
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False), help="Output image")
@click.option("--scale", type=int, default=2, show_default=True, help="Upscale factor")
def demo_upscale(in_path: str, out_path: str, scale: int) -> None:
    """CPU-only image resize demo using Pillow."""
    from scaleforge.demo.upscale import upscale_image
    from scaleforge.backend.selector import get_backend_alias

    upscale_image(in_path, out_path, scale=float(scale), mode="lanczos")
    alias, _ = get_backend_alias()
    click.echo(alias)


@cli.command("demo-batch")
@click.option("-i", "--input-dir", "input_dir", required=True, type=click.Path(exists=True, file_okay=False, path_type=str), help="Input directory")
@click.option("-o", "--output-dir", "output_dir", required=True, type=click.Path(file_okay=False, path_type=str), help="Output directory")
@click.option("-s", "--scale", type=float, default=2.0, show_default=True, help="Upscale factor")
@click.option("--mode", default="lanczos", show_default=True, help="Upsampling mode")
@click.option("--suffix", default="@scaled", show_default=True, help="Filename suffix for outputs")
@click.option("--include", multiple=True, type=str, help="Glob pattern of files to include")
@click.option("--exclude", multiple=True, type=str, help="Glob pattern of files to exclude")
@click.option("--limit", type=int, help="Maximum number of files to process")
@click.option("--dry-run", is_flag=True, help="Preview without processing")
@click.option("--overwrite", is_flag=True, help="Overwrite existing files")
@click.option("--debug", is_flag=True, help="Verbose logging")
def demo_batch(
    input_dir: str,
    output_dir: str,
    scale: float,
    mode: str,
    suffix: str,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    limit: int | None,
    dry_run: bool,
    overwrite: bool,
    debug: bool,
) -> None:
    """CPU-only batch image resize demo."""
    from scaleforge.demo.upscale import batch_upscale

    batch_upscale(
        input_dir,
        output_dir,
        scale=scale,
        mode=mode,
        suffix=suffix,
        include_patterns=include,
        exclude_patterns=exclude,
        limit=limit,
        dry_run=dry_run,
        overwrite=overwrite,
        debug=debug,
    )

demo.add_command(demo_batch, "batch")
