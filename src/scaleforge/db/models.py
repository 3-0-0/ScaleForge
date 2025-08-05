"""SQLite models and helper functions."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Any, Mapping

from pydantic import BaseModel, Field

DB_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_path TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    extra TEXT
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


class JobStatus:
    PENDING = "pending"
    UPSCALED_RAW = "upscaled_raw"
    DONE = "done"
    FAILED = "failed"


@contextmanager
def get_conn(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


SCHEMA_VERSION = 1

def check_schema(conn: sqlite3.Connection) -> bool:
    """Check if schema matches current version."""
    try:
        conn.execute("SELECT attempts FROM jobs LIMIT 1")
        return True
    except sqlite3.OperationalError:
        return False

def reset_db(db_path: Path):
    """Delete and recreate database."""
    db_path.unlink(missing_ok=True)
    init_db(db_path)

def init_db(db_path: Path, force: bool = False):
    """Initialize or upgrade database schema."""
    db_exists = db_path.exists()
    
    with get_conn(db_path) as conn:
        if db_exists and not force:
            if check_schema(conn):
                return  # Schema is current
            print("Warning: Database schema outdated. Attempting upgrade...")
            
        # Create or recreate schema
        conn.executescript(DB_SCHEMA)
        
        # Add version tracking
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()


class Job(BaseModel):
    id: int | None = None
    src_path: str
    hash: str
    status: str = Field(default=JobStatus.PENDING)
    error: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    attempts: int = 0
    extra: str | None = None

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
            None,
        )
        conn.execute(
            "INSERT INTO jobs (src_path, hash, status, attempts, error, created_at, updated_at, extra) "
            "VALUES(?,?,?,?,?,?,?,?)",
            job_data,
        )
        job_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        return cls(id=job_id, **data)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Job":
        return cls(**dict(row))

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


