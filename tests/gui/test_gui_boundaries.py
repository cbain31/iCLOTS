"""Import and architectural safeguards for the modern GUI boundary."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


pytestmark = [pytest.mark.unit, pytest.mark.gui]
ROOT = Path(__file__).parents[2]
GUI_ROOT = ROOT / "iclotspython" / "gui"


def _fresh_process(source: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_gui_package_import_has_no_window_or_qt_side_effects():
    completed = _fresh_process(
        "import sys; import iclotspython, iclotspython.gui; "
        "assert 'PySide6' not in sys.modules; print('clean')"
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "clean"


def test_application_and_core_imports_do_not_load_qt():
    completed = _fresh_process(
        "import sys; import iclotspython.application, iclotspython.core; "
        "assert not any(name.startswith('PySide6') for name in sys.modules)"
    )
    assert completed.returncode == 0, completed.stderr


def test_gui_modules_import_headlessly_without_opening_windows():
    completed = _fresh_process(
        "from PySide6.QtWidgets import QApplication; "
        "app=QApplication([]); "
        "import iclotspython.gui.application, iclotspython.gui.main_window; "
        "assert not app.topLevelWidgets()"
    )
    assert completed.returncode == 0, completed.stderr


def test_gui_source_has_no_legacy_gui_or_scientific_formula_dependency():
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in GUI_ROOT.glob("*.py")
    ).lower()
    assert "tkinter" not in source
    assert "gui.occroi" not in source
    assert "analysis.occroi" not in source
    assert "threshold_channel(" not in source
    assert "count_signal_pixels(" not in source
    assert "iclotspython.core" not in source
    assert "from iclotspython.application" in source
    assert "from iclotspython.presentation" in source
    assert "from iclotspython.output" in source
    assert ".write_text(" not in source
    assert ".write_bytes(" not in source
    assert "open(" not in source


def test_canonical_entrypoint_and_optional_dependency_file_exist():
    assert (GUI_ROOT / "__main__.py").is_file()
    requirements = (ROOT / "requirements-gui.txt").read_text(encoding="utf-8")
    assert "PySide6>=6.9,<6.10" in requirements
    assert "matplotlib" in requirements
    assert "openpyxl" in requirements
