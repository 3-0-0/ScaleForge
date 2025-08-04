

# First Steps with ScaleForge

Welcome to ScaleForge! This guide will help you get started with your first image upscaling.

## 🏁 Getting Started

1. **Installation**:
   - Download the latest release from our [GitHub Releases](https://github.com/3-0-0/ScaleForge/releases)
   - Or install via pip: `pip install scaleforge`

2. **Launching**:
   ```bash
   # For GUI mode:
   scaleforge gui

   # For CLI mode:
   scaleforge cli --scale 4 input.jpg
   ```

## 🖼️ Your First Upscale (GUI)

1. Click "Add Images" or drag & drop files
2. Select output directory
3. Choose upscale factor (2x, 4x, etc.)
4. Select model (balance quality vs speed)
5. Click "Start Processing"

## 💻 Command Line Usage

Basic syntax:
```bash
scaleforge cli --scale FACTOR INPUT [OUTPUT]
```

Examples:
```bash
# Single file
scaleforge cli --scale 4 photo.jpg

# Batch processing
scaleforge cli --scale 2 ./input_folder/ ./output/
```

## ⚠️ Common Pitfalls

- **Large images**: May exceed GPU memory - try smaller tiles
- **Output formats**: Some formats (like PNG) preserve quality better
- **GPU detection**: If having issues, try `--backend cpu` flag

## 🆘 Need Help?

- Check `--help` for all options
- Visit our [GitHub Discussions](https://github.com/3-0-0/ScaleForge/discussions)
- Report issues via [GitHub Issues](https://github.com/3-0-0/ScaleForge/issues)

