"""Independent formula checks for multiscale application orchestration."""

from dataclasses import replace
import math

import numpy as np
import pytest

from iclotspython.application.common import Region
from iclotspython.application.contracts import ROIAccumulationRequest
from iclotspython.application.errors import RequestValidationError, WorkflowCancelled
from iclotspython.application.multiscale import MultiscaleRequest, run_multiscale
from tests.support import accumulation_reference as reference

pytestmark = pytest.mark.unit


def images():
    frames = np.zeros((3, 8, 6, 3), dtype=np.uint8)
    frames[0, 1:3, :3, 0] = 100
    frames[1, 1:3, :4, 0] = 100
    frames[2, 1:3, :2, 0] = 100
    frames[2, 5:7, :, 2] = 100  # unselected blue defines a second band
    return ROIAccumulationRequest(tuple(frames), ("red",), {"red": 50, "green": 50, "blue": 50}, 2, "RGB")


def test_device_baseline_signed_changes_and_reference_percentages():
    request = images()
    result = run_multiscale(MultiscaleRequest(request, "device"))
    rows = result.table("Measurements").rows
    assert [r[3] for r in rows] == [0, 6, 8, 4]
    assert [r[-1] for r in rows] == [0, 24, 8, -16]
    bgr = np.asarray(request.frames)[..., ::-1]
    mask = reference.legacy_device_map(bgr)
    expected = [reference.legacy_percent_occlusion(f[:, :, 2] > 50, mask) for f in bgr]
    np.testing.assert_allclose([r[5] for r in rows[1:]], expected)


def test_microchannel_geometry_raw_columns_and_frame_summary_match_reference():
    request = images()
    result = run_multiscale(MultiscaleRequest(request, "microchannel"))
    assert result.table("Geometry").rows == ((1, 3), (5, 7))
    assert len(result.table("Measurements").rows) == 6
    assert result.table("Column occupancy").columns[3:] == tuple(map(str, range(6)))
    assert result.table("Column occupancy").rows[0][3:] == (100, 100, 100, 0, 0, 0)
    assert result.table("Frame summary").rows[0][-2:] == (12, 12)
    assert result.table("Frame summary").rows[-1][-1] == -8
    bgr = np.asarray(request.frames)[..., ::-1]
    geometry = reference.legacy_microchannel_map(bgr[-1], {"red": 50, "green": 50, "blue": 50})
    expected = reference.legacy_microchannel_series([f[:, :, 2] > 50 for f in bgr], geometry)
    for row, raw, expected_row in zip(result.table("Measurements").rows, result.table("Column occupancy").rows, expected):
        assert row[6] == expected_row["mean_occlusion_percent"]
        assert row[-1] == expected_row["accumulation_pixels"] * 4
        np.testing.assert_equal(raw[3:], expected_row["column_occupancy_percent"])


def test_rgb_bgr_equivalence_and_crop():
    request = images()
    a = run_multiscale(MultiscaleRequest(request, "microchannel", Region(1, 0, 4, 8)))
    b = run_multiscale(MultiscaleRequest(replace(request, frames=tuple(f[:, :, ::-1] for f in request.frames), channel_convention="BGR"), "microchannel", Region(1, 0, 4, 8)))
    assert a.tables == b.tables
    assert len(a.table("Column occupancy").columns) == 7


def test_zero_map_preserves_nonfinite_and_empty_geometry_is_controlled():
    request = replace(images(), frames=(np.ones((4, 4, 3), dtype=np.uint8),), thresholds={"red": 0, "green": 50, "blue": 50})
    result = run_multiscale(MultiscaleRequest(request, "device"))
    assert math.isinf(result.table("Measurements").rows[-1][5])
    empty = run_multiscale(MultiscaleRequest(replace(request, thresholds={"red": 50, "green": 50, "blue": 50}), "microchannel"))
    assert empty.table("Measurements").rows == ()
    assert "No horizontal" in empty.warnings[-1]


@pytest.mark.parametrize("roi", [Region(-1, 0, 3, 3), Region(0, 0, 0, 3), Region(0, 0, 99, 3)])
def test_invalid_roi(roi):
    with pytest.raises(RequestValidationError):
        run_multiscale(MultiscaleRequest(images(), "device", roi))


def test_all_geometry_thresholds_required_and_cancellation():
    with pytest.raises(RequestValidationError):
        run_multiscale(MultiscaleRequest(replace(images(), thresholds={"red": 50}), "microchannel"))
    with pytest.raises(WorkflowCancelled):
        run_multiscale(MultiscaleRequest(images(), "device"), is_cancelled=lambda: True)
    progress = []
    result = run_multiscale(MultiscaleRequest(images(), "device"), progress=progress.append)
    assert result.workflow_id == "device_accumulation"
    assert progress[-1].fraction_complete == 1
