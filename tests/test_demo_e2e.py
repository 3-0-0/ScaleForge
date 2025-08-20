from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scaleforge.demo import upscale as demo_upscale
from scaleforge.backend.selector import get_backend_alias


def test_demo_e2e(tmp_path: Path) -> None:
    src = tmp_path / "src.png"
    demo_upscale.Image.new("RGB", (16, 16), "blue").save(src)
    dst = tmp_path / "dst.png"

    cmd = [
        sys.executable,
        "-m",
        "scaleforge.cli",
        "demo",
        "upscale",
        "--in",
        str(src),
        "--scale",
        "2",
        "--out",
        str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert dst.exists()
    out = demo_upscale.Image.open(dst)
    assert (out.width, out.height) == (32, 32)
    alias, _ = get_backend_alias()
    assert alias in result.stdout
