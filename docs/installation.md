# Installing the modernization preview

The modern application is **2.0.0a1**, a scientific compatibility preview.
It is separate from the original `python iCLOTS.py` Tk launcher and the historical
`iCLOTS_softwareonly` snapshot. It is not a signed standalone desktop release.

## Source installation

Use Python 3.11 or 3.12. Python 3.12.4 on Windows is the locally validated system;
the CI matrix also targets Python 3.11 and Ubuntu but has not been run locally.

PowerShell, from the checkout:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install ".[desktop,analysis,test]"
python -m iclotspython --check
python -m iclotspython
```

POSIX shells: activate with `. .venv/bin/activate`; the remaining Python commands
are the same. The installed console command `iclots` launches the application;
`iclots --check` prints versions without importing Qt or heavy analysis modules.
The previous `python -m iclotspython.gui` launch command still works.

For numerical APIs only, install `python -m pip install .`; this requires NumPy
and does not require Qt. `desktop` adds Qt and plot/spreadsheet outputs;
`analysis` adds OpenCV, TrackPy, scikit-image and scikit-learn for the other
scientific screens. Install **both extras** for the full modern application.
An unavailable optional dependency is reported when its workflow runs.

The scientific orchestration dependencies are pinned to the tested versions in
`requirements-analysis.txt` and `pyproject.toml`. Qt stays on 6.9 because 6.11.1
failed to load native QtCore in the earlier Windows/Anaconda environment.
`requirements-validated.txt` records the exact direct versions used locally; it
is a reproduction recipe, not a complete transitive lockfile. Capture
`python -m pip freeze` alongside result reports for environment archival.
The analysis extra constrains NumPy to 1.26.4 so a fresh resolver cannot combine
the older tested scientific binary wheels with an unvalidated NumPy 2 runtime.
An isolated Windows installation of the wheel with all extras passed the full
305-test suite. Its complete resolved dependency inventory is stored at
`docs/testing/environments/windows-python312-clean.txt`; use it as a constraints
snapshot when reproducing that run with the local wheel.

On Windows with MKL, launch clustering with `OMP_NUM_THREADS=1` to avoid the
upstream small-batch KMeans memory-leak warning:

```powershell
$env:OMP_NUM_THREADS = "1"
python -m iclotspython
```

## Building and checking distributions

```powershell
python -m pip install ".[build]"
python -m build
python -m pip install --no-deps dist/iclots-2.0.0a1-py3-none-any.whl
iclots --check
```

The wheel contains only `iclotspython` and distribution metadata. It excludes
source datasets, test fixtures, the original launcher/adapters and the historical
snapshot. The sdist additionally carries documentation and dependency recipes.
Keep the Git checkout when the legacy application is needed.

There is no modern PyInstaller executable, macOS app bundle, signing/notarization,
auto-updater or published package in this change. Those are separate release
engineering deliverables. Installing a wheel is supported; publishing an installer
requires platform testing and a release review.

## Tests

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:OMP_NUM_THREADS = "1"
python -m pytest -q
```

Opt-in local dataset tests retain their explicit environment variable and markers:

```powershell
$env:ICLOTS_TEST_DATA_DIR = "<local iCLOTS_test_data path>"
python -m pytest -q -m local_data
```

An unavailable dataset skips cleanly. Ordinary runs deselect these tests even when
the variable is set. In restricted environments with unwritable system temporary
directories, supply an unused directory under `.pytest_cache`, for example
`--basetemp=.pytest_cache/validation-run`. Do not point basetemp at scientific data.
