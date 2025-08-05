
"""Video frame extraction pipeline stage."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import ffmpeg
from dataclasses import dataclass

from scaleforge.db.models import Job
from scaleforge.video.pipeline import VideoStreamConfig

logger = logging.getLogger(__name__)

@dataclass
class FrameInfo:
    frame_idx: int
    ts_ms: int
    filepath: Path
    status: str = 'pending'

class FrameExtractorStage:
    """Extracts frames from video using ffmpeg."""
    
    def __init__(self, config: VideoStreamConfig):
        self.config = config
        self.fps = None
        self.frame_count = 0

    def run(self, job: Job, ctx) -> list[FrameInfo]:
        """Extract frames to temp directory and return frame metadata."""
        output_dir = ctx.tmp_dir / 'frames'
        output_dir.mkdir(exist_ok=True)
        
        # Extract frames with ffmpeg
        output_pattern = str(output_dir / 'frame_%08d.png')
        try:
            logger.info(f"Extracting frames from {self.config.source} to {output_pattern}")
            (
                ffmpeg.input(str(self.config.source))
                .output(output_pattern, 
                       r=self.config.fps or 24,
                       vcodec='png',
                       pix_fmt='rgb24')
                .run(quiet=False)  # Set to False to see ffmpeg output
            )
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf8') if e.stderr else str(e)
            logger.error(f"FFmpeg error: {error_msg}")
            raise
        except Exception as e:
            logger.error(f"Frame extraction failed: {str(e)}")
            raise
        
        # Get frame metadata
        frames = []
        for i, frame_path in enumerate(sorted(output_dir.glob('frame_*.png'))):
            frames.append(FrameInfo(
                frame_idx=i,
                ts_ms=int(i * (1000 / (self.config.fps or 24))),
                filepath=frame_path
            ))
        
        return frames
