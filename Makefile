
.PHONY: smoke
smoke:
	mkdir -p /workspace/build/test-reports
	{ python -m scaleforge.cli --help || true; } | tee /workspace/build/cli.log
	pytest -q --junitxml=/workspace/build/test-reports/junit.xml 2>&1 | tee /workspace/build/test.log


.PHONY: venv demo-smoke

venv:
python -m venv .venv
. .venv/bin/activate && pip install -U pip && pip install -e ".[demo]" pytest

demo-smoke:
. .venv/bin/activate && SF_HEAVY_TESTS=0 pytest -q -k "demo or cli_help"

