import csv
from pathlib import Path

import pytest

from tests.support.tracking_reference import (
    absolute_x_endpoint_displacement,
    euclidean_endpoint_displacement,
    measure_track,
    signed_x_endpoint_displacement,
)


pytestmark = pytest.mark.scientific
FIXTURE = Path(__file__).parents[1] / "fixtures" / "tracking" / "trajectories.csv"


def _rows(fixture):
    with FIXTURE.open(newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row["fixture"] == fixture and row["table"] == "unfiltered"]


def test_particle_id_renumbering_does_not_change_physical_measurement():
    rows = _rows("valid_three")
    renumbered = [{**row, "particle": "42"} for row in rows]
    original = measure_track(rows, fps=10, micrometres_per_pixel=0.5)
    changed = measure_track(renumbered, fps=10, micrometres_per_pixel=0.5)
    for key in ("distance_pixels", "distance_micrometres", "elapsed_seconds", "velocity_micrometres_per_second"):
        assert changed[key] == pytest.approx(original[key])


def test_row_order_does_not_change_endpoint_measurement():
    rows = _rows("valid_three")
    ordered = measure_track(rows, fps=10, micrometres_per_pixel=0.5)
    reversed_rows = measure_track(list(reversed(rows)), fps=10, micrometres_per_pixel=0.5)
    assert reversed_rows["velocity_micrometres_per_second"] == pytest.approx(
        ordered["velocity_micrometres_per_second"]
    )


def test_doubling_calibration_doubles_distance_and_velocity():
    rows = _rows("horizontal")
    baseline = measure_track(rows, fps=10, micrometres_per_pixel=0.5)
    doubled = measure_track(rows, fps=10, micrometres_per_pixel=1.0)
    assert doubled["distance_micrometres"] == pytest.approx(2 * baseline["distance_micrometres"])
    assert doubled["velocity_micrometres_per_second"] == pytest.approx(
        2 * baseline["velocity_micrometres_per_second"]
    )


def test_doubling_fps_doubles_velocity():
    rows = _rows("horizontal")
    baseline = measure_track(rows, fps=10, micrometres_per_pixel=0.5)
    doubled = measure_track(rows, fps=20, micrometres_per_pixel=0.5)
    assert doubled["velocity_micrometres_per_second"] == pytest.approx(
        2 * baseline["velocity_micrometres_per_second"]
    )


def test_longer_duration_lowers_velocity_for_fixed_displacement():
    short = _rows("horizontal")
    long = [{**row, "frame": str(float(row["frame"]) * 2)} for row in short]
    short_result = measure_track(short, fps=10, micrometres_per_pixel=0.5)
    long_result = measure_track(long, fps=10, micrometres_per_pixel=0.5)
    assert long_result["velocity_micrometres_per_second"] == pytest.approx(
        short_result["velocity_micrometres_per_second"] / 2
    )


def test_horizontal_euclidean_and_absolute_axial_displacements_are_equal():
    rows = _rows("horizontal")
    assert euclidean_endpoint_displacement(rows) == pytest.approx(absolute_x_endpoint_displacement(rows))


def test_vertical_motion_has_zero_axial_and_nonzero_euclidean_displacement():
    rows = _rows("vertical")
    assert absolute_x_endpoint_displacement(rows) == pytest.approx(0)
    assert euclidean_endpoint_displacement(rows) == pytest.approx(4)


def test_diagonal_euclidean_displacement_exceeds_axial_displacement():
    rows = _rows("diagonal")
    assert euclidean_endpoint_displacement(rows) == pytest.approx(5)
    assert absolute_x_endpoint_displacement(rows) == pytest.approx(3)


def test_reverse_x_motion_retains_sign_in_signed_workflow():
    assert signed_x_endpoint_displacement(_rows("reverse_x")) == pytest.approx(-4)


def test_endpoint_velocity_ignores_intermediate_path_curvature_by_definition():
    straight = measure_track(_rows("straight_path"), fps=10, micrometres_per_pixel=0.5)
    curved = measure_track(_rows("curved_path"), fps=10, micrometres_per_pixel=0.5)
    assert curved["distance_pixels"] == pytest.approx(straight["distance_pixels"])
    assert curved["elapsed_seconds"] == pytest.approx(straight["elapsed_seconds"])
    assert curved["velocity_micrometres_per_second"] == pytest.approx(
        straight["velocity_micrometres_per_second"]
    )

