import sqlite3

from scaleforge.db.models import Job, JobStatus
from scaleforge.utils.hash import hash_params


def _make_conn(tmp_path):
    """Create and return a database connection that remains open."""
    from scaleforge.db.models import get_conn
    db = tmp_path / "sf.db"
    # Create connection outside context manager to keep it open
    conn = sqlite3.connect(db)
    # Ensure schema is initialized
    with get_conn(conn):
        pass
    return conn


def test_create_or_skip(tmp_path):
    conn = _make_conn(tmp_path)
    img = tmp_path / "a.png"
    img.write_bytes(b"123")
    h = hash_params(img, {"scale": 2})
    Job.create_or_skip(conn, {"src_path": str(img), "hash": h})
    assert Job.create_or_skip(conn, {"src_path": str(img), "hash": h}) is None


def test_pending_includes_retryable_failed(tmp_path):
    conn = _make_conn(tmp_path)
    j1 = Job.create_or_skip(conn, {"src_path": "f1", "hash": "h1"})
    j2 = Job.create_or_skip(conn, {"src_path": "f2", "hash": "h2"})
    j1.set_status(conn, JobStatus.FAILED, "err")  # attempts=1
    j2.set_status(conn, JobStatus.DONE)
    pending = {j.id for j in Job.pending(conn)}
    assert j1.id in pending and j2.id not in pending


def test_attempts_increment(tmp_path):
    conn = _make_conn(tmp_path)
    j = Job.create_or_skip(conn, {"src_path": "f", "hash": "h"})
    assert j.attempts == 0
    j.set_status(conn, JobStatus.FAILED, "boom")
    assert j.attempts == 1
