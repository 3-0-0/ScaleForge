
# ScaleForge 🚀

[![PyPI Version](https://img.shields.io/pypi/v/scaleforge)](https://pypi.org/project/scaleforge/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![GitHub Stars](https://img.shields.io/github/stars/3-0-0/ScaleForge)](https://github.com/3-0-0/ScaleForge/stargazers)

![ScaleForge Demo](docs/demo.gif) *Example: Upscaling 512px → 2048px*

Portable, cross-platform image upscaler powered by Real-ESRGAN with GPU acceleration. Transform low-resolution images into high-quality enlargements with AI-powered upscaling.

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

## 🗺️ Roadmap

Upcoming features:
- 🎨 Additional AI models
- 🌐 Web interface option
- 📱 Mobile app version
- 🔍 Comparison tools

View full roadmap: [ROADMAP.md](ROADMAP.md)

## 🙏 Credits

ScaleForge is made possible by:
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) - Core upscaling models
- [NCNN](https://github.com/Tencent/ncnn) - High-performance inference
- Our amazing [contributors](https://github.com/3-0-0/ScaleForge/graphs/contributors)

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

*ScaleForge v0.1.0-beta - Making high-quality upscaling accessible to everyone.*
