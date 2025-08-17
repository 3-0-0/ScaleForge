
from PIL import Image
from pathlib import Path
from typing import Optional, Tuple, List
import glob
import os

def upscale_image(
    input_path: str,
    output_path: str,
    scale: float = 2.0,
    mode: str = "lanczos",
    debug: bool = False
) -> None:
    """Upscale a single image using Pillow."""
    mode_map = {
        "nearest": Image.NEAREST,
        "bilinear": Image.BILINEAR,
        "bicubic": Image.BICUBIC,
        "lanczos": Image.LANCZOS
    }
    
    try:
        with Image.open(input_path) as img:
            width, height = img.size
            new_size = (int(width * scale), int(height * scale))
            resized = img.resize(new_size, mode_map[mode.lower()])
            resized.save(output_path)
    except Exception as e:
        if debug:
            print(f"Error processing {input_path}: {str(e)}")
        raise

def batch_upscale(
    input_dir: str,
    output_dir: str,
    scale: float = 2.0,
    mode: str = "lanczos",
    suffix: str = "@scaled",
    include_patterns: Tuple[str, ...] = (),
    exclude_patterns: Tuple[str, ...] = (),
    limit: Optional[int] = None,
    dry_run: bool = False,
    overwrite: bool = False,
    debug: bool = False
) -> None:
    """Batch process images with upscaling."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Collect files to process
    files: List[Path] = []
    for pattern in include_patterns or ["*"]:
        files.extend(Path(p) for p in glob.glob(str(input_path / pattern), recursive=True))
    
    # Apply excludes
    if exclude_patterns:
        excluded = set()
        for pattern in exclude_patterns:
            excluded.update(Path(p) for p in glob.glob(str(input_path / pattern), recursive=True))
        files = [f for f in files if f not in excluded]
    
    # Apply limit
    if limit is not None:
        files = files[:limit]
    
    if dry_run:
        print(f"DRY-RUN: Would process {len(files)} files:")
        for f in files:
            print(f"  {f} -> {output_path / (f.stem + suffix + f.suffix)}")
        return
    
    # Process files
    processed = 0
    for input_file in files:
        output_file = output_path / (input_file.stem + suffix + input_file.suffix)
        if output_file.exists() and not overwrite:
            print(f"Skipping {input_file} - output already exists (use --overwrite to force)")
            continue
            
        try:
            if debug or overwrite:
                print(f"Processing {input_file} -> {output_file}")
            upscale_image(str(input_file), str(output_file), scale, mode, debug)
            if overwrite and output_file.exists():
                print(f"Overwrote: {output_file}")
            processed += 1
        except Exception as e:
            print(f"Failed to process {input_file}: {e}")
            if debug:
                raise
    
    print(f"Processed {processed} file(s)")

# Alias for backward compatibility
demo_upscale = upscale_image
