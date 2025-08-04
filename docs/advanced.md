

# Advanced ScaleForge Usage

## 🔧 Configuration Options

### Backend Selection
```bash
--backend ncnn    # Fastest (Vulkan required)
--backend pytorch # More compatible
--backend cpu     # Fallback option
```

### Performance Tuning
```bash
--tile-size 256   # Adjust GPU memory usage
--threads 4       # CPU thread count
--fp16            # Use half-precision (faster)
```

## 🛠️ CLI Reference

### Core Arguments
```
--scale FACTOR    Upscale factor (2, 4, etc.)
--model NAME      Specific model to use
--output DIR      Custom output directory
--quiet           Suppress console output
```

### Job Control
```
--resume          Continue interrupted job
--skip-existing   Don't reprocess existing outputs
--force           Overwrite existing files
```

## ⚙️ Configuration File

Create `~/.scaleforge/config.json`:
```json
{
  "default_model": "realesrgan-x4",
  "output_dir": "~/upscaled",
  "gpu_preference": "discrete"
}
```

## 🐛 Debugging Tips

View debug logs:
```bash
scaleforge --log-level debug [...]
```

Check GPU capabilities:
```bash
scaleforge info --gpu
```

Reset cached settings:
```bash
scaleforge reset --cache
```

