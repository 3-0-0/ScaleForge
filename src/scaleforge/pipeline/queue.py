"""Asynchronous JobQueue implementation for the Sprint-2 stub MVP."""
from __future__ import annotations

import asyncio
import inspect
import logging
import random
from pathlib import Path
from typing import Iterable

from scaleforge.backend.base import Backend, BackendError
from scaleforge.db.models import Job, JobStatus, get_conn
from scaleforge.utils.hash import hash_params

logger = logging.getLogger(__name__)


class JobQueue:
    """Manage persistent jobs with retry / resume logic."""

    def __init__(self, db_path: Path, backend: Backend, concurrency: int = 1):
        self.db_path = Path(db_path)
        self.backend = backend
        self.concurrency = max(1, int(concurrency or 1))

    # ------------------------------------------------------------------
    def enqueue(self, inputs: Iterable[Path], model: str = None, scale: int = None):
        """Add new source files to the *jobs* table if not present."""
        params = {
            "backend": self.backend.name,
            "model": model,
            "scale": scale or 2  # Default to 2x if not specified
        }
        with get_conn(self.db_path) as conn:
            for p in inputs:
                p = Path(p)
                if p.is_dir():
                    files = list(p.rglob("*.png"))
                else:
                    files = [p]
                for img in files:
                    Job.create_or_skip(
                        conn,
                        {
                            "src_path": str(img),
                            "hash": hash_params(img, params),
                            "metadata": {
                                "model": model,
                                "scale": scale
                            }
                        },
                    )

    # ------------------------------------------------------------------
    async def run(self, *, resume: bool = False):  # noqa: D401
        """Process pending jobs with *concurrency* async workers."""
        workers = [asyncio.create_task(self._worker(wid)) for wid in range(self.concurrency)]
        await asyncio.gather(*workers)

    # ------------------------------------------------------------------
    async def _worker(self, wid: int):  # noqa: C901 – small and contained
        delay = 1.0
        while True:
            with get_conn(self.db_path) as conn:
                pending = Job.pending(conn, limit=1)
                if not pending:
                    return  # nothing left to do
                job = pending[0]
                job.set_status(conn, JobStatus.UPSCALED_RAW)

            try:
                src = Path(job.src_path)
                dst = src.with_suffix(src.suffix + ".x2.png")
                kwargs = {}
                if "job" in inspect.signature(self.backend.upscale).parameters:
                    kwargs["job"] = job
                await self.backend.upscale(src, dst, **kwargs)
                with get_conn(self.db_path) as conn:
                    job.set_status(conn, JobStatus.DONE)
                delay = 1.0  # reset back-off on success
            except BackendError as exc:
                logger.error("Worker %s fatal: %s", wid, exc)
                with get_conn(self.db_path) as conn:
                    job.set_status(conn, JobStatus.FAILED, error=str(exc))
                return  # stop worker on fatal backend error
            except Exception as exc:  # noqa: BLE001 – treat as transient
                logger.warning("Worker %s transient: %s", wid, exc)
                # mark failed so attempts increments; will be retried by pending()
                with get_conn(self.db_path) as conn:
                    job.set_status(conn, JobStatus.FAILED, error=str(exc))
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8) + random.random()
