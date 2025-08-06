
# Manual PyInstaller Build (Linux/macOS)

## Step 1: Clone Fresh Copy
```bash
git clone https://github.com/3-0-0/ScaleForge.git /tmp/build
cd /tmp/build
```

## Step 2: Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies
```bash
pip install -e .
pip install pyinstaller
```

## Step 4: Build Binary
```bash
pyinstaller --onefile \
  --name scaleforge \
  --add-data "src/scaleforge/models/model_registry.json:scaleforge/models" \
  src/scaleforge/cli/main.py
```

## Step 5: Run
```bash
./dist/scaleforge --version
```
