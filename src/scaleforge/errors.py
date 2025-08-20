"""Project-wide exception classes."""
from __future__ import annotations


class ModelDownloadError(Exception):
    """Raised when downloading a model fails for all candidate URLs."""


class ModelChecksumMismatch(ModelDownloadError):
    """Raised when a downloaded file does not match the expected checksum."""


__all__ = ["ModelDownloadError", "ModelChecksumMismatch"]

