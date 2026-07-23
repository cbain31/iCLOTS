import csv
from pathlib import Path

import pytest

from tests.support.velocity_reference import (
    axial_displacement,
    displacement_to_velocity,
    euclidean_displacement,
    profile_metrics,
)


pytestmark = pytest.mark.scientific
FIXTURE = Path(__file__).parents[1] / "fixtures" / "velocity" / "synthetic_profiles.csv"


def _synthetic_profiles():
    profiles = {}
    with FIXTURE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            profiles.setdefault(row["profile"], {"positions": [], "velocities": []})
            profiles[row["profile"]]["positions"].append(float(row["position"]))
            profiles[row["profile"]]["velocities"].append(float(row["velocity"]))
    return profiles


def test_uniform_plug_flow_is_flat():
    plug = _synthetic_profiles()["plug"]
    metrics = profile_metrics(plug["positions"], plug["velocities"])
    assert metrics["normalized_range"] == pytest.approx(0.0, abs=1e-14)
    assert metrics["profile_cv"] == pytest.approx(0.0, abs=1e-14)
    assert metrics["quadratic_coefficient_normalized"] == pytest.approx(0.0, abs=1e-14)


def test_parabolic_flow_is_center_fast_with_negative_curvature():
    parabola = _synthetic_profiles()["parabolic"]
    metrics = profile_metrics(parabola["positions"], parabola["velocities"])
    center = parabola["velocities"][parabola["positions"].index(0.0)]
    assert center > parabola["velocities"][0]
    assert center > parabola["velocities"][-1]
    assert metrics["quadratic_coefficient_raw"] < 0
    assert metrics["quadratic_r2"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("old", "new", "expected_euclidean", "expected_axial"),
    [
        ((0, 0), (4, 0), 4, 4),
        ((0, 0), (0, 4), 4, 0),
        ((0, 0), (3, 4), 5, 3),
    ],
    ids=["horizontal", "vertical", "diagonal"],
)
def test_displacement_definitions_on_known_motion(old, new, expected_euclidean, expected_axial):
    assert euclidean_displacement(old, new) == pytest.approx(expected_euclidean)
    assert axial_displacement(old, new) == pytest.approx(expected_axial)


def test_uniform_velocity_scaling_preserves_normalized_shape_metrics():
    parabola = _synthetic_profiles()["parabolic"]
    original = profile_metrics(parabola["positions"], parabola["velocities"])
    scaled_velocities = displacement_to_velocity(parabola["velocities"], fps=5, micrometres_per_pixel=2)
    scaled = profile_metrics(parabola["positions"], scaled_velocities)
    for metric in (
        "wall_to_max_ratio",
        "center_to_wall_contrast",
        "normalized_range",
        "profile_cv",
        "quadratic_coefficient_normalized",
        "quadratic_r2",
    ):
        assert scaled[metric] == pytest.approx(original[metric], abs=1e-12)
    assert scaled["quadratic_coefficient_raw"] == pytest.approx(
        10 * original["quadratic_coefficient_raw"]
    )

