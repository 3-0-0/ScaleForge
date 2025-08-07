"""Vulkan (NCNN) back-end using realesrgan-ncnn-vulkan binary."""

import asyncio
import logging
from pathlib import Path

from scaleforge.backend.base import Backend, BackendError

logger = logging.getLogger(__name__)


class VulkanBackend(Backend):
    """NCNN-vulkan-based Real-ESRGAN back-end using external binary."""

    name = "vulkan"

    def is_available(self) -> bool:
        """Check if backend is available (binary exists and Vulkan works)."""
        try:
            import subprocess
            result = subprocess.run(["realesrgan-ncnn-vulkan", "-h"], 
                                  capture_output=True,
                                  check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def description(self) -> str:
        """Return backend description."""
        return "NCNN-Vulkan (external binary)"

    async def upscale(
        self,
        src: Path,
        dst: Path,
        scale: int = 2,
        **kwargs,
    ) -> None:
        """Upscale one image using realesrgan-ncnn-vulkan binary."""
        cmd = [
            "realesrgan-ncnn-vulkan",
            "-i", str(src),
            "-o", str(dst),
            "-s", str(scale),
            "-n", "realesrgan",
        ]
        logger.debug("Running Vulkan backend command: %s", cmd)
        dst.parent.mkdir(parents=True, exist_ok=True)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            output = stderr.decode("utf-8", errors="ignore") or stdout.decode("utf-8", errors="ignore")
            raise BackendError(f"Vulkan backend failed (code {process.returncode}): {output.strip()}")
