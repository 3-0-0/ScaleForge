from click.testing import CliRunner
from scaleforge.cli import cli
from scaleforge.backend.selector import get_backend_alias
from PIL import Image
from scaleforge.config.loader import AppConfig

def test_cli_help_command():
    r = CliRunner().invoke(cli, ["--help"])
    assert r.exit_code == 0

def test_cli_detect_backend_debug(monkeypatch):
    monkeypatch.setenv("SCALEFORGE_BACKEND", "cpu-pillow")
    r = CliRunner().invoke(cli, ["detect-backend", "--debug"])
    assert r.exit_code == 0
    assert "cpu-pillow" in r.output


def test_cli_help_info_command(monkeypatch):
    monkeypatch.setenv("SCALEFORGE_BACKEND", "cpu-pillow")
    backend, _ = get_backend_alias()
    r = CliRunner().invoke(cli, ["info"])
    assert r.exit_code == 0
    assert backend in r.output

def test_cli_run_stub(tmp_path, monkeypatch):
    img = tmp_path / "sample.png"
    Image.new("RGB", (4, 4), "white").save(img)
    out_dir = tmp_path / "out"

    def fake_cfg():
        return AppConfig(
            database_path=tmp_path / "db.sqlite",
            log_dir=tmp_path / "logs",
            model_dir=tmp_path / "models",
        )

    monkeypatch.setattr("scaleforge.cli.main.load_config", fake_cfg)
    r = CliRunner().invoke(cli, ["run", str(img), "-o", str(out_dir)])
    assert r.exit_code == 0
    assert (out_dir / "sample.png.x2.png").exists()
