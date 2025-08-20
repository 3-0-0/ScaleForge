from __future__ import annotations

import click

from .main import _CFG, cli, load_config


@cli.command("info")
def info() -> None:
    """Show system and configuration information."""
    import platform
    from importlib import metadata as im
    from pathlib import Path

    from scaleforge.backend.detector import detect_gpu_caps
    from scaleforge.backend.selector import get_backend_alias
    import scaleforge as sf

    cfg = _CFG
    if cfg is None:
        loader = load_config
        if loader is None:  # pragma: no cover - should be set by ``cli``
            from scaleforge.config.loader import load_config as _load_config

            loader = _load_config
        cfg = loader()

    alias, _ = get_backend_alias()
    caps = detect_gpu_caps()

    def _pkg_version(name: str) -> str:
        try:
            return im.version(name)
        except im.PackageNotFoundError:
            return "not installed"

    pkgs = {
        "torch": _pkg_version("torch"),
        "onnxruntime": _pkg_version("onnxruntime"),
        "pillow": _pkg_version("Pillow"),
    }

    sf_path = Path(sf.__file__).resolve().parent

    click.echo("Platform:")
    click.echo(f"  OS: {platform.platform()}")
    click.echo(f"  Python: {platform.python_version()}")
    click.echo(f"  Scaleforge: {sf.__version__} ({sf_path})")
    click.echo()

    click.echo("Packages:")
    for name, ver in pkgs.items():
        click.echo(f"  {name}: {ver}")
    click.echo()

    click.echo("GPU caps:")
    click.echo(f"  vendor: {caps['vendor']}")
    click.echo(f"  cuda: {caps['cuda']}")
    click.echo(f"  rocm: {caps['rocm']}")
    click.echo(f"  mps: {caps['mps']}")
    click.echo()

    available = {"cpu-pillow"}
    if pkgs["torch"] != "not installed":
        if caps["cuda"]:
            available.add("torch-eager-cuda")
        if caps["rocm"]:
            available.add("torch-eager-rocm")
        if caps["mps"]:
            available.add("torch-eager-mps")
        available.add("torch-eager-cpu")
    try:
        from scaleforge.backend.vulkan_backend import VulkanBackend

        if VulkanBackend().is_available():
            available.add("ncnn-ncnn-vulkan")
    except Exception:  # pragma: no cover - optional path
        pass

    click.echo("Backends:")
    click.echo(f"  chosen: {alias}")
    click.echo(f"  available: {', '.join(sorted(available))}")
    click.echo()

    if cfg is not None:
        click.echo("Cache:")
        click.echo(f"  database: {cfg.database_path}")
        click.echo(f"  logs: {cfg.log_dir}")
        click.echo(f"  models: {cfg.model_dir}")
    else:  # pragma: no cover - cfg should exist
        click.echo("Cache: <unconfigured>")
