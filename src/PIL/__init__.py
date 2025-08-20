"""Very small stub of the :mod:`PIL` module used in tests.

The real project depends on Pillow to read and write images.  Shipping the
entire dependency would make the exercises considerably heavier, therefore a
tiny in-house stub is provided.  It implements just enough features for the
unit tests:

* ``Image.new`` creates an in-memory image object.
* ``Image.open`` loads the raw bytes of a file.
* ``Image.save`` writes those bytes back to disk.
* ``convert`` is a no-op returning ``self``.

The stub stores opaque byte strings instead of real image data – the tests only
verify file existence, not image contents.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class _Image:
    def __init__(self, data: bytes | None = None, size: tuple[int, int] | None = None) -> None:
        self._data = data or b""
        self.width, self.height = size or (0, 0)

    # The Pillow API accepts either a filesystem path or a file object.  The
    # tests only use paths so that's all we support here.
    def save(self, fp: str | Path | Any, format: str | None = None, **_: Any) -> None:
        """Save the image to *fp*.

        ``fp`` may be a filesystem path or a file-like object supporting
        ``write``.  The data written encodes the image dimensions as
        ``"{width}x{height}"``; no real image encoding takes place.
        """

        data = f"{self.width}x{self.height}".encode()
        if hasattr(fp, "write"):
            fp.write(data)
        else:
            Path(fp).write_bytes(data)

    def convert(self, mode: str) -> "_Image":  # pragma: no cover - trivial
        return self

    def resize(self, size: tuple[int, int], resample: Any | None = None) -> "_Image":  # noqa: D401
        """Return a new image with ``size``."""

        return _Image(self._data, size)


def new(mode: str, size: tuple[int, int], color: str | tuple[int, int, int]):
    """Return a new blank image.  Mode/size/colour are ignored."""

    return _Image(b"", size)


def open(path: str | Path, mode: str = "r") -> _Image:  # noqa: D401
    """Open *path* and return an ``_Image`` containing its bytes."""

    data = Path(path).read_bytes()
    try:
        dims = data.decode().split("x", 1)
        size = (int(dims[0]), int(dims[1]))
    except Exception:  # pragma: no cover - bad data
        size = (0, 0)
    return _Image(data, size)


# Provide ``Image`` namespace similar to Pillow
class ImageModule:
    Image = _Image
    new = staticmethod(new)
    open = staticmethod(open)
    NEAREST = 0
    BILINEAR = 1
    BICUBIC = 2
    LANCZOS = 3


Image = ImageModule()

__all__ = ["Image", "new", "open"]

