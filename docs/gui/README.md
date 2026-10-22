# Modern desktop workflow guide

The 2.0.0a1 compatibility preview has eleven enabled scientific screens in one
PySide6 window. Install with `python -m pip install ".[desktop,analysis]"` and
launch `python -m iclotspython` or `iclots`. The original Tk launcher remains
available from the checkout. See [installation](../installation.md).

## Workflows and inputs

| Screen | Inputs and parameters | Results |
|---|---|---|
| ROI Accumulation | Ordered equal-size images; explicit RGB/BGR, channel thresholds, calibration and interval | Artificial zero baseline, area, signed frame changes |
| Device Accumulation | Same-field images, channels, thresholds, calibration, optional explicit crop | Signal-derived device map count, area, unrestricted device percentage and signed changes |
| Microchannel Accumulation | Same-field images; all three thresholds define final-frame geometry | Geometry bands, individual channel measurements, raw per-column occupancy and frame means |
| Velocity Profiling | One video, acquisition FPS, calibration, bins, corners, block/window sizes, optional crop | Every accepted event, frame summaries, upper-edge profile with sample SD and descriptive statistics |
| Single-cell Tracking | One video, diameter, mass, search/distance criteria, FPS, calibration | Legacy-selected track measurements, linked details and statistics |
| Deformability | One video; width-derived search and strict distance bounds | Signed endpoint measurements under the existing deformability policy |
| Transient Adhesion | One video; mass interval, width-derived search, FPS and calibration | Existing signed transient measurements, including reverse motion |
| Brightfield Adhesion | Independent images, odd diameter, mass, invert and calibration | TrackPy detections, radius-based area, eccentricity and density |
| Fluorescence Adhesion | Independent images; primary/functional channels, strict thresholds/size bounds | Areas, eccentricity, texture, conditional functional intensity and density |
| Filopodia | Independent images; threshold/size bounds, Harris settings, channel and calibration | Legacy convex-image corner count and distance summaries |
| Clustering | One-sheet XLSX workbooks, two or more selected numeric features, cluster count | Seeded final labels, explicit missing-row exclusions, cluster statistics/counts, correlation and unseeded scree diagnostic |

Fluorescence **video tracking** is disabled pending scientific review of a
reproduced division-by-zero defect. Static fluorescence adhesion is available.
Video editing utilities remain in the original application.

## Input handling

Image selection preserves the supplied file order. Accumulation requires equal
sizes; static adhesion accepts differently sized independent specimens. Preview
the selected image and verify its filename and dimensions before analysis.
Remove or clear inputs to correct selection; reload in the intended order when
reordering is needed. Qt reads the first TIFF page and converts images to uint8
RGB; it does not currently expose multipage/high-bit-depth selection. Do not
infer file-level parity for such images without an explicit decoding comparison.

Optional crop controls use integer x/y/width/height in source pixels. Unchecked
means the full image/video; checked rectangles must be nonempty and inside every
input. Coordinates in results are crop-relative. Visual ROI drawing and mask
previews remain future work.

Videos show a first-frame preview and decode in the analysis worker. Acquisition
FPS defaults to the legacy value 1 and must be set from the experiment. Playback
FPS is not a substitute for the scientific acquisition rate. Tracking retains
processed grayscale/mask frames in memory; large recordings require substantial
memory. The synthetic demos are labeled artificial inputs, not specimen data.

## Execution and outputs

Run one analysis per screen, watch progress, or request cooperative cancellation.
Changing inputs or parameters invalidates old results; edits during a run discard
that run's stale result. Cancellation is checked between decode/detection steps;
third-party linking/fitting must return before it can complete. Window close is
deferred when a worker has not stopped safely. There is no application-wide queue.

Use Summary, Data table, Plot, Warnings & provenance and Export tabs. For migrated
workflows the table selector above the tabs chooses raw, summary or diagnostic
tables. ROI retains its established single-table presentation.

Choose an existing output directory and desired CSV, XLSX or PNG formats. New
workflow exports include a JSON reproducibility report with exact parameters,
source identifiers, scientific policy, versions, warnings and table schemas.
CSV writes each result table separately; XLSX contains those tables plus a
Reproducibility sheet. NaN/Inf remain explicit text in file outputs. Manifests
report per-file status, checksums, partial failures and errors. Existing files
require explicit replacement approval; failed replacements preserve originals.
ROI continues to use its established PNG/CSV/XLSX output contract.

The application does not yet export labeled images/videos, exhaustive clustering
pairplots/mosaics, saved sessions or batch projects. Legacy calculation adapters
and the historical software-only snapshot remain intact.

## Review and testing

Load a synthetic demo, run, inspect tables/plots/provenance, export to an empty
folder, then change a parameter and verify that export is disabled until rerun.
Headless tests exercise these paths on every enabled screen:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:OMP_NUM_THREADS = "1"
python -m pytest -m gui
```

Local examples remain opt-in through `ICLOTS_TEST_DATA_DIR` and `-m local_data`.
They establish operability and unchanged source hashes, not validated biological
parameters or exact historical parity. Review the
[validation summary](../modernization_summary.md) and
[scientific issue register](../testing/scientific_issue_register.md).
