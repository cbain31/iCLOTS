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
- [ ] Assess remaining static adhesion/filopodia/clustering/utility migration.
  Production activation requires implemented, independently tested workflows;
  ambiguous scientific behavior must be recorded without silent correction.
- [ ] Package the modern application. Acceptance: wheel builds and installs,
  package imports/entrypoint work outside the repository; GUI remains optional
  for headless numerical use; source datasets/legacy snapshot excluded.
- [ ] Execute full and configured opt-in tests, update user/developer docs,
  record validation matrix, scientific differences, limitations and phase 5–6
  proposals. Preserve read-only source-data integrity checks.
- [ ] Commit focused milestones and open review PRs when authenticated platform
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
runs; an ignored `.pytest_cache` basetemp was used. GitHub CLI authentication is
invalid, so remote PR creation is not currently available through that CLI.

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
