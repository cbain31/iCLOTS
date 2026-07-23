# Synthetic tracking fixture provenance

Every trajectory in this directory is synthetic. No human, animal, biological, clinical, or collaborator data are included. There are no source-video frames, filenames, timestamps, or identifiers.

`trajectories.csv` uses zero-based frame indices and pixel coordinates `(x, y)`. Unless a test states otherwise, calibration is `0.5 micrometres/pixel`, imaging rate is `10 FPS`, and the GUI minimum-distance example is `9 pixels`. `mass`, `size`, and `ecc` are transparent synthetic TrackPy-like columns used only to specify legacy summary formulas. `empty_trajectories.csv` is a header-only empty-table case.

Fixture purposes:

- `valid_three`, `two_frame_stub`, and `one_frame_detection` define observation-count filtering.
- `noncontiguous_ids` and `highest_id` expose label-selection behavior.
- `gap_memory_one` contains frames 0, 2, and 3: three observations with one missing frame, compatible with `memory=1` linking semantics.
- `horizontal`, `vertical`, `diagonal`, `reverse_x`, and `zero_displacement` define endpoint direction cases.
- `repeated_then_move`, `straight_path`, and `curved_path` specify endpoint-based measurement.
- `threshold_exact`, `threshold_below`, and `threshold_above` surround the literal 9-pixel intended threshold.
- `legacy_threshold_exact`, `legacy_threshold_below`, and `legacy_threshold_above` surround the current one-third threshold when the GUI value is 9 pixels.
- `single_frame_zero_time` specifies zero elapsed time.
- `filtered_extra` distinguishes measuring the filtered table from measuring a longer unfiltered table.
- `stub_leak` provides filtered IDs 0 and 2 while unfiltered ID 1 is a two-observation stub, exposing the legacy loop/table interaction.

Tests prefixed `legacy` represent checked-out source behavior. Tests prefixed `intended` represent GUI/help implications or controlled API behavior and do not assert production conformance. Scientific tests state calibration, timing, geometry, or label invariants.

