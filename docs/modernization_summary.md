# iCLOTS 2.0 modernization report — 2026-10-22

This report records implemented and executed work, not completion of all release
or scientific-validation gates. The starting checkout was clean at `8aed41d` on
`refine/phase3d-gui-hardening`; development uses
`codex/accelerated-modernization`. The original Tk application and historical
software-only snapshot were preserved. No source dataset was modified or added
to Git. No pull request has been merged.

## Delivered implementation

Review is split into stacked draft PRs: [ROI lifecycle #4](https://github.com/cbain31/iCLOTS/pull/4),
[accumulation #5](https://github.com/cbain31/iCLOTS/pull/5),
[video workflows #6](https://github.com/cbain31/iCLOTS/pull/6),
[static adhesion #7](https://github.com/cbain31/iCLOTS/pull/7),
[clustering #8](https://github.com/cbain31/iCLOTS/pull/8), and
[packaging/report #9](https://github.com/cbain31/iCLOTS/pull/9).
The first targets the pre-existing ROI-hardening branch; subsequent PRs target
the preceding milestone branch. None targets a direct modification of main.

The modern desktop expands from one working screen to eleven: ROI, device and
microchannel accumulation; velocity profiling; general single-cell tracking,
deformability and transient adhesion; brightfield and fluorescence static
adhesion; filopodia; and clustering. Fluorescence video tracking is deliberately
disabled pending SCI-001 review.

Scientific calculations live in `iclotspython/core`, with lazy static-adhesion
and clustering modules extending the earlier accumulation/velocity/tracking core.
The application layer owns validation, decoding, detection/linking orchestration,
progress and cancellation. Qt owns input controls, preview and presentation.
New immutable results provide named raw/summary tables, plots, parameters,
provenance and warnings. No legacy GUI adapter is imported by the modern GUI.

Shared exports produce table-specific CSV, multi-sheet XLSX, PNG and a JSON
reproducibility report. Manifests contain sizes, SHA-256 checksums and explicit
success/partial/failure records. Existing targets are preserved by default; failed
replacements preserve originals and clean temporary files. ROI retains its
established output schema, now with the release version in provenance.

Worker revisions prevent stale results after parameter/input changes. Old results
are cleared before reruns. Thread shutdown is cooperative and window closure is
deferred while a worker remains active. Optional dependencies produce structured
installation guidance. Static images can have independent dimensions; video
decoding streams in the worker. Explicit crop rectangles are supported on new
image/video workflows. A fallback font handles environments exposing no system
fonts; controls and table selection were adjusted after offscreen visual review.

Packaging now provides `pyproject.toml`, desktop/analysis/test/build extras, a
tested dependency recipe, source/wheel distributions, lazy `iclots` and
`python -m iclotspython` entrypoints, and `--check` environment diagnostics.
CI targets Windows/Ubuntu and Python 3.11/3.12. All four matrix jobs passed tests,
builds, environment checks and artifact uploads for code commit `8eb634e` in
[the PR validation run](https://github.com/cbain31/iCLOTS/actions/runs/39804378737).
No package was published.

## Executed validation

Environment: Windows, Anaconda Python 3.12.4; NumPy 1.26.4, PySide6 6.9.3,
OpenCV 4.10.0.84, TrackPy 0.7, pandas 2.2.2, scipy 1.13.1,
scikit-image 0.23.2, scikit-learn 1.4.2, matplotlib 3.8.4, openpyxl 3.1.2.
The first validation used an ignored project virtual environment that reuses
the existing system scientific libraries. A second, isolated virtual environment
with `include-system-site-packages=false` then installed the built wheel and
declared desktop/analysis/test extras successfully. Its 40-package inventory is
recorded in `testing/environments/windows-python312-clean.txt`. Scientific pins
were retained; the resolver selected matplotlib 3.11.2, openpyxl 3.1.5 and pytest
9.1.1. All eleven installed screens completed real worker/demo/export checks
outside the source checkout, and the clean environment passed **305 tests**.
This is a clean Python environment on the same Windows machine, not a fresh OS.

| Check | Executed evidence |
|---|---|
| Starting baseline | 237 passed, 2 opt-in tests deselected |
| ROI lifecycle | 7 targeted GUI tests passed, including stale-result and shutdown cases |
| Accumulation milestone | 252 ordinary tests passed; six local tests passed |
| Velocity and tracking milestone | 275 ordinary tests passed; two full local velocity videos and three complete tracking runs passed |
| Static adhesion | 16 targeted tests and three complete local image-group tests passed |
| Clustering | Nine targeted tests; three local workbook checks passed, including malformed multisheet rejection |
| Pre-packaging full suite | 299 passed, 17 deselected |
| Packaging | Wheel/sdist built, archive exclusions checked, installed wheel imported outside checkout, console version and eleven-screen window construction passed |
| Isolated installation | All declared extras resolved without system site packages; all eleven installed screens completed demo/worker/exports; 305 tests passed, 17 deselected |
| Cross-environment numerical probe | 980 numeric cells across velocity, general tracking, static fluorescence and final clustering differed by at most 1.11e-16; no tolerance failures |
| Final full suite | 305 passed, 17 deselected, with the local-data variable set to confirm opt-in isolation |
| Missing local data configuration | 17 skipped, 305 deselected |
| GitHub Actions | Windows and Ubuntu, Python 3.11 and 3.12: all four jobs passed tests, builds, diagnostics and artifact upload on 8eb634e |
| Combined configured local run | 17 passed, 303 deselected; all source-integrity snapshots unchanged |
| Visual checks | Two 1280×820 offscreen screenshots inspected; missing-font issue corrected and affected tests rerun |

Final command forms (PowerShell):

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:OMP_NUM_THREADS = "1"
.venv/Scripts/python -m pytest -q --basetemp=.pytest_cache/final-full-3
$env:ICLOTS_TEST_DATA_DIR = (Resolve-Path data/iCLOTS_test_data).Path
.venv/Scripts/python -m pytest -q -m local_data --basetemp=.pytest_cache/final-local
```

The opt-in policy is unchanged: ordinary runs never execute local-data tests,
even with the variable set. An absent configuration skips cleanly. Source names,
sizes and SHA-256 values are compared before/after local execution. Outputs use
temporary directories outside source datasets. The suite has no numeric coverage
percentage report; passing these tests does not imply every code path is covered.

Warnings observed are upstream openpyxl UTC deprecations, TrackPy invert
deprecation/black-mask notifications and, without `OMP_NUM_THREADS=1`, the
scikit-learn Windows/MKL thread-count warning.

## Scientific compatibility and intentional behavior differences

No existing numerical core formula or default was edited. Independent references
and production seams preserve strict thresholds, channel ordering, artificial
zero baselines, signed changes, squared calibration, unrestricted/nonfinite device
percentages, all-layer final-frame microchannel geometry, KLT destination-point
detection, swapped/halved windows, status filtering, legacy time vectors and
upper-edge profile bins. Tracking preserves exclusive maximum-ID omission,
unfiltered linked measurements and signed legacy policies.

OpenCV event results agree with an independently executed legacy loop within
1e-6 relative tolerance in the same installed library environment. New static
measurements agree with an independent transcription using original OpenCV and
regionprops_table operations at 1e-12 relative tolerance. Final clustering labels
and silhouette agree with the original KMeans constructor in the tested library.
These are same-environment compatibility checks, not recovery of the exact 2022
dependency environment.

A representative synthetic comparison between the original test environment
and the clean installation checked 980 numerical cells across velocity, general
tracking, static fluorescence adhesion and final clustering. Maximum absolute
difference was 1.1102230246251565e-16; every value passed 1e-6 relative / 1e-9
absolute tolerances. This observed floating-point drift is distinct from a
method change. The intentionally unseeded scree diagnostic was excluded. It is
a limited probe, not validation of all datasets or optional detection engines.

Intentional non-method changes: malformed inputs now produce structured failures;
empty detections return empty results/warnings rather than legacy GUI crashes;
the scree range is bounded by available rows rather than failing when fewer than
11 rows exist; source row IDs and excluded rows are retained explicitly. Final
clustering remains seeded at 100; the original unseeded diagnostic remains
nondeterministic and is identified as such. No scaling or new exclusion policy
was added. Reports record the actual estimator defaults and library versions.

The fluorescence video defect is reproduced, not corrected. Zero-intensity
division is rejected instead of replacing NaN/Inf or changing preprocessing.
Legacy filopodia row/column-center behavior and eccentricity labeled circularity
are retained with warnings. See the [issue register](testing/scientific_issue_register.md).

## Limits and remaining release gates

- Fluorescence video tracking needs collaborator-approved preprocessing and
  independent validation before activation. Exact historical detection/linking
  parity remains unresolved; local example parameters are operability settings.
- Labeled image/video exports, threshold-mask previews, visual ROI drawing,
  full clustering pairplots/mosaics, session persistence, batch projects and an
  application-wide work queue remain incomplete. Modern export organization
  differs from historical filenames/sheets; numerical tables and units are
  explicit, but complete legacy export parity is not claimed.
- Video editing/conversion utilities remain in the original Tk application.
  Normalization contains an indexing defect requiring separate review (SCI-002).
- Qt currently decodes the first TIFF page into uint8 RGB; high-bit-depth,
  multipage and codec-specific grayscale behavior need separate parity work.
  Large tracking recordings retain processed frames and may exhaust memory.
  Third-party fitting/linking calls limit immediate cancellation responsiveness.
- A wheel is installable, but no signed Windows installer, macOS application,
  Linux desktop bundle, notarization or auto-update has been produced. Fresh
  OS-level clean-machine desktop testing, macOS and interactive
  accessibility/high-DPI testing remain release gates.
- Phases 5–6 are proposals only in
  [future_workflows.md](architecture/future_workflows.md). No new scientific or
  clinical functionality was activated.

## Publication planning

The evidence supports describing an expanded interface, explicit scientific
compatibility contracts, independent numerical references, opt-in read-only
dataset integration, reproducibility metadata and practical Python packaging.
It does not support a claim of complete modernization, clinical validation,
universal legacy equivalence or validated biological settings for the examples.

For a publication-ready methods supplement, collaborators should choose annotated
datasets, freeze full environments, approve corrected policies separately,
prespecify numeric and feature-level tolerances, evaluate failure cases and
scaling, and document interactive usability/platform validation. Historical
archived velocity reproduction limits remain part of that scientific record.
