"""Passing intended-reference specifications, not production-conformance tests.

The GUI-bound production modules are not imported. Each test describes behavior
expected after a future extraction and is intentionally named ``intended``.
"""

import csv
from pathlib import Path

import pytest

from tests.support.tracking_reference import (
    filter_tracks_by_observation_count,
    intended_general_distance_included,
    intended_particle_ids,
    intended_velocity,
    measure_tracks,
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


def test_intended_all_filtered_particle_ids_are_measured_including_highest():
    rows = _rows("highest_id")
    ids = intended_particle_ids(rows)
    assert ids == [0, 1, 2]
    assert len(measure_tracks(ids, rows, fps=10, micrometres_per_pixel=0.5)) == 3


def test_intended_noncontiguous_particle_ids_are_supported():
    rows = _rows("noncontiguous_ids")
    assert intended_particle_ids(rows) == [0, 2, 7]
    assert len(measure_tracks([0, 2, 7], rows, fps=10, micrometres_per_pixel=0.5)) == 3


def test_intended_measurement_uses_only_filtered_rows():
    filtered = _rows("filtered_extra", "filtered")
    result = measure_tracks([0], filtered, fps=10, micrometres_per_pixel=0.5)[0]
    assert result["start_frame"] == 1
    assert result["end_frame"] == 3


def test_intended_gui_distance_threshold_is_literal_and_inclusive():
    assert not intended_general_distance_included(8.9, 9)
    assert intended_general_distance_included(9, 9)
    assert intended_general_distance_included(9.1, 9)


def test_intended_empty_filtered_results_return_no_particle_ids():
    assert intended_particle_ids([]) == []


def test_intended_one_frame_track_is_rejected_by_three_observation_filter():
    assert filter_tracks_by_observation_count(_rows("one_frame_detection"), 3) == []


def test_intended_two_frame_stub_is_rejected_by_three_observation_filter():
    assert filter_tracks_by_observation_count(_rows("two_frame_stub"), 3) == []


def test_intended_zero_duration_division_is_prevented():
    with pytest.raises(ValueError, match="elapsed time must be positive"):
        intended_velocity(1, 0)

