# Phase 2 core separation

## Purpose and boundary

Phase 2 establishes one importable, headless production calculation package at
`iclotspython/core`. It separates tested scientific calculations from Tkinter,
OpenCV/TrackPy orchestration, plotting, pandas output assembly, dialogs, and
filesystem behavior. It intentionally does not begin Phase 3 interface work.

```text
Tkinter workflow
      |
legacy analysis adapter  -- image/video I/O, OpenCV/TrackPy, DataFrames,
      |                      plots, exports, dialogs, and GUI state
      v
iclotspython.core        -- explicit arrays/records/configuration only
      |
      v
immutable numerical results
```

The package imports without Tkinter, OpenCV, TrackPy, pandas, matplotlib, file
access, plotting, dialogs, or working-directory changes.

## Module responsibilities and APIs

- `models.py` defines immutable `AccumulationSeries`, `FrameSummary`,
  `ProfileResult`, `MicrochannelMeasurement`, and `TrackMeasurement` results.
- `accumulation.py` supplies strict thresholding, signal counting, calibrated
  area, legacy zero-baseline series, unrestricted legacy device percentages,
  full-series device-map construction, final-frame/all-layer horizontal
  microchannel geometry, column occupancy, and microchannel series results.
- `velocity.py` accepts already status-filtered source/destination KLT points
  and supplies 2-D displacement, scaling, destination-y output rows, frame
  summaries, the legacy time vector, profile edges, digitization, means, and
  sample standard deviations.
- `tracking.py` accepts already linked trajectory records and supplies named
  `LegacyTrackingPolicy` choices plus endpoint selection, calibration,
  duration, velocity, thresholding, area, fluorescence, and circularity
  summaries.

The core uses NumPy arrays, mappings, tuples, enums, and small dataclasses.
There is no generic workflow base class or plugin registry.

## Extracted workflows

The primary adapters for ROI accumulation, device accumulation, microchannel
accumulation, velocity profiles, general single-cell tracking, fluorescence
single-cell tracking, deformability, and transient adhesion delegate their
tested numerical seams to the core.

Adapters retain feature detection, optical flow, TrackPy detection/linking and
stub filtering, image reads and crops, labeled-image creation, GUI state,
DataFrame schemas, plots, spreadsheets, filenames, folders, dialogs, and
workflow order.

Still legacy-only and outside this phase are adhesion-image segmentation,
protrusion analysis, clustering, input dialogs, export/path redesign,
packaging, dependency modernization, and every untested workflow.

## Behavior-preservation policy

Extraction is compatibility work, not scientific correction. The production
legacy path explicitly preserves:

- strict `value > threshold` comparisons and BGR layer conventions;
- calibration squared for areas, artificial baselines, and signed changes;
- signal-derived device maps, unrestricted numerators, and non-finite
  zero-denominator percentages;
- final-frame/all-layer microchannel geometry, full-width row expansion,
  top-to-bottom bands, and zero-based ROI-relative columns;
- destination-frame KLT feature detection, frame order, `p0` interpretation,
  status filtering, swapped/halved windows, unsigned 2-D displacement,
  destination y coordinates, legacy time vectors, upper-edge bins, and
  final-edge/empty-bin behavior;
- exclusive `range(last filtered particle)` enumeration, measurement from
  unfiltered linked rows, strict one-third thresholds, signed deformability
  bounds, reverse transient-adhesion motion, and legacy non-finite velocity.

Future corrections must be introduced as separately named intended policies,
with owner-approved scientific expectations and new tests. They must not
silently replace the legacy-compatible path.

## Duplicate-tree policy

The primary tree is the modernization source of truth.
`iCLOTS_softwareonly` is an untouched historical packaging/release snapshot.
The shared core exists only once in the primary tree. Modified primary
adapters intentionally diverge; safeguards assert that they import the core
and that their historical copies do not. Existing byte-identity checks remain
for unaffected duplicate files elsewhere in the test suite.

## Testing strategy

The test suite maintains three independent layers:

1. production implementation under `iclotspython/core`;
2. Phase 1 legacy and intended references under `tests/support`;
3. scientific invariants and archived/synthetic fixtures.

`test_*_core.py` compares production results with independent references.
`test_core_imports.py` verifies the package boundary is headless. Existing
legacy, intended, scientific, archived-fixture, repository, and no-raw-data
safeguards remain in place.

## Decision log

- **Package location:** a top-level `iclotspython/core` package was chosen
  because no `src/` or modern package root existed and tests already execute
  from the repository root. This creates one unambiguous production package.
- **Result models:** small immutable family-specific dataclasses expose stable
  numerical boundaries without forcing unlike workflows into one model.
- **Adapter seam:** OpenCV KLT and TrackPy stay in adapters; accepted point
  pairs and linked primitive records cross into the core.
- **Source of truth:** the primary tree modernizes; the software-only copy is
  retained unchanged as historical evidence.
- **Corrections deferred:** all scientific corrections are deferred because
  Phase 2 acceptance requires parity with checked-out behavior. Intended
  references remain forward-looking specifications.
- **No parity deferrals:** all requested tested numerical seams were extracted;
  no workflow in the stated scope was deferred for lack of parity.

