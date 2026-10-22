"""Release metadata, dependency recipes and headless launcher boundaries."""

import json
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest

from iclotspython import __version__

pytestmark = pytest.mark.unit
ROOT = Path(__file__).parents[2]


def test_version_and_dependency_recipes_match_package_metadata():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert config["project"]["version"] == __version__
    scientific = set(config["project"]["optional-dependencies"]["analysis"])
    recipe = {line.strip() for line in (ROOT / "requirements-analysis.txt").read_text().splitlines() if line.strip() and not line.startswith("#")}
    assert scientific == recipe
    assert config["project"]["scripts"]["iclots"] == "iclotspython.launcher:main"


def test_environment_diagnostics_do_not_import_optional_stacks():
    script = """
import sys
from iclotspython.launcher import main
assert main(['--check']) == 0
assert not {'PySide6', 'cv2', 'trackpy', 'pandas', 'sklearn', 'matplotlib'} & sys.modules.keys()
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    report = json.loads(result.stdout)
    assert report["iclots"] == __version__
    assert "trackpy" in report["dependencies"]


def test_module_version_command_runs_without_gui():
    result = subprocess.run([sys.executable, "-m", "iclotspython", "--version"], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == __version__


def test_all_new_workflow_imports_are_lazy_in_fresh_process():
    script = """
import sys
import iclotspython.application.multiscale
import iclotspython.application.velocity
import iclotspython.application.tracking
import iclotspython.application.adhesion
import iclotspython.application.clustering
import iclotspython.output.workflows
assert not {'PySide6', 'cv2', 'trackpy', 'pandas', 'skimage', 'sklearn', 'matplotlib', 'openpyxl'} & sys.modules.keys()
"""
    subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
