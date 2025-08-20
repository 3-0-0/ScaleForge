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
import urllib.request
from pathlib import Path
from typing import Dict, Any

from scaleforge.config.loader import load_config
from scaleforge.models.registry import load_effective_registry


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

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------
    def get_registry(self) -> Dict[str, Dict[str, Any]]:
        """Return the model registry mapping names to raw entry dictionaries."""

        if self._registry is None:
            data = load_effective_registry()
            resolved: Dict[str, _ResolvedModel] = {}
            for raw in data.get("models", []):
                # Entries are assumed to have already been validated elsewhere;
                # we simply skip obviously malformed ones.
                name = raw.get("name")
                url = raw.get("url")
                urls = raw.get("urls")
                if not name or (not url and not urls):
                    continue
                first_url = url or urls[0]
                filename = raw.get("filename") or Path(first_url).name
                resolved[name] = _ResolvedModel(info=raw, path=self.model_dir / filename)
            self._registry = resolved

        # ``self._registry`` maps to ``_ResolvedModel`` but the public contract is
        # a mapping to ``ModelSchema``.  Expose only the ``info`` attribute to the
        # outside world.
        return {name: rm.info for name, rm in self._registry.items()}

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------
    def _entry(self, name: str) -> _ResolvedModel:
        """Return the resolved registry entry for ``name``."""

        if self._registry is None:
            # Populate the cache
            self.get_registry()
        assert self._registry is not None  # for type-checkers
        return self._registry[name]

    def is_model_downloaded(self, name: str) -> bool:
        """Return ``True`` if the model file exists and matches the checksum."""

        entry = self._entry(name)
        if not entry.path.exists():
            return False
        return self._sha256(entry.path) == entry.info.sha256

    def download_model(self, name: str) -> Path:
        """Download ``name`` to the configured model directory.

        The downloaded file is verified against the SHA256 checksum declared in
        the registry.  A :class:`RuntimeError` is raised if the checksum does not
        match.
        """

        entry = self._entry(name)
        url = entry.info.resolved_urls()[0]
        self._download(url, entry.path)
        if self._sha256(entry.path) != entry.info.sha256:
            entry.path.unlink(missing_ok=True)
            raise RuntimeError("Model checksum verification failed")
        return entry.path

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

    @staticmethod
    def _download(url: str, dest: Path) -> None:  # pragma: no cover - network
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp")
        with urllib.request.urlopen(url) as resp, open(tmp, "wb") as fh:
            fh.write(resp.read())
        tmp.replace(dest)

