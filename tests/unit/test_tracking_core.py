"""Production tracking-core parity with independent Phase 1 references."""

from __future__ import annotations

import math

import pytest

from iclotspython.core.tracking import (
    LegacyTrackingPolicy,
    legacy_particle_ids,
    measure_legacy_tracks,
)
from tests.support import tracking_reference as reference


pytestmark = pytest.mark.unit


def _rows():
    return [
        {"particle": 0, "frame": 0, "x": 0, "y": 0, "mass": 255, "size": 2, "ecc": 0.2},
        {"particle": 0, "frame": 2, "x": 3, "y": 4, "mass": 765, "size": 4, "ecc": 0.4},
        {"particle": 1, "frame": 0, "x": 8, "y": 0, "mass": 255, "size": 1, "ecc": 0.1},
        {"particle": 1, "frame": 2, "x": 4, "y": 0, "mass": 255, "size": 1, "ecc": 0.3},
        {"particle": 2, "frame": 2, "x": 0, "y": 0, "mass": 255, "size": 1, "ecc": 0.1},
    ]


def test_legacy_selection_skips_highest_filtered_id_and_uses_unfiltered_rows():
    filtered = [_rows()[0], _rows()[2], _rows()[4]]
    assert legacy_particle_ids(filtered) == tuple(reference.legacy_particle_ids(filtered))
    result = measure_legacy_tracks(
        filtered,
        _rows(),
        fps=2,
        micrometres_per_pixel=0.5,
        policy=LegacyTrackingPolicy.GENERAL,
        threshold_pixels=9,
    )
    assert [item.source_particle for item in result] == [0, 1]
    assert result[0].distance_pixels == pytest.approx(
        reference.euclidean_endpoint_displacement(_rows()[:2])
    )
    assert result[0].area_pixels == pytest.approx(2)


def test_fluorescence_summary_matches_reference():
    result = measure_legacy_tracks(
        [_rows()[0], _rows()[4]],
        _rows(),
        fps=2,
        micrometres_per_pixel=0.5,
        policy=LegacyTrackingPolicy.FLUORESCENCE,
        threshold_pixels=9,
    )[0]
    expected = reference.fluorescence_area_and_intensity(_rows()[:2])
    assert result.area_pixels == pytest.approx(expected["area_pixels"])
    assert result.fluorescence == pytest.approx(expected["fluorescence"])


def test_signed_deformability_and_adhesion_policies_remain_distinct():
    filtered = [_rows()[0], _rows()[2], _rows()[4]]
    deformability = measure_legacy_tracks(
        filtered,
        _rows(),
        fps=2,
        micrometres_per_pixel=0.5,
        policy=LegacyTrackingPolicy.DEFORMABILITY,
        threshold_pixels=10,
    )
    assert [item.source_particle for item in deformability] == []
    adhesion = measure_legacy_tracks(
        filtered,
        _rows(),
        fps=2,
        micrometres_per_pixel=0.5,
        policy=LegacyTrackingPolicy.TRANSIENT_ADHESION,
        threshold_pixels=10,
    )
    assert [item.source_particle for item in adhesion] == [0, 1]
    assert adhesion[1].distance_pixels == -4
    assert adhesion[1].velocity_micrometres_per_second < 0
    expected = reference.adhesion_area_and_eccentricity(_rows()[:2], 0.5)
    assert adhesion[0].area_micrometres_squared == pytest.approx(
        expected["area_micrometres_squared"]
    )


def test_zero_duration_retains_nonfinite_velocity():
    rows = [
        {"particle": 0, "frame": 1, "x": 0, "y": 0, "mass": 255},
        {"particle": 0, "frame": 1, "x": 0, "y": 0, "mass": 255},
        {"particle": 1, "frame": 1, "x": 0, "y": 0, "mass": 255},
    ]
    result = measure_legacy_tracks(
        rows, rows, 2, 1, LegacyTrackingPolicy.GENERAL, -1
    )[0]
    assert math.isnan(result.velocity_micrometres_per_second)
