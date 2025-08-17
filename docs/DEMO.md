# ScaleForge Demo (Pillow-only)

## Quickstart

1. Set up environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
# .venv\Scripts\activate  # Windows
pip install -U pip
pip install -e ".[demo]" pytest
```

2. Single image upscaling:
```bash
python -m scaleforge.cli demo-upscale -i input.png -o output@2x.png -s 2 --mode lanczos
```

3. Batch processing:
```bash
python -m scaleforge.cli demo-batch \
  -i ./input_images \
  -o ./output \
  --suffix @2x \
  --include "*.png" "*.jpg" \
  --exclude "*thumb*" \
  --limit 100 \
  --overwrite
```

## Options

### demo-upscale
- `-i/--input`: Input image path (required)
- `-o/--output`: Output image path (required) 
- `-s/--scale`: Upscale factor (default: 2.0)
- `--mode`: Upsampling mode (nearest|bilinear|bicubic|lanczos, default: lanczos)

### demo-batch
- `-i/--input-dir`: Input directory (required)
- `-o/--output-dir`: Output directory (required)
- `--suffix`: Filename suffix for outputs (default: @scaled)
- `--include`: File patterns to include (multiple allowed)
- `--exclude`: File patterns to exclude (multiple allowed) 
- `--limit`: Maximum number of files to process
- `--overwrite`: Overwrite existing files
- `--dry-run`: Preview without processing

