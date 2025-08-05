
"""Tests for video frame extraction."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from scaleforge.video.frames import FrameExtractorStage, FrameInfo
from scaleforge.video.pipeline import VideoStreamConfig

@pytest.fixture
def sample_config():
    return VideoStreamConfig(
        source=Path(__file__).parent.parent / 'assets' / 'sample.mp4',
        fps=24
    )

def test_frame_extraction(sample_config, tmp_path):
    """Verify frame extraction produces expected number of frames."""
    ctx = MagicMock()
    ctx.tmp_dir = tmp_path
    
    extractor = FrameExtractorStage(sample_config)
    frames = extractor.run(MagicMock(), ctx)
    
    # Should produce 48 frames for 2 second video at 24fps
    assert len(frames) == 48
    assert all(isinstance(f, FrameInfo) for f in frames)
    
    # Verify timestamps increase by ~41ms (1000/24)
    for i in range(1, len(frames)):
        assert 40 <= (frames[i].ts_ms - frames[i-1].ts_ms) <= 42
    
    # Verify files exist
    assert all(f.filepath.exists() for f in frames)

def test_frame_info_dataclass():
    """Verify FrameInfo dataclass works as expected."""
    frame = FrameInfo(
        frame_idx=0,
        ts_ms=0,
        filepath=Path('/tmp/frame_00000000.png')
    )
    assert frame.status == 'pending'
