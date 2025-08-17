from __future__ import annotations
import click

def _sf_version() -> str:
    try:
        from importlib import metadata as im
        return im.version("scaleforge")
    except Exception:
        try:
            from scaleforge import __version__  # type: ignore
            return __version__
        except Exception:
            return "0.0.0"

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=_sf_version(), prog_name="ScaleForge")
def cli() -> None:
    """ScaleForge CLI (help-safe). Heavy imports are lazy inside subcommands."""
    pass

# Demo commands
@cli.command("demo-upscale")
@click.option("-i", "--input", required=True, type=click.Path(exists=True), help="Input image path")
@click.option("-o", "--output", required=True, help="Output image path")
@click.option("-s", "--scale", type=float, default=2.0, show_default=True, help="Upscale factor")
@click.option("--mode", type=click.Choice(["nearest", "bilinear", "bicubic", "lanczos"]), 
              default="lanczos", show_default=True, help="Upsampling mode")
def demo_upscale(input: str, output: str, scale: float, mode: str) -> None:
    """Demo command for single image upscaling using Pillow"""
    from scaleforge.demo.upscale import upscale_image
    try:
        upscale_image(input_path=input, output_path=output, scale=scale, mode=mode)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

@cli.command("demo-batch")
@click.option("-i", "--input-dir", required=True, type=click.Path(exists=True), help="Input directory")
@click.option("-o", "--output-dir", required=True, help="Output directory")
@click.option("-s", "--scale", type=float, default=2.0, show_default=True, help="Upscale factor")
@click.option("--mode", type=click.Choice(["nearest", "bilinear", "bicubic", "lanczos"]), 
              default="lanczos", show_default=True, help="Upsampling mode")
@click.option("--suffix", default="@scaled", show_default=True, help="Filename suffix for outputs")
@click.option("--include", multiple=True, help="Glob pattern for files to include")
@click.option("--exclude", multiple=True, help="Glob pattern for files to exclude")
@click.option("--limit", type=int, help="Maximum number of files to process")
@click.option("--dry-run", is_flag=True, help="Preview changes without processing")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output files")
def demo_batch(input_dir: str, output_dir: str, scale: float, mode: str, suffix: str,
              include: tuple[str], exclude: tuple[str], limit: int, dry_run: bool, overwrite: bool) -> None:
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
            overwrite=overwrite
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

@cli.command("detect-backend")
@click.option("--debug", is_flag=True, help="Verbose backend detection.")
def detect_backend(debug: bool) -> None:
    """Detect the best compute backend and print the decision."""
    try:
        try:
            from scaleforge.backend.selector import detect_backend as _detect  # type: ignore
        except Exception:
            from scaleforge.backend.detector import detect_backend as _detect  # type: ignore
    except Exception as e:
        click.echo(f"[detect-backend] import error: {e}", err=True)
        raise SystemExit(2)
    click.echo(_detect(debug=debug))

@cli.command("run")
@click.argument("input_path", type=click.Path(exists=True, path_type=str))
@click.option("--output", "-o", type=click.Path(path_type=str), required=True, help="Output directory")
@click.option("--scale", type=float, default=2.0, show_default=True, help="Upscale factor")
@click.option("--dry-run", is_flag=True, help="Check pipeline without running heavy steps")
@click.option("--resume", is_flag=True, help="Resume if partial outputs exist")
@click.option("--verbose", is_flag=True, help="Verbose logging")
def run_cmd(input_path: str, output: str, scale: float, dry_run: bool, resume: bool, verbose: bool) -> None:
    """Run the ScaleForge pipeline."""
    from pathlib import Path
    Path(output).mkdir(parents=True, exist_ok=True)
    if dry_run:
        click.echo(f"[dry-run] input={input_path} output={output} scale={scale} resume={resume} verbose={verbose}")
        return
    try:
        from scaleforge.pipeline.entry import run_pipeline  # type: ignore
    except Exception as e:
        click.echo(f"[run] pipeline import error: {e}", err=True)
        raise SystemExit(2)
    ok = run_pipeline(input_path=input_path, output_dir=output, scale=scale, resume=resume, verbose=verbose)
    raise SystemExit(0 if ok else 1)
