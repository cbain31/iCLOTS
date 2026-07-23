# Velocity fixture provenance

These fixtures are compact, non-identifying numerical extracts and synthetic data created for Phase 1.

## Archived profiles and expected metrics

`archived_profiles.csv` and `expected_metrics.csv` come from the tracked Phase 0 report `audit_outputs/velocity_validation/velocity_validation_report.md` and its generated `archived_profile_metrics.csv`. The biological labels are representative `control_500` and `sepsis_500`; they identify experimental conditions, not people. Values are archived workbook profile means or metrics derived from those means.

Profile velocity units are micrometres/second. Edge units are micrometres. Each profile has 20 edges and 19 values. The stored coordinate is the upper edge of each bin, not its center. The original raw feature positions were binned using default `numpy.digitize` behavior. Profile CV uses sample standard deviation (`ddof=1`). Values are retained at the precision recorded by the audit. Derived metric tests use absolute tolerance `1e-10`; ordering assertions use no rounding.

## Archived frame summary

`archived_frame_summary.csv` contains only frames 0–2 for each representative condition, selected from the immutable reference columns of `audit_outputs/velocity_reproduction/frame_comparison.csv`. Counts, frame means, and frame maxima are archived values. It is a provenance/example fixture and is not a substitute for the full time course.

## Synthetic profiles

`synthetic_profiles.csv` is generated mathematical data: constant plug flow and the parabola `10 - position^2`. Positions are arbitrary spatial units and velocities are arbitrary consistent units. Synthetic invariant tests use floating-point tolerances appropriate to exact small arrays.

Raw videos, full historical workbooks, per-feature data, and generated image sequences remain outside Git under the ignored local `data/` tree. No personal identifier, filename containing a personal identifier, protected health information, or sensitive metadata is included here.
