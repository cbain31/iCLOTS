# Velocity compatibility policy

Phase 1 separates compatibility with recorded outputs from scientific behavior that should remain true across implementations.

## Exact regression behavior

The following behavior is protected at explicitly documented floating-point tolerances:

- reconstruction of metrics from the archived representative 19-bin profiles;
- conversion of pixel displacement per frame to micrometres per second by multiplication by FPS and micrometres/pixel;
- per-frame minimum, arithmetic mean, and maximum aggregation;
- evenly spaced profile edges from zero through channel height;
- default `numpy.digitize` membership: an interior edge belongs to the bin on its right, while the final upper edge is outside the reported bins;
- empty bins produce `NaN` means;
- profile coordinates are the upper edges (`edges[1:]`), matching the legacy output array convention.

## Scientific invariants

The following relationships are scientific requirements rather than dependencies on a particular GUI or OpenCV release:

- velocity scales linearly with FPS and micrometres/pixel;
- normalized range, sample coefficient of variation (`ddof=1`), wall/maximum ratio, center-to-wall contrast, normalized quadratic coefficient, and quadratic R-squared are invariant to uniform velocity scaling;
- ideal plug flow is spatially flat;
- an ideal center-fast parabolic profile has negative quadratic curvature and a faster center;
- axial and Euclidean displacement agree for horizontal motion and differ predictably for diagonal or vertical motion;
- for the archived representative pair only, sepsis has higher wall/maximum ratio and lower normalized range, profile CV, and normalized curvature magnitude than control.

These assertions do not support population-level diagnostic or clinical conclusions.

## Known legacy quirks

The checked-out KLT path detects features in the destination frame, passes swapped and halved GUI window dimensions to KLT, bins by destination y-position, uses unsigned two-dimensional displacement, and constructs a time vector with `linspace(0, n, n) / FPS`. Profiles report bin upper edges rather than centers.

Tests document the numerical bin/output conventions and unsigned Euclidean displacement. The OpenCV-specific choices are not exercised in the normal suite because exact historical dependencies and parameters were not preserved. Known quirks may be covered by explicit legacy-compatibility tests during later work, but they are not automatically permanent scientific requirements. Changing one requires a deliberate compatibility decision, a scientific validation test, and release documentation; it must not happen incidentally during refactoring.
