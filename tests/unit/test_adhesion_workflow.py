"""Static adhesion core parity, strict bounds and application validation."""

from dataclasses import astuple, replace

import numpy as np
import pytest

from iclotspython.application.adhesion import AdhesionRequest, run_adhesion
from iclotspython.application.contracts import ROIAccumulationRequest
from iclotspython.application.errors import RequestValidationError, WorkflowCancelled
from iclotspython.core.adhesion import segment_legacy_cells
from tests.support.adhesion_reference import legacy_cells

pytestmark = pytest.mark.unit


def cell_image():
    rgb = np.zeros((64, 80, 3), dtype=np.uint8)
    rgb[10:24, 12:42, 0] = 100  # deliberately nonsquare
    rgb[12:18, 15:20, 1] = 70
    rgb[40:44, 10:14, 0] = 50  # equality to threshold must be excluded
    return rgb


def image_request():
    return ROIAccumulationRequest((cell_image(),), ("red",), {"red": 50}, 2, "RGB")


@pytest.mark.parametrize("filopodia", [False, True])
def test_core_matches_independent_legacy_regionprops_table(filopodia):
    rgb = cell_image()
    actual = segment_legacy_cells(rgb[:, :, 0], rgb[:, :, 1], 2, 0, 10000, 50, 30, filopodia=filopodia)
    expected = legacy_cells(rgb[:, :, 0], rgb[:, :, 1], calibration=2, filopodia=filopodia)
    np.testing.assert_allclose([astuple(c) for c in actual], expected, rtol=1e-12)
    assert actual[0].area_pixels == 420
    assert actual[0].functional_intensity == 6 * 5 * 70


def test_strict_area_bounds_and_thresholds():
    rgb = cell_image()
    assert not segment_legacy_cells(rgb[:, :, 0], rgb[:, :, 1], 1, 420, 1000, 50, 30)
    assert not segment_legacy_cells(rgb[:, :, 0], rgb[:, :, 1], 1, 0, 420, 50, 30)
    cells = segment_legacy_cells(rgb[:, :, 0], rgb[:, :, 1], 1, 0, 1000, 50, 70)
    assert cells[0].functional_signal == cells[0].functional_intensity == 0


@pytest.mark.parametrize("mode", ["fluorescence", "filopodia"])
def test_independent_image_dimensions_calibration_density_and_metadata(mode):
    request = replace(image_request(), frames=(cell_image(), cell_image()[:30]), frame_labels=("first", "second"))
    result = run_adhesion(AdhesionRequest(request, mode, primary_channel="red", functional_channel="green"))
    assert len(result.table("Measurements").rows) == 2
    assert result.table("Measurements").rows[0][5] == 1680
    summary = result.table("Image summary").rows
    assert summary[0][3] == pytest.approx(1 / (64 * 80 * 4 / 1E6))
    assert summary[-1][1] == 2
    assert dict(result.parameters)["micrometres_per_pixel"] == 2


def test_brightfield_area_and_real_trackpy():
    pytest.importorskip("trackpy")
    result = run_adhesion(AdhesionRequest(image_request(), "brightfield", minmass=10, invert=False))
    rows = result.table("Measurements").rows
    assert rows
    assert rows[0][4] == pytest.approx(rows[0][-1] ** 2 * np.pi)
    assert rows[0][5] == rows[0][4] * 4


@pytest.mark.parametrize("field,value", [("maxarea", 0), ("primary_threshold", 256), ("diameter", 2), ("threshold_rel", 2), ("primary_channel", "unknown")])
def test_invalid_adhesion_parameters(field, value):
    with pytest.raises(RequestValidationError):
        run_adhesion(replace(AdhesionRequest(image_request()), **{field: value}))


def test_cancel_before_segmentation():
    with pytest.raises(WorkflowCancelled):
        run_adhesion(AdhesionRequest(image_request()), is_cancelled=lambda: True)
