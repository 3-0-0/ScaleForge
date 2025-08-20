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
    def __init__(self, data: bytes | None = None) -> None:
        self._data = data or b""

    # The Pillow API accepts either a filesystem path or a file object.  The
    # tests only use paths so that's all we support here.
    def save(self, fp: str | Path | Any, format: str | None = None, **_: Any) -> None:
        """Save the image to *fp*.

        ``fp`` may be a filesystem path or a file-like object supporting
        ``write``.  The data written is the opaque byte payload stored on the
        instance; no real image encoding takes place.
        """

        if hasattr(fp, "write"):
            fp.write(self._data)
        else:
            Path(fp).write_bytes(self._data)

    def convert(self, mode: str) -> "_Image":  # pragma: no cover - trivial
        return self


def new(mode: str, size: tuple[int, int], color: str | tuple[int, int, int]):
    """Return a new blank image.  Mode/size/colour are ignored."""

    return _Image(b"")


def open(path: str | Path, mode: str = "r") -> _Image:  # noqa: D401
    """Open *path* and return an ``_Image`` containing its bytes."""

    data = Path(path).read_bytes()
    return _Image(data)


# Provide ``Image`` namespace similar to Pillow
class ImageModule:
    Image = _Image
    new = staticmethod(new)
    open = staticmethod(open)


Image = ImageModule()

__all__ = ["Image", "new", "open"]

