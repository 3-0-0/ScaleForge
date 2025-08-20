from .main import cli
from . import info as _info  # noqa: F401 ensure subcommands are registered
from . import demo as _demo  # noqa: F401 ensure demo commands are registered

__all__ = ["cli"]
