import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit
ROOT = Path(__file__).parents[2]


def test_no_tracked_files_exist_under_data():
    result = subprocess.run(
        ["git", "ls-files", "--", "data"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""


def test_expected_phase_0_audit_records_exist():
    expected = (
        "docs/audit/README.md",
        "audit_outputs/velocity_validation/velocity_validation_report.md",
        "audit_outputs/velocity_validation/archived_profile_metrics.csv",
        "audit_outputs/velocity_reproduction/velocity_reproduction_report.md",
        "audit_outputs/velocity_reproduction/reference_summary.csv",
    )
    missing = [path for path in expected if not (ROOT / path).is_file()]
    assert not missing, f"missing Phase 0 records: {missing}"


@pytest.mark.parametrize(
    "relative_path",
    [
        "iCLOTS.py",
        "analysis/velocity.py",
        "gui/velocity.py",
        "iCLOTS_softwareonly/analysis/velocity.py",
        "iCLOTS_softwareonly/gui/velocity.py",
    ],
)
def test_critical_source_file_compiles(relative_path):
    path = ROOT / relative_path
    compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_importing_pure_velocity_support_does_not_load_tkinter():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import tests.support.velocity_reference; "
            "raise SystemExit(1 if 'tkinter' in sys.modules else 0)",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_modernized_velocity_adapter_diverges_and_delegates_to_core():
    primary = (ROOT / "analysis/velocity.py").read_text(encoding="utf-8")
    duplicate = (
        ROOT / "iCLOTS_softwareonly/analysis/velocity.py"
    ).read_text(encoding="utf-8")
    assert primary != duplicate
    assert "from iclotspython.core.velocity import" in primary
    assert "iclotspython.core" not in duplicate

