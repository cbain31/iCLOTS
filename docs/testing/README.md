# Phase 1 test foundation

## Phase 2 production-core coverage

Phase 2 adds direct tests in `test_accumulation_core.py`,
`test_velocity_core.py`, `test_tracking_core.py`, and `test_core_imports.py`.
They compare `iclotspython.core` with the independent Phase 1 references and
verify the package is headless. Legacy and intended references remain
specifications rather than production dependencies. Scientific tests continue
to check relationships and archived/synthetic fixtures. See
`docs/architecture/core_separation.md` for the adapter and duplicate-tree
boundaries.

## Phase 3A application-contract coverage

Phase 3A tests validate in-memory ROI request normalization, explicit RGB/BGR
ordering, structured errors and warnings, read-only defensive array copies,
core delegation, baseline/calibration parity, progress, cancellation,
provenance, table/plot/export-neutral helpers, deterministic execution, and
filesystem/dependency boundaries. Tests import neither GUI modules nor local
raw data. The original Phase 1 and Phase 2 suites remain unchanged in scope.

## Phase 3B output-service coverage

Phase 3B tests exercise deterministic ROI plot/export filenames, PNG
rendering, CSV and XLSX content, destination creation and rejection, default
no-overwrite behavior, explicit replacement, successful and partial
manifests, stop/continue failure policies, checksums, writer cleanup, and the
rule that only requested files survive. Fresh-process safeguards verify that
importing output contracts and services does not load Tkinter, PySide6,
matplotlib, pandas, openpyxl, OpenCV, or TrackPy. Plot and spreadsheet
dependencies are loaded only when their formats are executed.

## Phase 3C GUI coverage

Phase 3C tests live under `tests/gui/` and use Qt's offscreen platform without
requiring `pytest-qt` or a display server. They cover application-shell
construction, enabled and disabled navigation, deterministic demo input,
exact image-selection order, controlled dimension failures, request building,
validation feedback, production-service delegation, progress, cooperative
cancellation, overlap prevention, result replacement and invalidation,
table/plot presentation, Phase 3B export delegation, overwrite policy, and
success/partial/failure manifest display.

Fresh-process safeguards verify that importing `iclotspython.gui` constructs
no application or window and does not load PySide6. The application and core
packages remain Qt-independent. GUI source safeguards reject Tkinter, legacy
ROI adapters, direct core imports, and duplicated threshold/count operations.

Install the optional desktop dependencies before running GUI tests:

```powershell
python -m pip install -r requirements-gui.txt
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -m gui
```

The full Phase 3C development environment uses both `requirements-test.txt`
and `requirements-gui.txt`.

## Optional local-data integration coverage

The original distributed test-data folder remains ignored and is discovered
only through `ICLOTS_TEST_DATA_DIR`. The complete read-only inventory and
workflow mapping is in
[`local_test_data_inventory.md`](local_test_data_inventory.md).

Local tests carry both `local_data` and `integration`; the GUI smoke test also
carries `gui`. A repository collection hook deselects every `local_data` test
unless `local_data` is explicitly present in the marker expression. Therefore
ordinary `python -m pytest`, `-m unit`, and `-m gui` runs never execute these
tests, even when the dataset happens to exist locally.

Windows PowerShell:

```powershell
$env:ICLOTS_TEST_DATA_DIR = "<local path>"
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -m local_data
```

With no environment variable or an incomplete selected dataset, the explicit
local run skips cleanly. Configured tests hash source names, sizes, and
contents before and after execution. Phase 3B exports are written only to
automatically cleaned temporary output directories outside the dataset.
These tests establish operability, not formal legacy parity.

Phase 1 protects important numerical behavior before architectural refactoring. It is intentionally small: normal tests use committed arrays and CSV files, do not read `data/`, do not decode video, do not open historical workbooks, and do not import GUI-bound analysis modules.

## Test categories

- `tests/unit/` checks isolated displacement, conversion, aggregation, binning, metric, and repository behavior.
- `tests/regression/` checks representative archived control/sepsis profiles against Phase 0 values. These assertions concern one representative pair, not a population or clinical claim.
- `tests/scientific/` checks synthetic ground truth and scientific invariants that should survive implementation changes.
- `tests/fixtures/velocity/` contains compact numerical inputs and provenance only.
- `tests/support/` contains a clearly labeled pure reference implementation of the legacy numerical conventions. It is not a replacement for the GUI-bound KLT implementation.
- `tests/gui/` checks the optional PySide6 presentation client headlessly.
- `tests/integration/` contains opt-in tests spanning multiple modern layers.

Markers mirror these categories: `unit`, `regression`, `scientific`, `gui`,
`integration`, `local_data`, and reserved `slow`. Normal GUI tests also carry
the `unit` marker. No slow tests are currently included.

## Development environment

Phase 1 supports Python 3.11 and 3.12. Python 3.12 is the environment used to establish this suite. Test-only dependencies are NumPy and pytest, listed in `requirements-test.txt`.

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-test.txt
python -m pytest
```

On POSIX shells:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m pytest
```

The historical application targeted Python 3.7-era dependencies. This test environment does not attempt to recreate that stack: the supported Python policy and declared NumPy range exclude Python 3.7. Exact historical OpenCV feature selection and tracking therefore remain outside the normal suite.

## Phase 0 records used

The checkout stores its audit index at `docs/audit/README.md` (singular), despite earlier references to `docs/audits/`. Detailed tracked records are under `audit_outputs/velocity_validation/` and `audit_outputs/velocity_reproduction/`. Repository safeguards check these existing paths and do not rename or duplicate the audit archive.

Relevant Phase 0 conclusions are limited to the following test inputs:

- representative `control_500` and `sepsis_500` profiles contain 19 means associated with 20 bin edges;
- positions are stored as upper edges in micrometres and membership follows `numpy.digitize` with its default boundary behavior;
- archived velocities use 0.875 micrometres/pixel and an inferred analysis rate near 159.9 FPS, not the AVI playback metadata of 5 FPS;
- the representative workbooks match Figure 4C/4D source values at four-decimal publication precision;
- sepsis is flatter than control for the predefined representative-pair metrics;
- destination-frame detection, swapped/halved KLT windows, destination-y binning, the source time vector, and upper-edge reporting are known legacy conventions;
- exact historical feature-level reproduction remains unresolved and does not block numerical or scientific tests.

Raw AVI files, full XLSX workbooks, decoded frames, and other historical data remain local under ignored `data/` and are never required by this suite.
