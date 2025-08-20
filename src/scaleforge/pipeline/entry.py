"""Pipeline entry point utilities."""
from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Sequence

from scaleforge.backend.base import Backend, TorchBackend
from scaleforge.db.models import Job, JobStatus, get_conn
from .queue import JobQueue


def _collect_inputs(path: Path) -> Sequence[Path]:
    if path.is_dir():
        return sorted(p for p in path.rglob("*.png") if p.is_file())
    return [path]


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    scale: float = 2.0,
    resume: bool = False,
    verbose: bool = False,
) -> bool:
    """Run the upscaling pipeline using :class:`JobQueue`.

    Parameters
    ----------
    input_path:
        File or directory containing source images. Only ``.png`` files are
        processed when a directory is given.
    output_dir:
        Directory where processed images will be written.
    scale:
        Requested upscale factor. Currently only ``2`` is honoured by the
        internal :class:`JobQueue` implementation.
    resume:
        When ``True`` existing database state is re-used allowing resumed jobs.
    verbose:
        Enable verbose logging.
    """

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    # Use the simple TorchBackend stub for now; heavy backends can hook in later
    backend: Backend = TorchBackend()

    db_path = output_dir / "pipeline.db"
    queue = JobQueue(db_path, backend)

    files = _collect_inputs(input_path)
    if not files:
        logging.warning("No input files found for %s", input_path)
        return False

    queue.enqueue(files, scale=int(scale))

    asyncio.run(queue.run(resume=resume))

    # Move outputs to requested directory
    for src in files:
        produced = src.with_suffix(src.suffix + ".x2.png")
        if produced.exists():
            shutil.move(str(produced), str(output_dir / produced.name))

    # Check for any remaining pending/failed jobs
    with get_conn(db_path) as conn:
        remaining = Job.pending(conn)
        failed = [j for j in remaining if j.status == JobStatus.FAILED]
    return not failed and not remaining


__all__ = ["run_pipeline"]
