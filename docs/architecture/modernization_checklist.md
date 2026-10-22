# Accelerated modernization assessment and checklist

Assessment: 2026-10-22, starting at `8aed41d` on
`refine/phase3d-gui-hardening`; implementation branch
`codex/accelerated-modernization`. The checkout was clean. No AGENTS.md or
additional instructions were present in the repository or parent directories.

## Evidence and current phase status

| Phase | Repository evidence | Status at assessment |
|---|---|---|
| 0 | Audit records, archived profile metrics, video reproduction report | Baseline recorded; exact historical feature reproduction unresolved |
| 1 | Independent numerical references, regression/scientific/unit suites | Foundation complete for accumulation, velocity and linked-track measurements; segmentation, detection/linking and clustering lack parity coverage |
| 2 | `iclotspython/core`, eight legacy adapters delegate numerical seams | Partial separation: detection/linking, image segmentation and clustering remain coupled to legacy orchestration |
| 3A–C | ROI request validation, presentation, output services, Qt shell | ROI only; all other modern navigation entries disabled |
| 3D | Existing GUI tests and opt-in local-data tests | Partial; worker state/shutdown, cropping and collaborator review remain |
| 3E | No other modern application services/screens | Incomplete |
| 4 | Two development requirements files; no package metadata/CI | Incomplete |
| 5–6 | No collaborator-approved new workflow or 3D/clinical specification | Proposal only; no production science authorized |

Baseline executed: `python -m pytest -q`: **237 passed, 2 deselected**.
Environment: Windows, Anaconda Python 3.12.4; Qt offscreen tests work.
`data/iCLOTS_test_data` is available but `ICLOTS_TEST_DATA_DIR` was unset.
TrackPy is not initially installed. The opt-in hook and `local_data`,
`integration`, `gui` markers must be retained. Dataset examples have incomplete
scientific parameter provenance: local operability is not historical parity.

The legacy `iCLOTS_softwareonly` tree is an immutable historical snapshot.
Existing scientific quirks are documented in the compatibility policies and
must remain explicit. Static adhesion, filopodia, clustering and video-editing
tools are still available through the original launcher; a numerical core alone
does not constitute a complete modern workflow.

## Dependency-ordered implementation plan

- [x] Audit history, architecture, tests, dataset configuration and baseline.
- [x] Harden ROI worker state and shutdown. Acceptance: parameter/input changes
  cannot publish stale results; closing a running window cannot destroy a live
  QThread; exercised cancellation/failure tests pass.
- [x] Add device and microchannel application/presentation/output/GUI paths.
  Acceptance: independent legacy-reference comparisons cover strict thresholds,
  all-layer geometry, non-finite device percentages, signed changes, calibration,
  raw column occupancy and by-frame aggregation; GUI, CSV/XLSX/PNG tests pass.
- [x] Add velocity application and GUI path. Acceptance: preserve destination
  detection, swapped/halved KLT windows, status selection, frame/time convention,
  upper-edge bins and sample SD; test real OpenCV orchestration and core parity.
- [ ] Add the four existing tracking policies (three enabled; fluorescence blocked
  by reproduced SCI-001). Acceptance: preserve preprocessing,
  TrackPy batch/link/filter parameters, exclusive particle enumeration and
  endpoint policies; test orchestration and scientific results independently.
- [x] Assess remaining static adhesion/filopodia/clustering/utility migration.
  Production activation requires implemented, independently tested workflows;
  ambiguous scientific behavior must be recorded without silent correction.
- [x] Package the modern application. Acceptance: wheel builds and installs,
  package imports/entrypoint work outside the repository; GUI remains optional
  for headless numerical use; source datasets/legacy snapshot excluded.
- [x] Execute full and configured opt-in tests, update user/developer docs,
  record validation matrix, scientific differences, limitations and phase 5–6
  proposals. Preserve read-only source-data integrity checks.
- [x] Commit focused milestones and open review PRs when authenticated platform
  access is available. Never merge without user approval.

## Validation and reporting policy

Each milestone records exact commands and observed counts below. New adapters
must call the existing core rather than copy its formulas. Ordinary tests use
synthetic inputs; local integration remains explicit and verifies source hashes.
Library/environment changes and unresolved legacy defects are recorded separately
from formula changes. No clinical validity or complete modernization is claimed
until the corresponding evidence exists.

## Milestone log

### M1 — ROI lifecycle

Added request-revision checks to discard stale worker results, cleared old
results before each run, and connected thread quit directly so cooperative
shutdown can finish while the GUI thread waits. Window close is deferred if a
worker does not stop within two seconds. Files: ROI screen, main window, GUI
workflow tests. Executed `python -m pytest tests/gui/test_gui_roi_workflow.py -q`:
**7 passed**. No scientific calculations changed. Next: accumulation migration.

### M2 — Multiscale accumulation

Added `application/common.py`, `application/multiscale.py`, immutable multi-table
presentation contracts, shared workflow output services and Qt screens. Device
and microchannel navigation is enabled. Explicit crop rectangles, all-color
geometry thresholds, raw column occupancy, frame means, geometry rows, plots,
CSV/XLSX and JSON reproducibility reports are supported. Writers preserve
existing files by default and use temporary sibling files for replacement.

Executed `python -m pytest -q --basetemp=.pytest_cache/m2-full`:
**252 passed, 6 deselected**. Executed with `ICLOTS_TEST_DATA_DIR` explicitly set,
`python -m pytest -q -m local_data --basetemp=.pytest_cache/m2-local`:
**6 passed, 252 deselected**, including both complete nine-frame subgroups and
both multiscale screens. Source name/size/SHA-256 snapshots were unchanged.
Openpyxl 3.1.2 emits upstream UTC deprecation warnings. No numerical core changes;
independent-reference comparisons preserve baseline, geometry, signed changes,
calibration and non-finite percentages. Local examples establish operability,
not historical parity. Labeled-image exports and interactive visual ROI drawing
remain future work (explicit crop coordinates work).

The sandbox's default pytest temporary-directory location is unwritable in some
runs; an ignored `.pytest_cache` basetemp was used. The initial sandboxed GitHub
CLI authentication check failed. A later network-enabled check succeeded;
the CLI created draft PRs after the connector's PR write was denied with HTTP 403.

### M3 — Velocity and video tracking

Added streaming `application/video_input.py`, velocity and tracking services,
video/track parameter screens, deterministic video demonstration, reference-loop
tests and local-video GUI tests. Seven modern workflows are now enabled.
The application services retain OpenCV/TrackPy detection/linking parameters and
delegate measurements to the existing core. TrackPy 0.7 was installed into an
ignored `.venv` with access to existing environment dependencies; the global
environment was not modified. Detection cancellation is checked between frames;
linking remains one synchronous third-party call.

Executed `.venv/Scripts/python -m pytest -q --basetemp=.pytest_cache/m3-full`:
**275 passed, 11 deselected**. Two complete 401-frame local velocity videos passed
GUI and export checks (**2 passed**). Complete representative general,
deformability and transient videos passed (**3 passed**, 53 seconds). All source
hashes were unchanged. These use explicit smoke-test parameters, not validated
biological calibrations or historical-oracle workbooks.

Independent OpenCV-loop events agree within 1e-6 relative tolerance in the same
library environment; no scientific core formulas changed. Empty detections now
produce explicit empty results and warnings, replacing legacy GUI crashes.
Fluorescence mask/intensity division was reproduced as producing NaN/Inf at zero
pixels; the modern service rejects that case and its navigation remains disabled.
See `docs/testing/scientific_issue_register.md` (SCI-001). Correction needs
collaborator methodology review. Labeled video export and historical
feature-level reproduction remain incomplete. Next: static analysis and packaging.

### M4 — Static adhesion and filopodia

Added a lazy, headless `core/adhesion.py`, static application service and three
screens. Independent specimen images may differ in dimensions; same-field
accumulation still requires equal dimensions. The static outputs retain strict
area bounds, texture population SD, conditional full functional-intensity sums,
TrackPy radius-derived area, eccentricity under the original circularity label,
and the legacy nonsquare filopodia coordinate convention. These conventions are
visible in result warnings. Image/combined density and descriptive tables are
exported with parameters and environment versions.

Executed the adhesion unit/GUI/shell tests: **16 passed**. Independent reference
uses original OpenCV thresholding and regionprops_table; production uses region
objects. Synthetic numerical comparisons pass at 1e-12 relative tolerance.
All three complete local adhesion image groups passed GUI and CSV/XLSX/PNG
export tests: **3 passed**; source snapshots were unchanged. Ten modern scientific
screens are enabled. Colored-image grayscale decoding may differ from legacy
codec-specific imread behavior, and TIFF page selection remains first-page only;
image-file-level historical parity is not asserted. Labeled images remain to
be migrated. Next: clustering, packaging and final validation.

### M5 — Clustering

Added a lazy core KMeans adapter, single-sheet workbook loader, explicit feature
selection, seeded final clustering, original unscaled/dropna policy, exclusion
audit, cluster statistics/counts, correlation and scree data and standard exports.
Estimator defaults are recorded rather than guessed from historical versions.
The unseeded legacy scree remains labeled nondeterministic. For fewer than 11
rows its range stops at the available row count instead of crashing. No final
cluster method, feature normalization or row exclusion definition was changed.

Targeted unit/GUI tests: **9 passed**. Local artificial and Control/SCD workbook
groups plus rejection of the distributed multisheet error workbook: **3 passed**;
source snapshots unchanged. Tests compare final labels/silhouette directly to
the checked-in KMeans constructor in scikit-learn 1.4.2. Local commands set
`OMP_NUM_THREADS=1` to avoid scikit-learn's Windows/MKL thread-count warning;
this is an execution setting, not an application parameter default. The modern
screen plots the first selected feature pair and exports correlations; exhaustive
pairplots and mosaic images remain unmigrated. Eleven scientific screens enabled.

### M6 — Packaging, usability, documentation and final review

Added installable 2.0.0a1 metadata, extras, dependency recipes, lazy CLI/version/
environment diagnostics, wheel/sdist build configuration and Windows/Ubuntu
CI configuration. Package archives exclude datasets and historical trees. Wheel
installation into the ignored venv, imports outside the checkout, console version
and construction of eleven screens passed. Initial checks reused system scientific
libraries. A subsequent isolated venv installed the wheel and all extras without
system site packages; all eleven installed screens completed demo/worker/exports,
and its ordinary suite passed **305 tests, 17 deselected**. The resolved 40-package
inventory is committed under `../testing/environments/`. A 980-numeric-cell
synthetic cross-environment probe had maximum absolute drift 1.11e-16 and zero
failures at 1e-6 relative / 1e-9 absolute tolerance; unseeded scree was excluded.

Visual review found no Qt system fonts in the restricted offscreen environment.
Added a conditional fallback to the existing Matplotlib DejaVu font and tested
it in a fresh process. Inspected readable 1280x820 accumulation/clustering images;
reflowed input buttons/table selection and fixed stale running-status feedback.
Clustering feature-pair plots now use scatter marks. ROI provenance records the
actual release version; its previous unversioned assertion was updated.

Final complete ordinary run, with the local-data environment variable also set:
`.venv/Scripts/python -m pytest -q --basetemp=.pytest_cache/final-full-3`:
**305 passed, 17 deselected**. Explicit local selection without the variable:
**17 skipped, 305 deselected**. Four packaging tests passed again after constraining
the analysis extra to the validated NumPy 1.26.4 binary runtime.
The configured combined local run passed **17 tests** (303 deselected), with
unchanged source hashes. This run preceded only font/layout/presentation repairs;
the ordinary GUI tests were rerun after those repairs. Missing-data behavior is
also checked explicitly. Upstream warnings and scientific limitations are in
`../modernization_summary.md`. SCI-002 now reproduces the unchanged legacy
normalization loop modifying row three rather than color planes.

Updated README, installation, GUI/test/developer guides, current phase references,
publication-planning summary and isolated Phase 5–6 proposals. No new assay or
clinical feature was added. Outstanding release gates are explicit, including
fluorescence methodology, legacy utilities, labeled exports and signed installers.

Review stack (all draft, none merged):

1. ROI lifecycle: https://github.com/cbain31/iCLOTS/pull/4
2. Accumulation: https://github.com/cbain31/iCLOTS/pull/5
3. Video workflows: https://github.com/cbain31/iCLOTS/pull/6
4. Static adhesion: https://github.com/cbain31/iCLOTS/pull/7
5. Clustering: https://github.com/cbain31/iCLOTS/pull/8
6. Packaging/documentation: https://github.com/cbain31/iCLOTS/pull/9

All six drafts were pushed and attached to the chat. GitHub Actions for code
commit `8eb634e` passed all four Windows/Ubuntu, Python 3.11/3.12 matrix jobs,
including tests, builds, diagnostics and artifact uploads:
https://github.com/cbain31/iCLOTS/actions/runs/39804378737 . The follow-up commit
only records review links, the deduplicated environment inventory and CI evidence;
it introduces no code changes. CI runner notices about deprecated action Node
runtimes remain upstream maintenance information; no job failed.
