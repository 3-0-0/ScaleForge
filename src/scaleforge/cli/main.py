
"""ScaleForge CLI entrypoint."""

from __future__ import annotations
from importlib.metadata import version as get_version

import asyncio
import json
import sys
from pathlib import Path
from typing import List

from scaleforge.models.downloader import ModelDownloader
from scaleforge.gui.app import ScaleForgeApp
from scaleforge.db.models import get_conn


import click
import logging
from pydantic import BaseModel
DEV_MODE = False  # Global dev mode flag

@click.version_option(version=get_version('scaleforge'), message='ScaleForge %(version)s')
@click.group()
@click.option('--dev', is_flag=True, help='Enable developer mode (debug logging, console, etc)')
def cli(dev):
    """ScaleForge command line interface."""
    global DEV_MODE
    DEV_MODE = dev
    if dev:
        click.echo("🛠️  Developer mode enabled")

from scaleforge.config.loader import load_config
from scaleforge.db.models import init_db
from scaleforge.backend.selector import get_backend
from scaleforge.pipeline.queue import JobQueue
from scaleforge.cli.info import info as info_command

from .utils import print_status


@cli.group("model")
def model_command():
    """Manage models (install, hash, etc)."""
    pass


@model_command.command("install")
@click.argument("model", required=True)
def model_install(model):
    """Install a model."""
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
    downloader.download_model(model)
    click.echo("✅ Done.")


@model_command.command("hash")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def model_hash(path: Path):
    """Compute SHA256 hash of a model file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    digest = sha256.hexdigest()
    click.echo(f"🔢 SHA256: {digest}")



@cli.command()
def gui():
    """Launch the ScaleForge GUI."""
    ScaleForgeApp().run()

@cli.command()
@click.option('--debug', is_flag=True, help='Show detailed backend detection info')
@click.option('--probe', is_flag=True, help='Force fresh GPU capability detection')
def detect_backend(debug, probe):
    """Detect and display GPU backend capabilities."""
    from scaleforge.backend import detect_gpu_caps, load_caps
    from scaleforge.config.loader import load_config
    from datetime import datetime
    import json
    
    cfg = load_config()
    app_root = Path(str(cfg.model_dir)).parent
    
    if probe:
        caps = detect_gpu_caps(app_root, force_probe=True)
        source = "probed"
    else:
        caps = load_caps(app_root) or detect_gpu_caps(app_root, force_probe=True)
        source = "cached" if not probe else "probed"
    
    if debug:
        click.echo(json.dumps({
            "vendor": caps["vendor"],
            "backend": caps["backend"],
            "max_tile_size": caps["max_tile_size"],
            "max_megapixels": caps["max_megapixels"],
            "detected_at": caps["detected_at"],
            "cache_path": str(app_root / "gpu_caps.json"),
            "source": source
        }, indent=2))
    else:
        click.echo(
            f"backend={caps['backend']} "
            f"vendor={caps['vendor']} "
            f"tile={caps['max_tile_size']} "
            f"mpx={caps['max_megapixels']:.1f} "
            f"({source})"
        )

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".gif"
}

def is_supported_image(path: Path) -> bool:
    """Check if file has a supported image extension."""
    return path.suffix.lower() in SUPPORTED_EXTENSIONS

cfg = load_config()
# Initialize database on first connection
with get_conn(cfg.database_path) as conn:
    init_db(conn)


@click.group()
def cli():
    """ScaleForge - AI-powered image upscaler & resizer using Real-ESRGAN
    
    Supports: .jpg, .png, .bmp, .webp, .tiff, and .gif (first frame only)


cli.add_command(model_command)


    
    Commands:
      run    - Process images with AI upscaling
      info   - List supported models and backends
    """
    pass

cli.add_command(info_command)




class PlanItem(BaseModel):
    src: str
    dst: str
    scale: int = 2

@cli.command()
@click.option("--input", "-i", "inputs", type=click.Path(path_type=Path), 
              multiple=True, help="Input file(s)/directory(ies) to process (supports glob patterns)")
@click.argument("inputs_fallback", nargs=-1, type=click.Path(path_type=Path),
               required=False)
@click.option("--output", "-o", "out_dir", type=click.Path(path_type=Path),
             default="${APP_ROOT}/outputs", show_default=True,
             help="Output directory for processed files (default: ./outputs)")
@click.option("--dry-run", is_flag=True,
             help="Show planned operations without executing")
@click.option("--verbose", is_flag=True,
             help="Show detailed progress and statistics")
@click.option("--model", default="realesrgan-x4plus", show_default=True,
             help="""AI model to use. Available options:
  - realesrgan-x4plus: General purpose images (default)
  - realesr-general-x4v3: Enhanced details for photos
  - realesr-animevideov3: Optimized for anime/cartoons

Supported formats: .jpg, .png, .bmp, .webp, .tiff, .gif (first frame only)

Examples:
  scaleforge run -i *.jpg
  scaleforge run photos/ --output upscaled/ --model realesr-general-x4v3
  scaleforge run anime.gif --model realesr-animevideov3 --verbose""")
@click.option("--concurrency", "-j", type=int, default=None,
             help="Number of parallel jobs (default: CPU cores)")
@click.option("--resume", is_flag=True,
             help="Resume previous interrupted run")
@click.option("--force-backend", type=click.Choice(["torch", "ncnn", "cpu"]),
             help="Force specific backend (for debugging)")
@click.option("--reset-db", is_flag=True,
             help="Reset job tracking database (use with caution)")
@click.option("--scale", type=click.Choice(["2", "4"], case_sensitive=False),
             default=None,
             help="Upscale factor (2 or 4). Overrides model default.")
def run(inputs: List[Path], inputs_fallback: tuple[Path], dry_run: bool, 
       out_dir: Path, model: str, concurrency: int, 
       resume: bool, reset_db: bool, verbose: bool, 
       scale: str | None = None, force_backend: str | None = None):
    """Upscale images using AI models.
    
    Args:
        verbose: If True, show detailed processing information
        scale: Upscale factor (2=2x, 4=4x) or None for model default
    """
    scale_int = int(scale) if scale else None
    # Track processing stats
    processed_files = 0
    success_count = 0
    warning_count = 0
    error_count = 0


    def update_status(file: Path, status: str, message: str = ""):
        """Update and display processing status."""
        nonlocal processed_files, success_count, warning_count, error_count
        processed_files += 1
        if status == "success":
            success_count += 1
        elif status == "warning":
            warning_count += 1
        else:
            error_count += 1
        print_status(file, status, message)


    if dry_run:
        click.echo("🔍 Dry run mode - showing planned operations:")
        for p in inputs + list(inputs_fallback):
            if p.is_dir():
                update_status(p, "success", "Directory will be processed")
                for img in p.rglob("*.png"):
                    update_status(img, "success", "Would upscale")
            else:
                update_status(p, "success", "Would upscale")
        return

    # Debug imports
    try:
        from scaleforge.models.downloader import ModelDownloader
        click.echo("✅ ModelDownloader import successful") if verbose else None
    except ImportError as e:
        click.echo(f"❌ ModelDownloader import failed: {e}", err=True)
        raise

    if verbose:
        click.echo("🚀 ScaleForge run started (verbose mode)")
        click.echo(f"Inputs: {[*inputs, *inputs_fallback]}")
        click.echo(f"Output directory: {out_dir}")
        click.echo(f"Model: {model} (scale: {scale}x)")
        click.echo(f"Concurrency: {concurrency}")

        click.echo("\nProcessing status:")
        click.echo("----------------")


    downloader = ModelDownloader()
    registry = downloader.get_registry()
    
    if model not in registry:
        available = "\n".join(f" • {name}" for name in registry.keys())
        raise click.BadParameter(
            f"Unknown model: {model}\nAvailable models:\n{available}"
        )
        
    if not downloader.is_model_downloaded(model):
        click.echo(f"📥 Model not found locally: {model}")
        click.echo(f"🔽 Downloading from: {registry[model]['url']}")
        try:
            ModelDownloader().download_model(model)
            click.echo("✅ Download complete")
        except Exception as e:
            raise click.ClickException(f"Failed to download model: {str(e)}")
    # Combine --input and positional args
    all_inputs = list(inputs) + list(inputs_fallback)
    if not all_inputs:
        click.echo("❌ No input files provided.", err=True)
        click.echo("Try:", err=True)
        click.echo("  scaleforge run *.jpg", err=True)
        click.echo("  scaleforge run photos/ --output output/", err=True)
        raise click.Abort()


    # Check for GIF limitations
    from ..models.downloader import ModelDownloader
    ModelDownloader.check_gif_limitations(all_inputs)


        
    # Validate input files exist
    missing_files = [str(p) for p in all_inputs if not p.exists()]
    if missing_files:


        # Update status for missing files
        for f in missing_files:
            update_status(Path(f), "error", "File not found")




        for f in missing_files:
            update_status(Path(f), "error", "File not found")


        click.echo("❌ Some input files could not be found:", err=True)
        for f in missing_files:
            click.echo(f"  {f}", err=True)
        click.echo("\nPlease check the paths and try again.", err=True)
        raise click.Abort()
        
    if reset_db:
        from scaleforge.db.models import reset_db
        reset_db(cfg.database_path)
        click.echo("Database reset complete")

    out_dir = Path(str(out_dir).replace("${APP_ROOT}", str(cfg.model_dir.parent)))
    
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        # Test write permission
        (out_dir / ".permission_test").touch()
        (out_dir / ".permission_test").unlink()
    except OSError as e:
        click.echo(f"Warning: Cannot write to output directory ({e}). Using temp directory instead.")
        import tempfile
        out_dir = Path(tempfile.mkdtemp(prefix="scaleforge-output-"))
        click.echo(f"Using temporary directory: {out_dir}")

    targets: List[PlanItem] = []
    skipped_files = 0
    gif_warning_shown = False
    
    for p in inputs:
        if p.is_dir():
            for img in p.rglob("*"):
                if not is_supported_image(img):
                    if verbose:
                        click.echo(f"Skipping unsupported file: {img}")
                    skipped_files += 1
                    continue
                    
                if img.suffix.lower() == ".gif" and verbose and not gif_warning_shown:
                    click.echo("⚠️  Warning: Animated GIFs are not fully supported - only the first frame will be processed")
                    gif_warning_shown = True
                    
                targets.append(PlanItem(
                    src=str(img),
                    dst=str(out_dir / img.name),
                    scale=scale
                ))
                if verbose:
                    click.echo(f"• Queued: {img} → {out_dir/img.name}")
        else:
            targets.append(PlanItem(
                src=str(p),
                dst=str(out_dir / p.name),
                scale=scale
            ))
            if verbose:
                click.echo(f"• Queued: {p} → {out_dir/p.name}")

    if verbose and targets:
        click.echo(f"\nProcessing {len(targets)} files with {concurrency} workers...")

    if dry_run:
        if verbose:
            click.echo("\nSummary:")
            click.echo(f" • Files queued:      {len(targets)}")
            click.echo(f" • Files skipped:     {skipped_files}")
            click.echo(f" • Output directory:  {out_dir}")
        click.echo(json.dumps([t.model_dump() for t in targets], indent=2))
        sys.exit(0)

    backend = get_backend()
    logger.info(f"Backend initialized: {type(backend).__name__}")
    jq = JobQueue(cfg.database_path, backend, concurrency)
    if not resume:
        jq.enqueue([t.src for t in targets])
    asyncio.run(jq.run(resume=resume))

    if verbose:
        click.echo("\nSummary:")
        click.echo(f" • Files processed:   {len(targets)}")
        click.echo(f" • Files skipped:     {skipped_files}")
        click.echo(f" • Output directory:  {out_dir}")


if __name__ == "__main__":
    cli()




