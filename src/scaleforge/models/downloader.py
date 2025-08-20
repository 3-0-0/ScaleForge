"""Utility for downloading model files from the registry.

This module provides a small :class:`ModelDownloader` class that is used by
 the CLI to fetch model files listed in the ScaleForge registry.  The
 implementation is intentionally lightweight – it only implements the pieces the
 CLI currently relies on: reading the registry, checking if a model has already
 been downloaded and downloading a model while verifying the checksum.

The registry entries are defined in :mod:`scaleforge.models.registry` and are
represented as simple dictionaries.  Heavy validation is avoided to keep the
 test environment light-weight.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional

from scaleforge.config.loader import load_config
from scaleforge.models.registry import load_effective_registry
from scaleforge.errors import ModelChecksumMismatch, ModelDownloadError


def _candidate_urls(info: Dict[str, Any]) -> List[str]:
    """Return a list of candidate URLs from a registry entry."""

    urls = info.get("urls")
    if isinstance(urls, list) and urls:
        return [str(u) for u in urls]
    url = info.get("url")
    return [str(url)] if isinstance(url, str) else []


@dataclass
class _ResolvedModel:
    """Internal helper describing a resolved model entry."""

    info: Dict[str, Any]
    path: Path


class ModelDownloader:
    """Download and cache model files declared in the registry."""

    def __init__(self, model_dir: Path | None = None) -> None:
        cfg = load_config()
        self.model_dir = Path(model_dir or cfg.model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._registry: Dict[str, _ResolvedModel] | None = None
        self.last_url: Optional[str] = None

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------
    def get_registry(self) -> Dict[str, Dict[str, Any]]:
        """Return the model registry mapping names to raw entry dictionaries."""

        if self._registry is None:
            data = load_effective_registry()
            resolved: Dict[str, _ResolvedModel] = {}
            models = data.get("models", {})
            if isinstance(models, dict):
                for name, entry in models.items():
                    info = entry.get("info", {})
                    urls = _candidate_urls(info)
                    if not urls:
                        continue
                    first_url = urls[0]
                    filename = entry.get("filename") or Path(first_url).name
                    resolved[name] = _ResolvedModel(info=info, path=self.model_dir / filename)
            self._registry = resolved

        return {name: rm.info for name, rm in self._registry.items()}

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------
    def _entry(self, name: str) -> _ResolvedModel:
        if self._registry is None:
            self.get_registry()
        assert self._registry is not None
        return self._registry[name]

    def is_model_downloaded(self, name: str) -> bool:
        entry = self._entry(name)
        if not entry.path.exists():
            return False
        return self._sha256(entry.path) == entry.info["sha256"]

    def download_model(self, name: str, progress: Callable[[str], None] | None = None) -> Path:
        """Download ``name`` to the configured model directory."""

        entry = self._entry(name)
        sha = entry.info["sha256"]
        if entry.path.exists() and self._sha256(entry.path) == sha:
            self.last_url = None
            if progress:
                progress("done")
            return entry.path

        urls = _candidate_urls(entry.info)
        last_exc: Exception | None = None
        for url in urls:
            if progress:
                progress("start")
            try:
                self._download_with_retries(url, entry.path, sha)
            except ModelChecksumMismatch as e:
                last_exc = e
                continue
            except ModelDownloadError as e:
                last_exc = e
                continue
            self.last_url = url
            if progress:
                progress("verify")
                progress("done")
            return entry.path
        if isinstance(last_exc, ModelChecksumMismatch):
            raise last_exc
        raise ModelDownloadError(f"all URLs failed for {name}")

    # ------------------------------------------------------------------
    # Static utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _sha256(path: Path) -> str:
        hash_obj = hashlib.sha256()
        with open(path, "rb") as fh:  # pragma: no cover - small helper
            for chunk in iter(lambda: fh.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def _download_with_retries(self, url: str, dest: Path, sha256: str) -> None:
        delays = [0.2, 0.5, 1.0]
        last_error: Optional[Exception] = None
        for idx, delay in enumerate(delays, 1):
            try:
                self._download_once(url, dest, sha256)
                return
            except ModelChecksumMismatch:
                raise
            except ModelDownloadError as e:
                last_error = e
                if idx < len(delays):
                    time.sleep(delay)
        if last_error:
            raise last_error

    def _download_once(self, url: str, dest: Path, sha256: str) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp")
        hash_obj = hashlib.sha256()
        start = 0
        mode = "wb"
        if tmp.exists():
            start = tmp.stat().st_size
            with open(tmp, "rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    hash_obj.update(chunk)
            mode = "ab"
        headers = {}
        if start:
            headers["Range"] = f"bytes={start}-"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp, open(tmp, mode) as fh:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    fh.write(chunk)
                    hash_obj.update(chunk)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            raise ModelDownloadError(str(e)) from e
        digest = hash_obj.hexdigest()
        if digest != sha256:
            tmp.unlink(missing_ok=True)
            raise ModelChecksumMismatch("checksum mismatch")
        tmp.replace(dest)


__all__ = ["ModelDownloader"]

