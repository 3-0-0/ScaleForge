<!-- README banner -->
<p align="center">
  <img src="ScaleForge.png"
       alt="ScaleForge — a dragon forging pixels into detail"
       width="960"
       height="480">
</p>

# ScaleForge

Fast, portable AI upscaler/resizer powered by Real-ESRGAN — with smart GPU detection and a single pipeline for CLI and GUI.

<p align="center">
  <!-- Optional banner: put an image at assets/brand/banner.png and uncomment -->
  <!--<img src="assets/brand/banner.png" width="720" alt="ScaleForge banner">-->
</p>

[![CI](https://img.shields.io/github/actions/workflow/status/3-0-0/ScaleForge/ci.yml?label=CI)](https://github.com/3-0-0/ScaleForge/actions)
[![Release](https://img.shields.io/github/v/release/3-0-0/ScaleForge)](https://github.com/3-0-0/ScaleForge/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![OS](https://img.shields.io/badge/OS-Windows%20%7C%20Linux-lightgrey.svg)

---

## Why ScaleForge?
- **One code path** for CLI + GUI. No duplicate logic.
- **Smart backend selection** with fallbacks:
  - NVIDIA → PyTorch CUDA  
  - AMD (Linux ROCm-capable) → PyTorch ROCm  
  - Intel/AMD (no CUDA/ROCm) → NCNN/Vulkan  
  - Else → PyTorch CPU
- **No-drama install** (venv or portable build).  
- **Model manager**: list, fetch, cache, resume.  
- **Batteries included**: tiny sample + CPU-only demo to verify your setup.

---

## Quick start

### A) From source (dev workflow)

```bash
# 1) Clone and enter
git clone https://github.com/3-0-0/ScaleForge.git
cd ScaleForge

# 2) Create an isolated env (Python 3.12)
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
# .\.venv\Scripts\Activate.ps1

# 3) Install (dev extras include ruff/pytest)
pip install -e ".[dev]"
````

Verify the pipeline end-to-end (CPU-only sanity check):

```bash
# Detect backend (prints decision + reasons)
scaleforge detect-backend --debug

# List built-in and user models
scaleforge models list

# Fetch a model (cached; resumes on retry)
scaleforge models fetch realesrgan-x4plus

# Run the tiny demo (bundled 128×128 → 2x)
scaleforge demo --cpu-only
# Output: samples/out/demo_2x.png
```

Run on your own image:

```bash
scaleforge run --in input.jpg --out out.png --scale 2x --backend auto
```

> Tip: `--backend auto` chooses the best available accelerator and logs the fallback chain used.

---

## GUI (minimal path)

```bash
scaleforge gui
# Select image → Run. Uses the same pipeline as the CLI.
```

---

## Features at a glance

* Model registry with schema validation (built-ins + user models)
* Robust download: checksum, resume, local cache
* Tiled/streamed processing to avoid OOM
* Decision log (why a backend was chosen, and what fell back)
* Clean logs; `--debug` for deeper traces
* Tests + ruff-clean code

---

## Roadmap

* Sprint 20-B-F “finalize”

  * ✅ Model downloader + registry polish (schema validate, CLI)
  * ✅ Backend fallback: CUDA → ROCm/NCNN → CPU (decision log)
  * ✅ One pipeline for CLI + GUI
  * ⏳ Docs site + tiny video/GIF demo
* Next

  * Presets (quality/speed/memory)
  * Batch jobs + resume/skip on failure
  * Packaged builds (Windows first), `pipx` install
  * Advanced model zoo (ESRGAN variants, face enhancer, denoise)

---

## Development

```bash
# Lint
ruff check .

# Tests
pytest -q

# Type checks (optional if enabled)
# mypy src/
```

Project layout:

```
src/            # library + CLI + GUI (single pipeline)
tests/          # unit tests
samples/        # tiny demo input + outputs
assets/         # images, logos, GIFs for README/docs
```

---

## Backend selection (summary)

1. Detect hardware + drivers
2. Score candidates by capability
3. Try in order; on failure, log and fall back
4. Expose final choice via `detect-backend --debug`

This keeps “works everywhere” as the default.

---

## Contributing

Issues and PRs welcome. Please:

1. Open an issue describing the change
2. Keep diffs minimal and ruff-clean
3. Add/adjust tests for behavior changes

---

# Credits

## 🧠 Core Contributors

- **300**  
  _Project creator, visionary, and development lead; coordinated AI-agent workflows and oversaw project management._

- **Nexus (ChatGPT)**  
  _Partner AI; architectural co-designer & planner, strategic guidance, troubleshooting, documentation, and quality assurance._  
  → Powered by GPT-5, GPT-4o, GPT-4.5, GPT-4-turbo (o3), and o4-mini-high from [OpenAI](https://openai.com).

- **OpenHands Agent**  
  _Autonomous software engineer; responsible for the majority of the ScaleForge codebase, including initial backend and frontend implementations._  
  → Uses [OpenHands](https://github.com/All-Hands-AI/OpenHands) runtime with GPT APIs to operate independently.

- **Deepseek-Coder**  
  _Auxiliary agent used to reduce compute costs during development._  
  → Powered by [DeepSeek-Coder 1.5](https://github.com/deepseek-ai/DeepSeek-Coder), a distilled model trained on GPT-3.5 and GPT-4 via OpenAI API.



## ⚙️ Upstream Projects & Libraries

ScaleForge is made possible by the incredible open-source ecosystem. Huge thanks to the following projects:

### 🔮 Image Upscaling
- [**Real-ESRGAN**](https://github.com/xinntao/Real-ESRGAN) – super-resolution model for photo-realistic image enhancement, by Xintao Wang et al.  
- [**ncnn**](https://github.com/Tencent/ncnn) – fast neural-network inference framework by Tencent.  
- [**PyTorch**](https://pytorch.org/) – deep-learning framework by Meta AI.

### 🖼️ UI / Frontend
- [**Kivy**](https://kivy.org/) – cross-platform UI framework for Python.

### 🧪 Tooling & Developer Experience
- [**ruff**](https://github.com/astral-sh/ruff) – fast Python linter  
- [**black**](https://github.com/psf/black) – Python code formatter  
- [**mypy**](https://github.com/python/mypy) – static type checker  
- [**pytest**](https://pytest.org/) – unit-testing framework  
- [**mkdocs**](https://www.mkdocs.org/) – documentation generator  
- [**mkdocs-material**](https://squidfunk.github.io/mkdocs-material/) – beautiful docs theme  
- [**EditorConfig**](https://editorconfig.org/) – consistent coding styles across editors  



## 🤝 Community Contributions
_We welcome feedback, bug reports, and pull requests from the broader community. Join us on GitHub to help improve ScaleForge!_



## 🌐 Project Resources
- **GitHub Repository**: [ScaleForge on GitHub](https://github.com/3-0-0/scaleforge)  
- **Documentation**: _(coming soon)_ :contentReference[oaicite:7]{index=7}



## 💡 Inspiration
- [**NASA / JWST Wallpapers – Webb Telescope**](https://webbtelescope.org/resource-gallery/images)  
- [**NASA / JWST Wallpapers – Flickr**](https://www.flickr.com/photos/nasawebbtelescope/)  
  The beauty of the cosmos inspired the first use case that led to the creation of ScaleForge. :contentReference[oaicite:8]{index=8}



## 🛠️ Infrastructure & CI/CD
- [**GitHub Actions**](https://github.com/features/actions) – continuous integration and delivery

---

## 📄 License
ScaleForge is released under the [MIT License](LICENSE).

---
