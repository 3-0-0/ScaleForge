from pathlib import Path
from PIL import Image

from scaleforge.pipeline.entry import run_pipeline


def test_run_pipeline_basic(tmp_path):
    src = tmp_path / "src.png"
    Image.new("RGB", (2, 2), "red").save(src)
    out_dir = tmp_path / "out"
    ok = run_pipeline(str(src), str(out_dir), scale=2, resume=False, verbose=False)
    assert ok is True
    assert (out_dir / "src.png.x2.png").exists()
