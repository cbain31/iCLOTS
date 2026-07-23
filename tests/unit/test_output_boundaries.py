"""Headless and architectural safeguards for Phase 3B services."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit
ROOT = Path(__file__).parents[2]


def test_output_import_is_lazy_and_headless_in_fresh_process():
    code = """
import json
import sys
import iclotspython.output
from iclotspython.output.plotting import render_roi_plot
from iclotspython.output.exporting import export_roi_data
blocked = {'tkinter', 'PySide6', 'matplotlib', 'pandas', 'openpyxl', 'cv2', 'trackpy'}
print(json.dumps(sorted(blocked & set(sys.modules))))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "[]"


def test_output_services_consume_presentation_result_not_scientific_core():
    files = [
        ROOT / "iclotspython" / "output" / "plotting.py",
        ROOT / "iclotspython" / "output" / "exporting.py",
    ]
    content = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "iclotspython.presentation" in content
    assert "iclotspython.core" not in content
    assert "threshold_channel" not in content
    assert "calibrated_area" not in content
    assert "legacy_series_with_zero_baseline" not in content


def test_output_modules_do_not_reference_gui_frameworks_or_legacy_adapters():
    paths = list((ROOT / "iclotspython" / "output").glob("*.py"))
    content = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for forbidden in (
        "tkinter",
        "PySide6",
        "analysis.occroi",
        "matplotlib.pyplot",
        "pandas",
    ):
        assert forbidden not in content

