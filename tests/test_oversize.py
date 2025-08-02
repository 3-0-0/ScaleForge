

"""Tests for oversize image skipping logic."""
import os
import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

from scaleforge.cli.main import cli
from scaleforge.config.loader import load_config
from scaleforge.db.models import Job, JobStatus, init_db

@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Fixture providing isolated test environment."""
    # Setup test database
    db_path = tmp_path / "test.db"
    init_db(db_path)
    
    # Create test image
    img_path = tmp_path / "test.png"
    Image.new("RGB", (100, 100), "white").save(img_path)
    
    # Patch config to use test paths
    cfg = load_config()
    monkeypatch.setattr(cfg, "database_path", db_path)
    monkeypatch.setattr(cfg, "model_dir", tmp_path / "models")
    
    # Force oversize condition
    monkeypatch.setattr(
        "scaleforge.gpu.caps.load_caps",
        lambda: {"vendor": "test", "tile_size": 16, "max_pixels": 1}
    )
    
    # Stub backend
    monkeypatch.setenv("SF_STUB_UPSCALE", "1")
    
    return {"db_path": db_path, "img_path": img_path}

def test_oversize_skip(test_env):
    """Test CLI properly skips oversize images."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "cli",
            "--no-progress",
            "--scale", "4",
            str(test_env["img_path"])
        ],
        catch_exceptions=False
    )
    
    # Verify CLI output contains exact skip message
    assert "Skipped 1 oversize files" in result.output
    
    # Verify DB state
    with sqlite3.connect(test_env["db_path"]) as conn:
        job = Job.get_by_src_path(conn, str(test_env["img_path"]))
        assert job is not None
        assert job.status == JobStatus.SKIPPED_OVERSIZE
        assert "max_pixels" in job.extra  # Verify reason is recorded

