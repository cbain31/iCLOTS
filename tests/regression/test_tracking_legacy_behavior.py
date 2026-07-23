import csv
import math
from pathlib import Path

import pytest

from tests.support.tracking_reference import (
    euclidean_endpoint_displacement,
    filter_tracks_by_observation_count,
    legacy_adhesion_distance_included,
    legacy_deformability_distance_included,
    legacy_general_distance_included,
    legacy_particle_ids,
    measure_track,
    measure_tracks,
    signed_x_endpoint_displacement,
)


pytestmark = pytest.mark.regression
FIXTURE = Path(__file__).parents[1] / "fixtures" / "tracking" / "trajectories.csv"


def _rows(fixture, table="unfiltered"):
    with FIXTURE.open(newline="", encoding="utf-8") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row["fixture"] == fixture and row["table"] == table
        ]


def test_legacy_general_tracking_omits_highest_particle_id():
    rows = _rows("highest_id")
    assert legacy_particle_ids(rows) == [0, 1]


def test_legacy_general_tracking_assumes_contiguous_particle_ids():
    rows = _rows("noncontiguous_ids")
    ids = legacy_particle_ids(rows)
    assert ids == list(range(7))
    with pytest.raises(IndexError, match="particle 1 has no rows"):
        measure_tracks(ids, rows, fps=10, micrometres_per_pixel=0.5)


def test_legacy_general_tracking_measures_stub_from_unfiltered_table():
    filtered = _rows("stub_leak", "filtered")
    unfiltered = _rows("stub_leak", "unfiltered")
    assert legacy_particle_ids(filtered) == [0, 1]
    measured = measure_tracks([1], unfiltered, fps=10, micrometres_per_pixel=0.5)
    assert measured[0]["distance_pixels"] == pytest.approx(4)


def test_legacy_general_tracking_uses_unfiltered_rows_for_retained_id():
    filtered = _rows("filtered_extra", "filtered")
    unfiltered = _rows("filtered_extra", "unfiltered")
    filtered_result = measure_track(filtered, fps=10, micrometres_per_pixel=0.5)
    legacy_result = measure_track(unfiltered, fps=10, micrometres_per_pixel=0.5)
    assert filtered_result["start_frame"] == 1
    assert legacy_result["start_frame"] == 0
    assert legacy_result["elapsed_seconds"] > filtered_result["elapsed_seconds"]


def test_legacy_empty_filtered_table_fails_on_last_row_lookup():
    with pytest.raises(IndexError, match="empty filtered table"):
        legacy_particle_ids([])


def test_legacy_general_tracking_applies_one_third_distance_threshold():
    assert legacy_general_distance_included(
        euclidean_endpoint_displacement(_rows("threshold_below")), 9
    )
    assert not legacy_general_distance_included(
        euclidean_endpoint_displacement(_rows("legacy_threshold_exact")), 9
    )


def test_legacy_general_tracking_uses_two_dimensional_displacement():
    assert euclidean_endpoint_displacement(_rows("vertical")) == pytest.approx(4)


def test_legacy_deformability_uses_strict_forward_signed_x_bounds():
    forward = signed_x_endpoint_displacement(_rows("horizontal"))
    reverse = signed_x_endpoint_displacement(_rows("reverse_x"))
    assert legacy_deformability_distance_included(forward, roi_width_pixels=10)
    assert not legacy_deformability_distance_included(reverse, roi_width_pixels=10)
    assert not legacy_deformability_distance_included(10 / 3, roi_width_pixels=10)
    assert not legacy_deformability_distance_included(10, roi_width_pixels=10)


def test_legacy_transient_adhesion_retains_reverse_signed_x_motion():
    reverse = signed_x_endpoint_displacement(_rows("reverse_x"))
    assert reverse == pytest.approx(-4)
    assert legacy_adhesion_distance_included(reverse, roi_width_pixels=10)


def test_legacy_current_stub_minima_are_three_and_ten_observations():
    three_frame = _rows("valid_three")
    two_frame = [{**row, "particle": "1"} for row in _rows("two_frame_stub")]
    assert len(filter_tracks_by_observation_count(three_frame + two_frame, 3)) == 3
    assert filter_tracks_by_observation_count(three_frame, 10) == []


def test_legacy_single_frame_zero_displacement_produces_nonfinite_velocity():
    result = measure_track(
        _rows("single_frame_zero_time"),
        fps=10,
        micrometres_per_pixel=0.5,
        zero_duration="legacy",
    )
    assert result["elapsed_seconds"] == 0
    assert math.isnan(result["velocity_micrometres_per_second"])
