

# Contributing Guide

Welcome to ScaleForge! We appreciate your interest in contributing.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/3-0-0/ScaleForge.git
   cd ScaleForge
   ```

2. Set up virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/MacOS
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Running Tests

```bash
pytest tests/ -v
```

## Making Changes

1. Create a new branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. Commit changes with descriptive messages
3. Open a Pull Request against the `main` branch

## Code Style

- Follow PEP 8 guidelines
- Type hints encouraged for new code
- Document public APIs with docstrings

