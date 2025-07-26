"""Back-end adapters."""

try:
    from .torch_backend import TorchRealESRGANBackend  # noqa: F401

    __all__ = ["TorchRealESRGANBackend"]
except Exception:  # pragma: no cover
    # Heavy deps missing – nothing exported
    pass
    __all__: list[str] = []
