# Scientific compatibility issues requiring separate review

No corrections below are silently enabled in the modern application.

## SCI-001 — Fluorescence tracking preprocessing

`analysis/sct_fluor.py` computes `foreground_mask / grayscale_frame` before
TrackPy detection. The GUI constructs the mask with MOG2 (shadows disabled)
and 5x5 morphological closing. Contrary to the adjacent comment, division is
not multiplication of the original intensity by a binary mask. At a zero
intensity pixel, `255/0` is Inf and `0/0` is NaN.

Reproduction is executable in
`tests/unit/test_tracking_workflow.py::test_legacy_fluorescence_division_reproduces_unresolved_defect`.
The modern service reproduces this operation and raises a structured scientific
failure for nonfinite input. The fluorescence navigation entry remains disabled
pending scientific review. Even finite division results are compatibility
evidence only; this workflow is not declared fully migrated or validated.

Proposed separately validated correction: collaborators confirm whether the
intended input is original intensity multiplied by the foreground mask, select
threshold/mass policies and compare tracked cells, area and fluorescence against
annotated representative data. This would be a named new policy, preserving
the legacy reference. No corrected policy has been implemented.

## Existing documented conventions

- Track enumeration excludes the last filtered particle ID and uses unfiltered
  trajectories. Empty legacy tables crash; modern services return explicit empty
  results with warnings. Missing enumerated particles produce structured errors.
- Transient adhesion accepts signed reverse motion. Deformability has strict
  one-third and full-width distance bounds.
- Device percentages use an unrestricted numerator and signal-derived map at
  threshold 10, allowing >100%, NaN and Inf.
- Microchannel geometry uses every layer of the final frame.
- KLT detects destination-frame features, swaps/halves window dimensions and
  reports a legacy linspace time vector, destination y and upper-edge bins.

These conventions remain in production compatibility paths. Earlier independent
intended-specification tests do not authorize changing their definitions.
