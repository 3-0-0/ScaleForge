
# ScaleForge 🚀

![ScaleForge Demo](docs/demo.gif) *Example: Upscaling 512px → 2048px*

Portable, cross-platform image upscaler powered by Real-ESRGAN with GPU acceleration.

## ✨ Key Features

- 🖼️ **AI-Powered Upscaling** (Real-ESRGAN models)
- ⚡ **GPU Acceleration** (NCNN/PyTorch backends)
- 🖥️ **Cross-Platform GUI** (Kivy-based)
- 📦 **Portable** (Single executable available)
- 🔄 **Batch Processing** (Process entire folders)
- 📊 **Progress Tracking** (Job queue with pause/resume)

## 🛠️ Installation

### Option 1: Pip Install
```bash
pip install scaleforge
```

### Option 2: Download Pre-built
Get the latest release from our [GitHub Releases](https://github.com/3-0-0/ScaleForge/releases) page.

## 🚀 Quick Start

1. **Launch ScaleForge**:
   ```bash
   scaleforge gui  # For graphical interface
   ```
   or
   ```bash
   scaleforge cli --scale 4 input.jpg  # For command line
   ```

2. **Select images** and desired upscale factor
3. **Choose model** (quality vs speed tradeoff)
4. **Run** and wait for results!

## 📚 Learn More

- [First Steps Guide](docs/first_steps.md) - New user walkthrough
- [Advanced Usage](docs/advanced.md) - CLI options and configs
- [Feedback Guide](docs/feedback.md) - How to report issues

## 🤝 Contributing

We welcome feedback and contributions! Please:
- Report bugs via [GitHub Issues](https://github.com/3-0-0/ScaleForge/issues)
- Share suggestions in our [Discussions](https://github.com/3-0-0/ScaleForge/discussions)

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

*ScaleForge v0.1.0-beta - Making high-quality upscaling accessible to everyone.*
