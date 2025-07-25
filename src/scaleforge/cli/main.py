"""ScaleForge CLI entrypoint."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import List

import click
from pydantic import BaseModel

from scaleforge.config.loader import load_config
from scaleforge.db.models import init_db
from scaleforge.backend.selector import get_backend
from scaleforge.pipeline.queue import JobQueue

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
@click.argument("inputs", nargs=-1, type=click.Path(path_type=Path))
@click.option("--dry-run", is_flag=True, help="Print plan and exit.")
@click.option("--output", "out_dir", type=click.Path(path_type=Path), default="${APP_ROOT}/outputs")
@click.option("-j", "--concurrency", default=1, show_default=True, help="Number of parallel workers")
@click.option("--resume", is_flag=True, help="Resume unfinished jobs")

def run(inputs: List[Path], dry_run: bool, out_dir: Path, concurrency: int, resume: bool):
    """Upscale INPUTS (files or dirs)."""
    out_dir = Path(str(out_dir).replace("${APP_ROOT}", str(cfg.model_dir.parent)))
    out_dir.mkdir(parents=True, exist_ok=True)

    targets: List[PlanItem] = []
    for p in inputs:
        if p.is_dir():
            for img in p.rglob("*.png"):
                targets.append(PlanItem(src=str(img), dst=str(out_dir / img.name)))
        else:
            targets.append(PlanItem(src=str(p), dst=str(out_dir / p.name)))

    if dry_run:
        click.echo(json.dumps([t.model_dump() for t in targets], indent=2))
        sys.exit(0)

    backend = get_backend()
    jq = JobQueue(cfg.database_path, backend, concurrency)
    if not resume:
        jq.enqueue(inputs)
    asyncio.run(jq.run(resume=resume))


if __name__ == "__main__":
    cli()
