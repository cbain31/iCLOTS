import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit
ROOT = Path(__file__).parents[2]
TRACKING_FIXTURES = ROOT / "tests" / "fixtures" / "tracking"


def test_tracking_fixtures_are_small_text_files_without_video_or_workbook_data():
    files = [path for path in TRACKING_FIXTURES.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() in {".csv", ".md"} for path in files)
    assert all(path.stat().st_size < 50_000 for path in files)
    assert not any(path.suffix.lower() in {".avi", ".mp4", ".xlsx", ".xls"} for path in files)


def test_tracking_support_and_tests_do_not_reference_local_data_directory():
    paths = [ROOT / "tests" / "support" / "tracking_reference.py"]
    test_paths = [
        path
        for path in (ROOT / "tests").glob("**/*tracking*.py")
        if path.resolve() != Path(__file__).resolve()
    ]
    content = "\n".join(path.read_text(encoding="utf-8") for path in paths + test_paths)
    assert "data/" not in content and "data\\" not in content


def test_importing_tracking_reference_does_not_load_tkinter_trackpy_or_opencv():
    code = (
        "import sys; import tests.support.tracking_reference; "
        "raise SystemExit(1 if {'tkinter', 'trackpy', 'cv2'} & set(sys.modules) else 0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "relative_path",
    [
        "analysis/single_cell_tracking.py",
        "analysis/sct_fluor.py",
        "analysis/deform.py",
        "analysis/adhvideo.py",
    ],
)
def test_modernized_tracking_adapters_diverge_and_delegate_to_core(relative_path):
    primary = (ROOT / relative_path).read_text(encoding="utf-8")
    duplicate = (ROOT / "iCLOTS_softwareonly" / relative_path).read_text(
        encoding="utf-8"
    )
    assert primary != duplicate
    assert "from iclotspython.core.tracking import" in primary
    assert "iclotspython.core" not in duplicate
