"""Namespace package wrapper for tests.

The project sources live under ``src/scaleforge`` to follow the
``src/``-layout.  The unit tests import modules simply as ``scaleforge``
without installing the package, therefore the path containing the real
modules needs to be added to ``__path__`` when this lightweight wrapper is
imported.
"""

from __future__ import annotations

from pathlib import Path
import sys

# ``__path__`` is defined by Python for packages.  We append the path to the
# actual implementation package living under ``../src/scaleforge`` so that
# submodules resolve correctly when the project hasn't been installed.  At the
# same time the parent ``src`` directory is added to ``sys.path`` which exposes
# sibling stub packages such as ``PIL`` used in the tests.
_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _ROOT / "src"
_SRC = _SRC_ROOT / "scaleforge"
if _SRC.exists():  # pragma: no branch - always true in tests
    if str(_SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(_SRC_ROOT))
    __path__.append(str(_SRC))  # type: ignore[name-defined]

try:  # pragma: no cover - best effort
    from ._version import __version__ as __version__
except Exception:
    __version__ = "0"

