import json
import math
from pathlib import Path

import numpy as np
import pytest

from tests.support.accumulation_reference import (
    count_signal_pixels,
    legacy_device_map,
    legacy_lexical_image_order,
    legacy_microchannel_map,
    legacy_microchannel_series,
    legacy_percent_occlusion,
    legacy_series_with_zero_baseline,
    microchannel_summaries,
)


pytestmark = pytest.mark.regression
FIXTURE = Path(__file__).parents[1] / "fixtures" / "accumulation" / "fixtures.json"


def _fixtures():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_legacy_roi_inserts_zero_baseline():
    result = legacy_series_with_zero_baseline([1, 2, 3])
    np.testing.assert_allclose(result["areas"], [0, 1, 2, 3])
    np.testing.assert_allclose(result["changes"], [0, 1, 1, 1])


def test_legacy_roi_preserves_negative_interframe_change():
    result = legacy_series_with_zero_baseline([3, 2, 1])
    np.testing.assert_allclose(result["changes"], [0, 3, -1, -1])


def test_legacy_device_also_inserts_zero_baseline():
    result = legacy_series_with_zero_baseline([2, 2])
    np.testing.assert_allclose(result["areas"], [0, 2, 2])
    np.testing.assert_allclose(result["changes"], [0, 2, 0])


def test_legacy_device_map_depends_on_full_series_signal():
    series = np.zeros((2, 2, 3, 3), dtype=int)
    series[0, 0, 0, 2] = 11
    series[1, 1, 2, 1] = 11
    expected = [[1, 0, 0], [0, 0, 1]]
    np.testing.assert_array_equal(legacy_device_map(series), expected)


def test_legacy_device_percent_numerator_is_not_restricted_to_map():
    signal = [[1, 1], [1, 1]]
    device = [[1, 0], [0, 0]]
    assert legacy_percent_occlusion(signal, device) == pytest.approx(400)


def test_legacy_device_zero_area_yields_nonfinite_percent():
    zero = _fixtures()["zero_area_device"]
    assert math.isnan(legacy_percent_occlusion(zero, zero))


def test_legacy_microchannel_map_depends_only_on_last_frame():
    earlier = np.zeros((3, 4, 3), dtype=int)
    earlier[0, 0, 2] = 51
    final = np.zeros((3, 4, 3), dtype=int)
    final[2, 1, 1] = 51
    map_mask = legacy_microchannel_map(final, {"red": 50, "green": 50, "blue": 50})
    np.testing.assert_array_equal(map_mask, [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1]])
    assert count_signal_pixels(legacy_microchannel_map(earlier, {"red": 50, "green": 50, "blue": 50})) == 4


def test_legacy_microchannel_map_uses_all_rgb_layers_regardless_of_output_selection():
    final = np.zeros((2, 4, 3), dtype=int)
    final[0, 2, 0] = 51
    map_mask = legacy_microchannel_map(final, {"red": 50, "green": 50, "blue": 50})
    np.testing.assert_array_equal(map_mask, [[1, 1, 1, 1], [0, 0, 0, 0]])


def test_legacy_microchannel_regions_are_contiguous_horizontal_row_bands():
    straight = _fixtures()["straight_microchannel"]
    summaries = microchannel_summaries(straight, straight)
    assert [(item["row_start"], item["row_end"]) for item in summaries] == [(1, 3)]


def test_legacy_rgb_overlap_is_counted_independently():
    fixture = _fixtures()["overlapping_rgb"]
    assert count_signal_pixels(fixture["red"]) == 1
    assert count_signal_pixels(fixture["green"]) == 1


def test_legacy_file_order_is_lexical_with_extension_grouping():
    ordered = legacy_lexical_image_order(_fixtures()["filenames"])
    assert ordered == ["frame1.png", "frame10.png", "frame2.png", "frame01.jpg", "frame02.jpg"]


def test_legacy_microchannel_output_uses_zero_based_roi_relative_columns():
    summary = microchannel_summaries(
        _fixtures()["known_column_signal"], [[1, 1, 1, 1], [1, 1, 1, 1]]
    )[0]
    assert summary["channel"] == 0
    assert list(range(len(summary["column_occupancy_percent"]))) == [0, 1, 2, 3]


def test_legacy_microchannel_first_frame_accumulation_is_area_from_zero_state():
    signal = _fixtures()["known_column_signal"]
    series = legacy_microchannel_series([signal], [[1, 1, 1, 1], [1, 1, 1, 1]])
    assert series[0]["frame"] == 0
    assert series[0]["area_pixels"] == 4
    assert series[0]["accumulation_pixels"] == pytest.approx(4)
