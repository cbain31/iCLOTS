"""Headless import safeguards for the Phase 2 production core."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest


pytestmark = pytest.mark.unit


def test_core_import_is_headless():
    code = """
import json
import sys
import iclotspython.core
blocked = ("tkinter", "cv2", "pandas", "matplotlib", "trackpy")
print(json.dumps([name for name in blocked if name in sys.modules]))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout) == []
