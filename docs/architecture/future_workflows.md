# Phase 5–6 proposals (no production science added)

## Phase 5: collaborator-defined workflow

The application layer now supports immutable requests/results, cancellation,
progress, named raw/summary tables, plot series, units, provenance and explicit
exports. A collaborator workflow can use those boundaries without importing Qt
into a scientific implementation. Do not add a plugin registry until an actual
second-party extension demonstrates the need.

Before implementation, obtain an agreed assay question, representative
non-sensitive inputs, measurement definitions and units, exclusions/defaults,
manually annotated expected results and uncertainty tolerances. Keep the first
prototype isolated from production navigation. Acceptance requires an independent
reference, sensitivity analysis, reproducible fixtures, parameter provenance and
collaborator review. Compare against relevant legacy policies where applicable.

An immediate collaborator decision is the intended fluorescence video
preprocessing in SCI-001. Validate a named corrected policy separately and retain
legacy evidence. Do not infer that passing operability tests validates that method.

## Phase 6: volumetric or clinical expansion

For volumetric work, introduce an explicit volume request with axis ordering,
voxel spacing per axis and physical units. Two-dimensional pixel calibration
cannot stand in for voxel calibration. Prototype volume measurement separately;
use synthetic solids and independently calculated volumes before representative
stacks. Specify overlap, connected-component connectivity, anisotropy and boundary
handling with collaborators. TIFF multipage decoding is not a validated 3D method.

For clinical research, first agree the intended use, cohort and data-governance
requirements. Keep identifying data outside Git, reports and test fixtures. Assess
patient-level split independence, reference annotations, site/device variation,
uncertainty and failure handling in a separate validation protocol. No diagnostic
claims, clinical thresholds or deployment readiness follow from this modernization.

Neither proposal is enabled in the application. No new scientific feature or
clinical workflow has been introduced by this change.
