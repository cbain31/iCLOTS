import json
from pathlib import Path

import numpy as np
import pytest

from iclotspython.core.accumulation import (
    calibrated_area as pixel_count_to_area,
    column_occupancy,
    count_signal_pixels,
    signed_sequential_changes,
)
from tests.support.accumulation_reference import intended_percent_occlusion


pytestmark = pytest.mark.scientific
FIXTURE = Path(__file__).parents[1] / "fixtures" / "accumulation" / "fixtures.json"


def _fixtures():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_area_scales_with_calibration_squared():
    pixels = count_signal_pixels(_fixtures()["full_mask"])
    assert pixel_count_to_area(pixels, 1.0) == pytest.approx(4 * pixel_count_to_area(pixels, 0.5))


def test_percent_occlusion_is_calibration_invariant():
    signal = _fixtures()["single_positive"]
    device = _fixtures()["full_mask"]
    pixel_percent = intended_percent_occlusion(signal, device)
    signal_pixels = count_signal_pixels(signal)
    device_pixels = count_signal_pixels(device)
    for calibration in (0.5, 1.0, 2.0):
        area_percent = (
            pixel_count_to_area(signal_pixels, calibration)
            / pixel_count_to_area(device_pixels, calibration)
            * 100
        )
        assert area_percent == pytest.approx(pixel_percent)


def test_adding_signal_cannot_lower_same_channel_area():
    counts = [count_signal_pixels(mask) for mask in _fixtures()["increasing_masks"]]
    assert counts == sorted(counts)


def test_identical_masks_yield_zero_signed_change():
    counts = [count_signal_pixels(mask) for mask in _fixtures()["identical_masks"]]
    np.testing.assert_allclose(signed_sequential_changes(counts), [0])


def test_removing_signal_yields_negative_signed_accumulation():
    counts = [count_signal_pixels(mask) for mask in _fixtures()["decreasing_masks"]]
    assert np.all(signed_sequential_changes(counts) < 0)


def test_full_device_mask_has_100_percent_occlusion():
    full = _fixtures()["full_mask"]
    assert intended_percent_occlusion(full, full) == pytest.approx(100)


def test_half_filled_rectangular_channel_has_expected_occupancy():
    signal = [[1, 1, 1, 1], [0, 0, 0, 0]]
    np.testing.assert_allclose(column_occupancy(signal, 0, 2), [50, 50, 50, 50])


def test_rgb_channel_order_does_not_change_per_channel_counts():
    fixture = _fixtures()["disjoint_rgb"]
    first = {name: count_signal_pixels(mask) for name, mask in fixture.items()}
    second = {name: count_signal_pixels(fixture[name]) for name in reversed(list(fixture))}
    assert first == second


def test_translating_signal_within_fixed_device_preserves_raw_area():
    first = np.asarray([[1, 0, 0], [0, 0, 0]])
    translated = np.asarray([[0, 0, 0], [0, 0, 1]])
    assert count_signal_pixels(first) == count_signal_pixels(translated)


def test_device_map_shape_changes_percentage_but_not_raw_signal_area():
    signal = np.asarray([[1, 1], [0, 0]])
    small_device = np.asarray([[1, 1], [0, 0]])
    large_device = np.ones((2, 2), dtype=int)
    assert count_signal_pixels(signal) == 2
    assert intended_percent_occlusion(signal, small_device) == pytest.approx(100)
    assert intended_percent_occlusion(signal, large_device) == pytest.approx(50)


def test_splitting_region_preserves_total_raw_area():
    connected = [[1, 1, 1, 1]]
    split = [[1, 1, 0, 1, 1]]
    assert count_signal_pixels(connected) == count_signal_pixels(split)


def test_columnwise_output_recovers_known_spatial_pattern():
    np.testing.assert_allclose(
        column_occupancy(_fixtures()["known_column_signal"], 0, 2),
        [100, 50, 50, 0],
    )
