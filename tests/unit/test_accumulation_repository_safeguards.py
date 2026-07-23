import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit
ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "accumulation"


def test_accumulation_fixtures_are_small_transparent_text_files():
    files = [path for path in FIXTURES.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() in {".json", ".md", ".csv", ".txt"} for path in files)
    assert all(path.stat().st_size < 50_000 for path in files)


def test_accumulation_fixtures_contain_no_image_video_or_workbook_binaries():
    forbidden = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".avi", ".mp4", ".xlsx", ".xls", ".npy", ".npz"}
    assert not [path for path in FIXTURES.rglob("*") if path.is_file() and path.suffix.lower() in forbidden]


def test_accumulation_support_and_tests_do_not_reference_local_data_directory():
    current = Path(__file__).resolve()
    paths = [
        path
        for path in (ROOT / "tests").glob("**/*accumulation*.py")
        if path.resolve() != current
    ]
    content = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "data/" not in content and "data\\" not in content


def test_importing_accumulation_reference_does_not_load_gui_or_imaging_stacks():
    code = (
        "import sys; import tests.support.accumulation_reference; "
        "blocked={'tkinter','cv2','pandas','skimage','scipy'}; "
        "raise SystemExit(1 if blocked & set(sys.modules) else 0)"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("module", ["occroi.py", "occdevice.py", "occmicro.py"])
def test_primary_and_softwareonly_accumulation_modules_remain_byte_identical(module):
    assert (ROOT / "analysis" / module).read_bytes() == (
        ROOT / "iCLOTS_softwareonly" / "analysis" / module
    ).read_bytes()

