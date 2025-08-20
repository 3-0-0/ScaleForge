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
