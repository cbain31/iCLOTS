import csv
from pathlib import Path

import numpy as np
import pytest

from tests.support.velocity_reference import profile_metrics


pytestmark = pytest.mark.regression
FIXTURES = Path(__file__).parents[1] / "fixtures" / "velocity"
METRIC_TOLERANCE = 1e-10


def _profiles():
    result = {}
    with (FIXTURES / "archived_profiles.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            sample = row["sample"]
            result.setdefault(sample, {"positions": [], "velocities": []})
            result[sample]["positions"].append(float(row["upper_edge_um"]))
            result[sample]["velocities"].append(float(row["profile_velocity_um_per_s"]))
    return result


def _expected_metrics():
    with (FIXTURES / "expected_metrics.csv").open(newline="", encoding="utf-8") as handle:
        return {row["sample"]: row for row in csv.DictReader(handle)}


@pytest.mark.parametrize("sample", ["control_500", "sepsis_500"])
def test_representative_archived_profile_metrics_match_phase_0(sample):
    profile = _profiles()[sample]
    actual = profile_metrics(profile["positions"], profile["velocities"])
    expected = _expected_metrics()[sample]
    mapping = {
        "wall_to_max_ratio": "wall_to_max_ratio",
        "center_to_wall_contrast": "center_to_wall_contrast",
        "normalized_range": "normalized_range",
        "profile_cv": "profile_cv",
        "quadratic_coefficient_raw": "quadratic_coefficient_raw_per_um2",
        "quadratic_coefficient_normalized": "quadratic_coefficient_normalized_per_um2",
        "quadratic_r2": "quadratic_r2",
    }
    for actual_name, expected_name in mapping.items():
        assert actual[actual_name] == pytest.approx(
            float(expected[expected_name]), abs=METRIC_TOLERANCE, rel=0
        )


def test_representative_sepsis_profile_is_flatter_than_representative_control():
    profiles = _profiles()
    control = profile_metrics(**{
        "positions": profiles["control_500"]["positions"],
        "velocities": profiles["control_500"]["velocities"],
    })
    sepsis = profile_metrics(**{
        "positions": profiles["sepsis_500"]["positions"],
        "velocities": profiles["sepsis_500"]["velocities"],
    })
    assert sepsis["wall_to_max_ratio"] > control["wall_to_max_ratio"]
    assert sepsis["normalized_range"] < control["normalized_range"]
    assert sepsis["profile_cv"] < control["profile_cv"]
    assert abs(sepsis["quadratic_coefficient_normalized"]) < abs(
        control["quadratic_coefficient_normalized"]
    )


def test_archived_profiles_preserve_19_upper_edge_values_without_empty_bins():
    for profile in _profiles().values():
        assert len(profile["positions"]) == 19
        assert len(profile["velocities"]) == 19
        assert np.all(np.isfinite(profile["velocities"]))


def test_compact_archived_frame_summary_contains_only_documented_reference_rows():
    with (FIXTURES / "archived_frame_summary.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [(row["sample"], int(row["frame"])) for row in rows] == [
        ("control_500", 0),
        ("control_500", 1),
        ("control_500", 2),
        ("sepsis_500", 0),
        ("sepsis_500", 1),
        ("sepsis_500", 2),
    ]
    assert all(int(row["feature_count"]) <= 250 for row in rows)
    assert all(
        float(row["max_velocity_um_per_s"]) >= float(row["mean_velocity_um_per_s"])
        for row in rows
    )
