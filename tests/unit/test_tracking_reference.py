import math

import pytest

from tests.support.tracking_reference import (
    absolute_x_endpoint_displacement,
    adhesion_area_and_eccentricity,
    calibrated_distance,
    elapsed_time,
    euclidean_endpoint_displacement,
    filter_tracks_by_observation_count,
    fluorescence_area_and_intensity,
    intended_general_distance_included,
    intended_velocity,
    legacy_area_mass,
    legacy_general_distance_included,
    legacy_velocity,
    signed_x_endpoint_displacement,
)


pytestmark = pytest.mark.unit


def _track(end_x, end_y, end_frame=2):
    return [
        {"particle": 0, "frame": 0, "x": 0, "y": 0},
        {"particle": 0, "frame": end_frame, "x": end_x, "y": end_y},
    ]


def test_euclidean_endpoint_displacement():
    assert euclidean_endpoint_displacement(_track(3, 4)) == pytest.approx(5)


def test_signed_and_absolute_x_endpoint_displacement():
    track = _track(-3, 4)
    assert signed_x_endpoint_displacement(track) == pytest.approx(-3)
    assert absolute_x_endpoint_displacement(track) == pytest.approx(3)


def test_zero_endpoint_displacement():
    assert euclidean_endpoint_displacement(_track(0, 0)) == pytest.approx(0)


def test_diagonal_displacement_exceeds_axial_component():
    track = _track(3, 4)
    assert euclidean_endpoint_displacement(track) == pytest.approx(5)
    assert absolute_x_endpoint_displacement(track) == pytest.approx(3)


def test_elapsed_time_uses_frame_index_difference_and_fps():
    assert elapsed_time(_track(4, 0, end_frame=5), fps=10) == pytest.approx(0.5)


def test_elapsed_time_rejects_nonpositive_fps():
    with pytest.raises(ValueError, match="FPS must be positive"):
        elapsed_time(_track(4, 0), fps=0)


def test_calibrated_distance_scales_pixels():
    assert calibrated_distance(4, 0.5) == pytest.approx(2)


def test_known_velocity_calculation():
    assert intended_velocity(distance_micrometres=2, elapsed_seconds=0.2) == pytest.approx(10)


def test_intended_zero_duration_is_rejected():
    with pytest.raises(ValueError, match="elapsed time must be positive"):
        intended_velocity(2, 0)


def test_legacy_zero_duration_returns_nonfinite_values():
    assert math.isnan(legacy_velocity(0, 0))
    assert legacy_velocity(2, 0) == math.inf
    assert legacy_velocity(-2, 0) == -math.inf


def test_legacy_general_threshold_is_strict_at_one_third_gui_value():
    assert not legacy_general_distance_included(3, gui_minimum_pixels=9)
    assert not legacy_general_distance_included(2.9, gui_minimum_pixels=9)
    assert legacy_general_distance_included(3.1, gui_minimum_pixels=9)


def test_intended_general_threshold_is_literal_and_inclusive():
    assert not intended_general_distance_included(8.9, gui_minimum_pixels=9)
    assert intended_general_distance_included(9, gui_minimum_pixels=9)
    assert intended_general_distance_included(9.1, gui_minimum_pixels=9)


def test_filter_tracks_counts_observations_not_frame_span():
    rows = [
        {"particle": 0, "frame": 0},
        {"particle": 0, "frame": 2},
        {"particle": 0, "frame": 3},
        {"particle": 1, "frame": 0},
        {"particle": 1, "frame": 20},
    ]
    filtered = filter_tracks_by_observation_count(rows, 3)
    assert {row["particle"] for row in filtered} == {0}


def test_brightfield_legacy_area_is_mean_mass_divided_by_255():
    rows = [
        {"particle": 0, "frame": 0, "mass": 255},
        {"particle": 0, "frame": 1, "mass": 765},
    ]
    assert legacy_area_mass(rows) == pytest.approx(2)


def test_fluorescence_summary_uses_mean_size_area_and_mean_mass():
    rows = [
        {"particle": 0, "frame": 0, "size": 1, "mass": 100},
        {"particle": 0, "frame": 1, "size": 3, "mass": 300},
    ]
    result = fluorescence_area_and_intensity(rows)
    assert result["area_pixels"] == pytest.approx(math.pi * 4)
    assert result["fluorescence"] == pytest.approx(200)


def test_adhesion_summary_scales_area_and_averages_eccentricity():
    rows = [
        {"particle": 0, "frame": 0, "mass": 255, "ecc": 0.2},
        {"particle": 0, "frame": 1, "mass": 765, "ecc": 0.4},
    ]
    result = adhesion_area_and_eccentricity(rows, micrometres_per_pixel=0.5)
    assert result["area_micrometres_squared"] == pytest.approx(0.5)
    assert result["mean_eccentricity_labeled_circularity"] == pytest.approx(0.3)
