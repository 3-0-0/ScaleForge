
.PHONY: smoke
smoke:
	mkdir -p /workspace/build/test-reports
	{ python -m scaleforge.cli --help || true; } | tee /workspace/build/cli.log
	pytest -q --junitxml=/workspace/build/test-reports/junit.xml 2>&1 | tee /workspace/build/test.log
