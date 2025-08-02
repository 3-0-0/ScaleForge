
# ScaleForge

Portable, cross-platform image upscaler powered by Real-ESRGAN.

## Features

- Automatic GPU detection and optimization
- Batch processing
- Multiple output formats
- Progress tracking

### GPU detection & caps cache

ScaleForge probes the GPU vendor and capability limits on startup and caches the results in `gpu_caps.json`. When detection fails (e.g., headless CI or no GPU), it falls back to safe defaults. Before doing work, ScaleForge computes the effective pixel cost (width × height × scale²) and skips jobs exceeding `max_pixels`, marking them with status `skipped_oversize` to avoid overloading the backend.

## Installation

```bash
pip install scaleforge
```

## Usage

```bash
scaleforge cli --scale 4 input.jpg
```

See `scaleforge cli --help` for all options.
