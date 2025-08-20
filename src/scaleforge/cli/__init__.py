from .main import cli
from . import info as _info  # noqa: F401 ensure subcommands are registered

__all__ = ["cli"]
