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

Phase 1 protects important numerical behavior before architectural refactoring. It is intentionally small: normal tests use committed arrays and CSV files, do not read `data/`, do not decode video, do not open historical workbooks, and do not import GUI-bound analysis modules.

## Test categories

- `tests/unit/` checks isolated displacement, conversion, aggregation, binning, metric, and repository behavior.
- `tests/regression/` checks representative archived control/sepsis profiles against Phase 0 values. These assertions concern one representative pair, not a population or clinical claim.
- `tests/scientific/` checks synthetic ground truth and scientific invariants that should survive implementation changes.
- `tests/fixtures/velocity/` contains compact numerical inputs and provenance only.
- `tests/support/` contains a clearly labeled pure reference implementation of the legacy numerical conventions. It is not a replacement for the GUI-bound KLT implementation.

Markers mirror these categories: `unit`, `regression`, `scientific`, and reserved `slow`. No slow tests are currently included. A future slow suite should be run explicitly and should not become part of normal development execution.

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
