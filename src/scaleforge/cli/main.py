"""ScaleForge CLI entrypoint."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import List

import click
import logging
from pydantic import BaseModel

from scaleforge.config.loader import load_config
from scaleforge.db.models import init_db
from scaleforge.backend.selector import get_backend
from scaleforge.pipeline.queue import JobQueue

logger = logging.getLogger(__name__)

cfg = load_config()
init_db(cfg.database_path)


class PlanItem(BaseModel):
    src: str
    dst: str
    scale: int = 2


@click.group()
def cli():
    """ScaleForge CLI."""


@cli.command()
@click.option("--input", "inputs", type=click.Path(path_type=Path), 
              multiple=True, help="Input file(s)/directory(ies) to process")
@click.argument("inputs_fallback", nargs=-1, type=click.Path(path_type=Path),
               required=False)
@click.option("--output", "out_dir", type=click.Path(path_type=Path),
             default="${APP_ROOT}/outputs", show_default=True,
             help="Output directory path for processed files")
@click.option("--dry-run", is_flag=True,
             help="Generate processing plan without execution")
@click.option("--scale", type=int, default=2, show_default=True,
             help="Upscale factor (2=2x, 4=4x etc.)")
@click.option("--model", default="realesrgan-x4plus", show_default=True,
             help="AI model: realesrgan-x4plus|realesrgan-x4plus-anime")
@click.option("-j", "--concurrency", default=1, show_default=True,
             help="Max parallel jobs (CPU/GPU dependent)")
@click.option("--resume", is_flag=True,
             help="Resume previous incomplete jobs")
@click.option("--reset-db", is_flag=True,
             help="Reset job tracking database (use with caution)")

def run(inputs: List[Path], inputs_fallback: tuple[Path], dry_run: bool, 
       out_dir: Path, scale: int, model: str, concurrency: int, 
       resume: bool, reset_db: bool):
    """Upscale images using AI models.
    
    Examples:
      scaleforge run --input photo.jpg --output ./results
      scaleforge run --input ./photos --scale 4 -j 4
      scaleforge run *.png --model realesrgan-x4plus-anime
      scaleforge run --input file1.jpg file2.jpg  # Alternative syntax
    """
    # Combine --input and positional args
    all_inputs = list(inputs) + list(inputs_fallback)
    if not all_inputs:
        raise click.UsageError("No input files specified")
    if reset_db:
        from scaleforge.db.models import reset_db
        reset_db(cfg.database_path)
        click.echo("Database reset complete")

    out_dir = Path(str(out_dir).replace("${APP_ROOT}", str(cfg.model_dir.parent)))
    out_dir.mkdir(parents=True, exist_ok=True)

    targets: List[PlanItem] = []
    for p in inputs:
        if p.is_dir():
            for img in p.rglob("*.png"):
                targets.append(PlanItem(
                    src=str(img),
                    dst=str(out_dir / img.name),
                    scale=scale
                ))
        else:
            targets.append(PlanItem(
                src=str(p),
                dst=str(out_dir / p.name),
                scale=scale
            ))

    if dry_run:
        click.echo(json.dumps([t.model_dump() for t in targets], indent=2))
        sys.exit(0)

    backend = get_backend()
    logger.info(f"Backend initialized: {type(backend).__name__}")
    jq = JobQueue(cfg.database_path, backend, concurrency)
    if not resume:
        jq.enqueue([t.src for t in targets])
    asyncio.run(jq.run(resume=resume))


if __name__ == "__main__":
    cli()
