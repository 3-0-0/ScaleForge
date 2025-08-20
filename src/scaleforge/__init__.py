"""ScaleForge package root."""

try:
    from importlib.metadata import version, PackageNotFoundError  # py3.8+
except Exception:  # pragma: no cover
    version = None
    PackageNotFoundError = Exception

try:
    __version__ = version("scaleforge") if version else "0"
except PackageNotFoundError:
    # fallback for editable installs/tests
    from ._version import __version__ as __version__
