

from __future__ import annotations
import click
from typing import Any

def print_status(message: str, **kwargs: Any) -> None:
    """Print status message with optional formatting."""
    click.echo(message)

