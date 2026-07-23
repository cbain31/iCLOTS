"""Production velocity-core parity with independent Phase 1 references."""

from __future__ import annotations

import numpy as np
import pytest

from iclotspython.core.velocity import (
    accepted_point_measurements,
    frame_summary,
    profile_edges,
    velocity_profile,
)
from tests.support import velocity_reference as reference


pytestmark = pytest.mark.unit


def test_accepted_rows_use_unsigned_2d_motion_and_destination_y():
    source = [[1, 2], [2, 4]]
    destination = [[4, 6], [2, 5]]
    frames, positions, velocities = accepted_point_measurements(
        7, source, destination, fps=2, micrometres_per_pixel=0.5
    )
    np.testing.assert_array_equal(frames, [7, 7])
    np.testing.assert_array_equal(positions, [6, 5])
    np.testing.assert_allclose(
        velocities,
        reference.displacement_to_velocity(
            reference.euclidean_displacement(source, destination), 2, 0.5
        ),
    )


def test_frame_summary_matches_reference_and_legacy_time_vector():
    frames = [1, 1, 3]
    velocities = [2, 4, 8]
    result = frame_summary(frames, velocities, fps=2)
    expected = reference.frame_statistics(frames, velocities)
    np.testing.assert_array_equal(result.frames, expected["frame"])
    np.testing.assert_allclose(result.minimum, expected["minimum"])
    np.testing.assert_allclose(result.mean, expected["mean"])
    np.testing.assert_allclose(result.maximum, expected["maximum"])
    np.testing.assert_allclose(result.time_seconds, [0, 1])


def test_profile_matches_reference_upper_edges_means_and_empty_bins():
    positions = [0.5, 1.5, 3.5]
    velocities = [1, 3, 8]
    edges = profile_edges(4, 4)
    expected_edges, expected_means = reference.profile_bin_means(
        positions, velocities, edges
    )
    result = velocity_profile(positions, velocities, 4, 4, 0.5)
    np.testing.assert_allclose(result.upper_edges, expected_edges * 0.5)
    np.testing.assert_allclose(result.mean, expected_means, equal_nan=True)
    assert np.isnan(result.standard_deviation).all()
