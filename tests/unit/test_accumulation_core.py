"""Production accumulation-core parity with independent Phase 1 references."""

from __future__ import annotations

import math

import numpy as np
import pytest

from iclotspython.core.accumulation import (
    calibrated_area,
    count_signal_pixels,
    legacy_device_map,
    legacy_microchannel_map,
    legacy_microchannel_series,
    legacy_percent_occlusion,
    legacy_series_with_zero_baseline,
    threshold_channel,
)
from tests.support import accumulation_reference as reference


pytestmark = pytest.mark.unit


def test_roi_core_matches_reference():
    values = [3, 2, 5]
    actual = legacy_series_with_zero_baseline(values)
    expected = reference.legacy_series_with_zero_baseline(values)
    np.testing.assert_array_equal(actual.values, expected["areas"])
    np.testing.assert_array_equal(actual.changes, expected["changes"])
    assert count_signal_pixels(threshold_channel([49, 50, 51], 50)) == 1
    assert calibrated_area(4, 0.5) == pytest.approx(1)


def test_device_core_matches_reference_including_nonfinite_percent():
    series = np.zeros((2, 2, 3, 3), dtype=np.uint8)
    series[1, 0, 2, 1] = 11
    np.testing.assert_array_equal(
        legacy_device_map(series), reference.legacy_device_map(series)
    )
    zero = np.zeros((2, 3))
    assert math.isnan(legacy_percent_occlusion(zero, zero))
    assert legacy_percent_occlusion([[1, 0, 0], [0, 0, 0]], zero) == math.inf


def test_microchannel_core_matches_reference():
    last = np.zeros((4, 4, 3), dtype=np.uint8)
    last[0:2, 1, 2] = 60
    thresholds = {"red": 50, "green": 50, "blue": 50}
    channel_map = legacy_microchannel_map(last, thresholds)
    np.testing.assert_array_equal(
        channel_map, reference.legacy_microchannel_map(last, thresholds)
    )
    signal = threshold_channel(last[:, :, 2], 50)
    actual = legacy_microchannel_series([signal], channel_map, 0.5)
    expected = reference.legacy_microchannel_series([signal], channel_map)
    assert len(actual) == len(expected) == 1
    np.testing.assert_allclose(
        actual[0].column_occupancy_percent,
        expected[0]["column_occupancy_percent"],
    )
    assert actual[0].area_pixels == expected[0]["area_pixels"]
    assert actual[0].accumulation_pixels == expected[0]["accumulation_pixels"]
    assert actual[0].area_micrometres_squared == pytest.approx(0.5)
