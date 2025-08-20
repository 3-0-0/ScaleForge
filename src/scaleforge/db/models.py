"""SQLite models and helper utilities for ScaleForge."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Any, Mapping

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schema management
# ---------------------------------------------------------------------------

SCHEMA_VERSION = 2

DB_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS schema_info (
    version INTEGER PRIMARY KEY,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_path TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    path TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    fmt TEXT,
    quality INTEGER,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS resolutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    mode TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


@contextmanager
def get_conn(db_path: Path | sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Return a SQLite connection, initializing schema if required."""

    if isinstance(db_path, sqlite3.Connection):
        conn = db_path
        if not check_schema(conn):
            init_db(conn)
        yield conn
        return

    conn = sqlite3.connect(db_path)
    try:
        if not check_schema(conn):
            init_db(conn)
        yield conn
    finally:
        conn.close()


def check_schema(conn: sqlite3.Connection) -> bool:
    """Return True if database schema matches ``SCHEMA_VERSION``."""

    try:
        cur = conn.execute("SELECT version FROM schema_info")
        row = cur.fetchone()
        return bool(row) and row[0] == SCHEMA_VERSION
    except sqlite3.OperationalError:
        return False


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize or upgrade the database schema."""

    conn.executescript(DB_SCHEMA)
    conn.execute("DELETE FROM schema_info")
    conn.execute(
        "INSERT INTO schema_info (version, updated_at) VALUES (?, ?)",
        (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def reset_db(db_path: Path) -> None:
    """Delete and recreate the database at ``db_path``."""

    db_path.unlink(missing_ok=True)
    with get_conn(db_path):
        pass


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class JobStatus:
    PENDING = "pending"
    UPSCALED_RAW = "upscaled_raw"
    DONE = "done"
    FAILED = "failed"


class Job(BaseModel):
    id: int | None = None
    src_path: str
    hash: str
    status: str = Field(default=JobStatus.PENDING)
    error: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    attempts: int = 0
    metadata: dict[str, Any] | None = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    @classmethod
    def create_or_skip(cls, conn: sqlite3.Connection, data: Mapping[str, Any]) -> "Job | None":
        """Insert job if hash not present. Returns Job or None if skipped."""

        cur = conn.execute(
            "SELECT id, status FROM jobs WHERE hash=?", (data["hash"],),
        )
        row = cur.fetchone()
        if row:
            return None  # skip duplicate
        now = datetime.now(timezone.utc).isoformat()
        job_data = (
            data["src_path"],
            data["hash"],
            JobStatus.PENDING,
            0,
            None,
            now,
            now,
            json.dumps(data.get("metadata")) if data.get("metadata") is not None else None,
        )
        conn.execute(
            "INSERT INTO jobs (src_path, hash, status, attempts, error, created_at, updated_at, metadata) "
            "VALUES(?,?,?,?,?,?,?,?)",
            job_data,
        )
        job_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        return cls(id=job_id, **data)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Job":
        data = dict(row)
        if data.get("metadata"):
            data["metadata"] = json.loads(data["metadata"])
        return cls(**data)

    @classmethod
    def pending(cls, conn: sqlite3.Connection, limit: int = 100) -> list["Job"]:
        """Return jobs eligible for processing (pending or retryable failed)."""

        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT * FROM jobs WHERE (status=? OR (status=? AND attempts<3)) LIMIT ?",
            (JobStatus.PENDING, JobStatus.FAILED, limit),
        )
        return [cls.from_row(r) for r in cur.fetchall()]

    def set_status(self, conn: sqlite3.Connection, status: str, error: str | None = None):
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if error:
            self.error = error
        if status == JobStatus.FAILED:
            self.attempts += 1
        conn.execute(
            "UPDATE jobs SET status=?, attempts=?, error=?, updated_at=? WHERE id=?",
            (self.status, self.attempts, self.error, self.updated_at, self.id),
        )
        conn.commit()

