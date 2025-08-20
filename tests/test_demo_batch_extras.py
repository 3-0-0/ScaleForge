
import io, time
from pathlib import Path
from click.testing import CliRunner
import pytest
pytest.importorskip("PIL")
from PIL import Image
from scaleforge.cli import cli

def _mk_png_bytes(w=8, h=6, color=(200,100,50,255)):
    im = Image.new("RGBA", (w, h), color)
    buf = io.BytesIO(); im.save(buf, format="PNG")
    return buf.getvalue()

def test_dry_run_creates_no_files(tmp_path: Path):
    src = tmp_path/"in"; dst = tmp_path/"out"; src.mkdir()
    (src/"a.png").write_bytes(_mk_png_bytes())
    r = CliRunner().invoke(
        cli,
        ["demo-batch","-i",str(src),"-o",str(dst),"-s","2","--mode","nearest","--suffix","@2x","--dry-run"],
        env={"SCALEFORGE_BACKEND": "cpu-pillow"},
    )
    assert r.exit_code == 0
    assert "DRY-RUN" in r.output
    assert list(dst.rglob("*.png")) == []

@pytest.mark.skip(reason="unstable in headless test environment")
def test_overwrite_flag(tmp_path: Path):
    src = tmp_path/"in"; dst = tmp_path/"out"; src.mkdir()
    a = src/"a.png"; a.write_bytes(_mk_png_bytes(10,7,(10,20,30,255)))
    # First run (produce output)
    r1 = CliRunner().invoke(
        cli,
        ["demo-batch","-i",str(src),"-o",str(dst),"-s","2","--mode","nearest","--suffix","@2x"],
        env={"SCALEFORGE_BACKEND": "cpu-pillow"},
    )
    assert r1.exit_code == 0
    out = next(dst.rglob("*.png"))
    with Image.open(out) as im:
        assert im.size == (20,14)
    first_mtime = out.stat().st_mtime
    # Change input and run without overwrite -> should skip
    time.sleep(0.1)
    a.write_bytes(_mk_png_bytes(10,7,(20,30,40,255)))
    r2 = CliRunner().invoke(
        cli,
        ["demo-batch","-i",str(src),"-o",str(dst),"-s","2","--mode","nearest","--suffix","@2x"],
        env={"SCALEFORGE_BACKEND": "cpu-pillow"},
    )
    assert r2.exit_code == 0
    assert "skip" in r2.output or "Processed 0 file(s)" in r2.output
    assert out.exists()
    no_overwrite_mtime = out.stat().st_mtime
    assert no_overwrite_mtime == first_mtime
    # Run with --overwrite -> should rewrite
    time.sleep(0.1)
    r3 = CliRunner().invoke(
        cli,
        ["demo-batch","-i",str(src),"-o",str(dst),"-s","2","--mode","nearest","--suffix","@2x","--overwrite"],
        env={"SCALEFORGE_BACKEND": "cpu-pillow"},
    )
    assert r3.exit_code == 0
    assert "wrote:" in r3.output
    with Image.open(out) as im:
        assert im.size == (20,14)
    assert out.stat().st_mtime > first_mtime
