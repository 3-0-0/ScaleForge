from __future__ import annotations

from dataclasses import dataclass, field


def canonical_alias(vendor: str, engine: str, device: str | None = None) -> str:
    parts = [vendor, engine]
    if device:
        parts.append(device)
    return "-".join(parts)


@dataclass(frozen=True)
class BackendSpec:
    vendor: str
    engine: str
    device: str | None = None
    alias: str = field(init=False)

    def __post_init__(self) -> None:  # pragma: no cover - simple assignment
        object.__setattr__(self, "alias", canonical_alias(self.vendor, self.engine, self.device))


def parse_alias(alias: str) -> BackendSpec:
    parts = alias.split("-")
    if len(parts) < 2:
        raise ValueError(f"Invalid backend alias: {alias}")
    vendor, engine = parts[0], parts[1]
    device = "-".join(parts[2:]) if len(parts) > 2 else None
    return BackendSpec(vendor, engine, device)
