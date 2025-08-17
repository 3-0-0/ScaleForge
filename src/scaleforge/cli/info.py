

from __future__ import annotations
import click
from typing import Optional

@click.command("info")
def info():
    """Show system and configuration information."""
    click.echo("System information placeholder")

