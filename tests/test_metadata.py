import asyncio
from pathlib import Path

from scaleforge.pipeline.queue import JobQueue
from scaleforge.backend.base import Backend


class RecordingBackend(Backend):
    name = "record"

    def __init__(self):
        self.received_job = None

    async def upscale(self, src: Path, dst: Path, scale: int = 2, tile: int | None = None, job=None):
        self.received_job = job
        dst.write_bytes(src.read_bytes())


def test_metadata_propagation(tmp_path):
    src = tmp_path / "in.png"
    src.write_bytes(b"123")
    db = tmp_path / "sf.db"
    backend = RecordingBackend()
    queue = JobQueue(db, backend)
    queue.enqueue([src], model="realesrgan", scale=4)
    asyncio.run(queue.run())

    assert backend.received_job is not None
    assert backend.received_job.metadata == {"model": "realesrgan", "scale": 4}
