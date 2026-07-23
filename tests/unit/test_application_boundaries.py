"""Architecture safeguards for Phase 3A application and presentation layers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit
ROOT = Path(__file__).parents[2]


def test_fresh_process_imports_do_not_load_gui_or_heavy_presentation_dependencies():
    code = """
import json
import sys
import iclotspython.application
import iclotspython.presentation
from iclotspython.application.roi_accumulation import run_roi_accumulation
blocked = {'tkinter', 'matplotlib', 'pandas', 'cv2', 'trackpy', 'PySide6'}
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


def test_application_service_imports_production_core_without_formula_copy():
    source = (
        ROOT / "iclotspython" / "application" / "roi_accumulation.py"
    ).read_text(encoding="utf-8")
    assert "from iclotspython.core import accumulation as accumulation_core" in source
    assert "legacy_series_with_zero_baseline" in source
    assert "threshold_channel" in source
    assert "np.diff" not in source
    assert "** 2" not in source


def test_contract_and_presentation_modules_do_not_import_pandas_or_gui_packages():
    files = [
        ROOT / "iclotspython" / "application" / "contracts.py",
        ROOT / "iclotspython" / "application" / "errors.py",
        ROOT / "iclotspython" / "application" / "progress.py",
        ROOT / "iclotspython" / "presentation" / "models.py",
        ROOT / "iclotspython" / "presentation" / "tables.py",
    ]
    content = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for forbidden in ("tkinter", "matplotlib", "pandas", "cv2", "trackpy", "PySide6"):
        assert forbidden not in content


def test_legacy_roi_adapter_remains_on_phase2_core_delegation():
    source = (ROOT / "analysis" / "occroi.py").read_text(encoding="utf-8")
    assert "from iclotspython.core.accumulation import" in source
    assert "iclotspython.application" not in source

