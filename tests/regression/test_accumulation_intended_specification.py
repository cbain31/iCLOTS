"""Intended-helper specifications; these do not assert production conformance."""

import json
from pathlib import Path

import numpy as np
import pytest

from tests.support.accumulation_reference import (
    channel_masks_from_bgr,
    connected_components,
    intended_observed_series,
    intended_percent_occlusion,
    microchannel_summaries,
    natural_numeric_order,
    roi_area_summary,
    validate_complete_horizontal_geometry,
)


pytestmark = pytest.mark.regression
FIXTURE = Path(__file__).parents[1] / "fixtures" / "accumulation" / "fixtures.json"


def _fixtures():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_intended_empty_mask_returns_controlled_zero_area_summary():
    assert roi_area_summary(_fixtures()["empty_mask"], 0.5) == {
        "pixels": 0,
        "area_micrometres_squared": 0.0,
    }


def test_intended_zero_area_device_returns_controlled_zero_percent():
    zero = _fixtures()["zero_area_device"]
    assert intended_percent_occlusion(zero, zero) == pytest.approx(0)


def test_intended_all_connected_regions_are_returned_deterministically():
    components = connected_components(_fixtures()["disconnected_device"])
    assert len(components) == 2
    assert components[0][0] == (0, 0)
    assert components[1][0] == (0, 4)


def test_intended_natural_chronological_order_can_be_requested_explicitly():
    names = ["frame1.png", "frame10.png", "frame2.png"]
    assert natural_numeric_order(names) == ["frame1.png", "frame2.png", "frame10.png"]


def test_intended_first_observation_is_not_replaced_by_artificial_baseline():
    result = intended_observed_series([3, 4])
    np.testing.assert_allclose(result["areas"], [3, 4])
    assert np.isnan(result["changes"][0])
    assert result["changes"][1] == pytest.approx(1)


def test_intended_device_percent_is_map_intersected_and_bounded():
    signal = [[1, 1], [1, 1]]
    device = [[1, 0], [0, 0]]
    percent = intended_percent_occlusion(signal, device)
    assert percent == pytest.approx(100)
    assert 0 <= percent <= 100


def test_intended_channel_labels_map_deterministically_to_bgr_layers():
    image = np.asarray([[[3, 2, 1]]])
    masks = channel_masks_from_bgr(image, {"blue": 2, "green": 1, "red": 0})
    assert list(masks) == ["blue", "green", "red"]
    assert all(np.asarray(mask).item() == 1 for mask in masks.values())


def test_intended_incomplete_horizontal_geometry_has_controlled_failure():
    with pytest.raises(ValueError, match="rows must be complete"):
        validate_complete_horizontal_geometry(_fixtures()["broken_microchannel_walls"])


def test_intended_empty_microchannel_map_returns_empty_summary():
    zero = _fixtures()["zero_area_device"]
    assert microchannel_summaries(zero, zero) == []
