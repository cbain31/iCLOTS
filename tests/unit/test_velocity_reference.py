import numpy as np
import pytest

from tests.support.velocity_reference import (
    axial_displacement,
    displacement_to_velocity,
    euclidean_displacement,
    frame_statistics,
    profile_bin_means,
    profile_edges,
    profile_metrics,
)


pytestmark = pytest.mark.unit


def test_euclidean_displacement_uses_both_axes():
    assert euclidean_displacement((1, 2), (4, 6)) == pytest.approx(5.0)


def test_axial_displacement_uses_absolute_x_only():
    assert axial_displacement((4, 2), (1, 20)) == pytest.approx(3.0)


def test_displacement_converts_pixels_per_frame_to_micrometres_per_second():
    assert displacement_to_velocity(2.0, fps=100, micrometres_per_pixel=0.875) == pytest.approx(175.0)


def test_velocity_scales_linearly_with_fps():
    baseline = displacement_to_velocity(2.5, 80, 0.5)
    assert displacement_to_velocity(2.5, 160, 0.5) == pytest.approx(2 * baseline)


def test_velocity_scales_linearly_with_micrometres_per_pixel():
    baseline = displacement_to_velocity(2.5, 80, 0.5)
    assert displacement_to_velocity(2.5, 80, 1.0) == pytest.approx(2 * baseline)


def test_frame_wise_minimum_mean_and_maximum():
    result = frame_statistics([1, 0, 1, 0, 1], [8, 2, 4, 6, 12])
    np.testing.assert_array_equal(result["frame"], [0, 1])
    np.testing.assert_allclose(result["minimum"], [2, 4])
    np.testing.assert_allclose(result["mean"], [4, 8])
    np.testing.assert_allclose(result["maximum"], [6, 12])


def test_frame_statistics_reject_mismatched_inputs():
    with pytest.raises(ValueError, match="same shape"):
        frame_statistics([0, 1], [2])


def test_profile_edge_construction():
    np.testing.assert_allclose(profile_edges(8, 4), [0, 2, 4, 6, 8])


def test_profile_edges_require_positive_inputs():
    with pytest.raises(ValueError, match="positive"):
        profile_edges(0, 4)


def test_interior_boundary_belongs_to_bin_on_right():
    coordinates, means = profile_bin_means([1.0, 2.0, 3.0], [10, 20, 30], [0, 2, 4])
    np.testing.assert_allclose(coordinates, [2, 4])
    np.testing.assert_allclose(means, [10, 25])


def test_final_upper_edge_is_excluded_from_reported_bins():
    _, means = profile_bin_means([1.0, 4.0], [10, 99], [0, 2, 4])
    assert means[0] == pytest.approx(10)
    assert np.isnan(means[1])


def test_empty_profile_bin_is_nan():
    _, means = profile_bin_means([0.5, 3.5], [10, 30], [0, 1, 2, 3, 4])
    np.testing.assert_allclose(means[[0, 3]], [10, 30])
    assert np.isnan(means[1]) and np.isnan(means[2])


def test_profile_metric_definitions():
    metrics = profile_metrics([-2, -1, 0, 1, 2], [6, 9, 10, 9, 6])
    assert metrics["wall_to_max_ratio"] == pytest.approx(0.6)
    assert metrics["center_to_wall_contrast"] == pytest.approx(0.4)
    assert metrics["normalized_range"] == pytest.approx(0.4)
    assert metrics["profile_cv"] == pytest.approx(np.std([6, 9, 10, 9, 6], ddof=1) / 8)
    assert metrics["quadratic_coefficient_raw"] == pytest.approx(-1.0)
    assert metrics["quadratic_coefficient_normalized"] == pytest.approx(-0.1)
    assert metrics["quadratic_r2"] == pytest.approx(1.0)
