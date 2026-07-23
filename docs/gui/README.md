# Modern PySide6 interface

Phase 3C provides one restrained desktop shell and one functional ROI
accumulation workflow. It is a client of the Phase 3A application contracts
and Phase 3B output services; it is not a new scientific implementation.

## Install and launch

From the repository root, install the normal test dependencies and the
optional modern-desktop dependencies:

```powershell
python -m pip install -r requirements-test.txt
python -m pip install -r requirements-gui.txt
python -m iclotspython.gui
```

`requirements-gui.txt` is development dependency metadata, not Phase 4
packaging. PySide6 6.9 is pinned because 6.11.1 failed to load its native
QtCore DLL in the validated Windows 11 / Anaconda Python 3.12 environment.

## Shell and navigation

The application has one main window, a grouped workflow tree, a central
workspace, and a status bar. ROI Accumulation is enabled. Device and
microchannel accumulation, velocity, tracking, adhesion, clustering, and
utilities remain visible but disabled so the incremental migration path is
clear without presenting nonfunctional screens.

No `QApplication` or window is constructed at import time. The canonical
entrypoint creates one application instance and one main window.

## ROI accumulation workflow

The screen supports:

1. selecting multiple PNG, JPEG, BMP, TIFF images in explicit analysis order;
2. removing or clearing inputs and previewing the selected image;
3. loading a deterministic, clearly labeled synthetic demonstration;
4. selecting an explicit RGB or BGR convention;
5. selecting red, green, and blue channels independently;
6. setting strict per-channel thresholds, calibration, and frame interval;
7. running one background analysis, viewing progress, and requesting
   cooperative cancellation;
8. inspecting summary, immutable table data, plot-ready series, warnings, and
   provenance;
9. exporting selected PNG, CSV, and XLSX outputs through Phase 3B.

Loaded files must have equal dimensions. Qt normalizes supported images into
read-only RGB arrays. The screen converts them to the explicitly selected
convention before constructing `ROIAccumulationRequest`. It never passes file
paths as scientific inputs.

The synthetic demonstration contains three 64 × 48 RGB frames with a red
rectangle that grows and then shrinks. It exercises both positive and negative
signed accumulation and writes no files unless the user explicitly exports.
It is synthetic UI test data, not biological or research data.

## Threading and cancellation

`run_roi_accumulation` remains synchronous and GUI-independent. A small Qt
worker calls it on a `QThread`, forwards the existing `ProgressEvent` objects,
and exposes a thread-safe cancellation flag through the existing application
protocol. The screen disables overlapping runs. Cancellation is cooperative;
it does not terminate a thread or discard filesystem output midway.

## Results and exports

The result table binds to Phase 3A `TableData`. The embedded figure consumes
Phase 3A `PlotSeries`; it does not reuse a legacy plotting function. Export
buttons remain disabled until a current result exists.

The GUI constructs Phase 3B `PlotRequest` and `ExportRequest` objects. It
shows their `OutputManifest` records, including partial and failed outcomes.
No file is silently overwritten: the default is fail-if-present, and explicit
replacement requires user confirmation. Only selected output formats are
requested.

Changing input order, channel convention, channel selection, thresholds,
calibration, or timing invalidates the previous result and disables export.

## Testing

Run the GUI-specific headless suite:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -m gui
```

These tests need no raw microscopy data and create output only inside
automatically cleaned repository-local test directories.

## Visual review steps

1. Launch with `python -m iclotspython.gui`.
2. Select **ROI Accumulation** in the left navigation.
3. Click **Load synthetic demo**, then **Run analysis**.
4. Inspect the **Summary**, **Data table**, **Plot**, and
   **Warnings & provenance** tabs. The plot should show the red ROI growing
   and then shrinking.
5. Open **Export**, choose an empty destination directory, select the desired
   PNG/CSV/XLSX formats, and export. Review the returned manifest and the
   created files.
6. To review real-image handling, clear the inputs, click **Add images…**,
   select a same-size sequence in the desired order, confirm the displayed
   order, choose the explicit convention/channels/thresholds/calibration, and
   run.
7. Report the operating system, display scaling, input dimensions, exact
   action, and visible message with UI feedback. Do not include sensitive
   research data or personal information.

## Troubleshooting

- If Qt reports that no platform plugin can be initialized in a headless
  environment, set `$env:QT_QPA_PLATFORM = "offscreen"` before testing. Do
  not use offscreen mode for ordinary visual review.
- If `QtCore` reports a native DLL load failure, confirm that
  `python -m pip show PySide6` reports the tested 6.9 line and reinstall from
  `requirements-gui.txt`.
- If an image cannot be loaded, convert it to PNG, JPEG, BMP, or TIFF and
  confirm every frame has identical pixel dimensions.
- If export reports an existing target, choose a different directory or
  explicitly approve replacement. The application never silently overwrites.

## Current limitations

Phase 3C does not provide threshold-mask preview, drag-and-drop reordering,
project/session save and restore, batch analysis, application-wide job
management, accessibility review, installer integration, or migrated
workflows beyond ROI accumulation. Those are candidates for later approved
phases. The legacy Tkinter application and its behavior remain unchanged.
