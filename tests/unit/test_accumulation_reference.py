import json
import math
from pathlib import Path

import numpy as np
import pytest

from tests.support.accumulation_reference import (
    channel_masks_from_bgr,
    column_occupancy,
    connected_components,
    count_signal_pixels,
    legacy_percent_occlusion,
    microchannel_summaries,
    pixel_count_to_area,
    signed_sequential_changes,
    threshold_channel,
)


pytestmark = pytest.mark.unit
FIXTURE = Path(__file__).parents[1] / "fixtures" / "accumulation" / "fixtures.json"


def _fixtures():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_legacy_threshold_is_strict_below_equal_and_above_cutoff():
    values = _fixtures()["threshold_values"]
    np.testing.assert_array_equal(threshold_channel(values, 50), [0, 0, 1])


def test_signal_pixel_counting():
    assert count_signal_pixels(_fixtures()["single_positive"]) == 1
    assert count_signal_pixels(_fixtures()["empty_mask"]) == 0


def test_pixel_count_converts_to_physical_area():
    assert pixel_count_to_area(8, 0.5) == pytest.approx(2)


def test_physical_area_uses_squared_calibration():
    baseline = pixel_count_to_area(8, 0.5)
    assert pixel_count_to_area(8, 1.0) == pytest.approx(4 * baseline)


def test_nonpositive_calibration_is_rejected():
    with pytest.raises(ValueError, match="must be positive"):
        pixel_count_to_area(1, 0)


def test_percent_occlusion_uses_signal_over_device_area():
    signal = [[1, 1], [0, 0]]
    device = [[1, 1], [1, 1]]
    assert legacy_percent_occlusion(signal, device) == pytest.approx(50)


def test_legacy_zero_denominator_returns_nonfinite_values():
    zero = _fixtures()["zero_area_device"]
    assert math.isnan(legacy_percent_occlusion(zero, zero))
    assert legacy_percent_occlusion([[1, 0, 0], [0, 0, 0]], zero) == math.inf


def test_sequential_signed_differences_include_zero_and_negative_changes():
    np.testing.assert_allclose(signed_sequential_changes([1, 1, 3, 2]), [0, 2, -1])


def test_identical_consecutive_frames_have_zero_difference():
    masks = _fixtures()["identical_masks"]
    counts = [count_signal_pixels(mask) for mask in masks]
    np.testing.assert_allclose(signed_sequential_changes(counts), [0])


def test_column_occupancy_reports_percentage_by_band_height():
    occupancy = column_occupancy(_fixtures()["known_column_signal"], 0, 2)
    np.testing.assert_allclose(occupancy, [100, 50, 50, 0])


def test_microchannel_summary_reports_mean_max_and_area():
    signal = _fixtures()["known_column_signal"]
    channel_map = [[1, 1, 1, 1], [1, 1, 1, 1]]
    summary = microchannel_summaries(signal, channel_map)[0]
    assert summary["mean_occlusion_percent"] == pytest.approx(50)
    assert summary["max_occlusion_percent"] == pytest.approx(100)
    assert summary["area_pixels"] == 4


def test_multiple_horizontal_regions_are_numbered_top_to_bottom():
    summaries = microchannel_summaries(
        _fixtures()["multiple_horizontal_microchannels"],
        _fixtures()["multiple_horizontal_microchannels"],
    )
    assert [(item["channel"], item["row_start"], item["row_end"]) for item in summaries] == [
        (0, 0, 1),
        (1, 3, 5),
    ]


def test_connected_components_use_deterministic_row_major_order():
    components = connected_components(_fixtures()["disconnected_device"])
    assert components == [[(0, 0), (1, 0)], [(0, 4), (1, 4)]]


def test_bgr_channel_mapping_is_deterministic():
    image = np.zeros((1, 1, 3), dtype=int)
    image[0, 0] = [30, 20, 10]
    masks = channel_masks_from_bgr(image, {"red": 5, "green": 15, "blue": 25})
    assert count_signal_pixels(masks["red"]) == 1
    assert count_signal_pixels(masks["green"]) == 1
    assert count_signal_pixels(masks["blue"]) == 1

