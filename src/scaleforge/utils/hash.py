"""Hashing helpers.

The hash is based on the *content* of the source image **and** the relevant
processing parameters so that identical work is never executed twice.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

__all__ = ["hash_params"]


def _file_sha256(path: Path) -> str:
    """Return the SHA-256 of *path*'s contents."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_params(path: Path | str, params: Mapping[str, Any] | None = None) -> str:
    """Return a unique 64-char hash for *path* + *params*.

    Algorithm: SHA-256 over JSON blob {"sha256": <file>, "params": {...}}.
    """
    p = Path(path)
    file_hash = _file_sha256(p)
    blob = {"sha256": file_hash, "params": params or {}}
    data = json.dumps(blob, sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()
