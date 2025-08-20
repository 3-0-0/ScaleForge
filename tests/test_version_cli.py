import re
import subprocess

VERSION_RE = re.compile(r"\d+\.\d+\.\d+[a-z0-9\-]*")


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def test_cli_help_version_option():
    res = _run(["python", "-m", "scaleforge.cli", "--version"])
    assert res.returncode == 0
    assert VERSION_RE.search(res.stdout)


def test_cli_help_version_subcommand():
    res = _run(["python", "-m", "scaleforge.cli", "version"])
    assert res.returncode == 0
    assert VERSION_RE.search(res.stdout)
    # outputs should match
    assert res.stdout.strip() == _run(["python", "-m", "scaleforge.cli", "--version"]).stdout.strip()
