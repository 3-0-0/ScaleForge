#!/bin/bash
# Build ScaleForge CLI as a single-file executable using PyInstaller
set -e
pip install --upgrade pip setuptools wheel pyinstaller
pyinstaller --onefile --name scaleforge src/scaleforge/cli/main.py --collect-all scaleforge

echo "Binary is available in dist/scaleforge"
