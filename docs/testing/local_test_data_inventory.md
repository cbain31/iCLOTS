# Optional local iCLOTS test-data inventory

## Scope and handling policy

This inventory describes the original locally distributed dataset expected at
the directory named by `ICLOTS_TEST_DATA_DIR`. The directory must contain the
immediate folders listed below. It is ignored by Git and is not a repository
fixture.

The inventory was established from filenames and read-only metadata. Image
dimensions were read with Pillow, video metadata with OpenCV, and workbook
sheet names with openpyxl. No source file was renamed, copied, rewritten, or
used as an output destination.

Counts include `.DS_Store` files because they are present in the distribution.
“Modern support” means a workflow has an implemented Phase 3 application/GUI
path, not merely that Qt can decode its file format.

The 13 immediate folders contain 98 files. One additional root-level
`.DS_Store` makes the complete local distribution 99 files.

## Immediate-folder inventory

| Dataset folder | Likely workflow | Files and extensions | Dimensions and ordering | Outputs or parameters | Modern GUI support | Uncertainties |
|---|---|---|---|---|---|---|
| `Adhesion_brightfield_app` | Static brightfield adhesion image analysis | 3: 2 `.tif`, 1 `.DS_Store` | Both TIFFs are 1392×1040 grayscale. They appear to be independent collagen and fibrinogen specimens, not a time sequence. | No output or parameter file is present. | No. | Exact segmentation policy, calibration, thresholds, and expected measurements are not supplied. |
| `Adhesion_filopodia_app` | Filopodia/protrusion analysis of platelet images | 4: 3 `.tif`, 1 `.DS_Store` | All TIFFs are 512×512 RGB. Treat filenames as independent biological groups; no temporal ordering is encoded. | No output or parameter file is present. | No. | The intended protrusion parameters and validated outputs are unknown. |
| `Adhesion_fluorescence_app` | Static fluorescence adhesion analysis | 5: 4 `.png`, 1 `.DS_Store` | Three specimen images are approximately 3809–3810×3796–3802 RGB. `Parameter_test.png` is 437×429 RGB. Images appear independent rather than sequential. | No generated outputs are present. `Parameter_test.png` is an image despite its name, not an explicit parameter file. | No. | The role of `Parameter_test.png`, channel policy, thresholds, and expected results are not documented. |
| `Adhesion_video_app` | Transient/video adhesion tracking | 2: 1 `.avi`, 1 `.DS_Store` | `WBC_adhesion.avi` is 320×200, 399 frames, reported at 5 FPS. Video frames carry the chronological order. | No output or parameter file is present. | No. | Scientific frame rate, motion policy, calibration, and expected tracking results are not supplied. |
| `Machine_learning_artifical_data` | Artificial clustering/machine-learning input | 1 `.xlsx` | `Artifical_data.xlsx` contains a `Data` sheet. Workbook row order is the only apparent record order. | The workbook appears to be input data, not an application output. | No. | The distributed folder and filename use the spelling `artifical`; feature schema and expected clusters are not documented. |
| `Machine_learning_set1` | Clustering/machine-learning workbook set | 5: 4 `.xlsx`, 1 `.DS_Store` | Three workbooks contain `Data`; `Error_test.xlsx` contains `Data` and `Data2`. Workbooks appear to be separate groups rather than a sequence. | Input workbooks are present; no explicit generated outputs or standalone parameter file is present. | No. | `Error_test.xlsx` likely exercises invalid/multiple-sheet behavior, but the intended error is not stated. |
| `Machine_learning_set2` | Clustering comparison, likely Control versus SCD | 3: 2 `.xlsx`, 1 `.DS_Store` | `Control.xlsx` and `SCD.xlsx` each contain a `Data` sheet. Treat as independent group inputs. | Input workbooks are present; no output or parameter file is present. | No. | Feature meanings, preprocessing, and validated clustering results are unknown. |
| `Multiscale_accumulation_microfluidic-w-microchannels` | Device/microchannel accumulation | 21: 18 `.png`, 3 `.DS_Store` | Two separate nine-frame sequences: `SCD/combinedimg_0.png` through `_8.png` at 1792×1024, and `SCD_with_drug/..._0.png` through `_8.png` at 1791×1023. Order is the numeric suffix within each subgroup; the subgroups must not be merged. | No outputs or parameter files are present. | No for the intended device/microchannel workflow. A subgroup is decodable by the ROI loader, but that is not equivalent workflow support. | Calibration, channel meaning, thresholds, device geometry, and expected outputs are absent. The two subgroup dimensions differ by one pixel in each axis. |
| `Multiscale_accumulation_surface` | ROI/surface accumulation | 13: 10 `.tif`, 3 `.DS_Store` | Two separate five-frame sequences. `Healthy`: `1_T0001_00001_Overlay.tif` through `T0005`; `SCD`: `6_T0001_00001_Overlay.tif` through `T0005`. All report 960×720 RGB and two TIFF pages. Order is increasing `T` value within a subgroup. | No expected output or parameter file is present. | **Yes, for ROI operability validation.** This is the selected initial local dataset. | Qt currently loads the first decoded TIFF image. Intended use of the second TIFF page, channel convention, thresholds, calibration, interval, and expected legacy values are not supplied. Formal parity cannot be claimed. |
| `Single_cell_tracking_brightfield_app` | Brightfield single-cell tracking; one later result folder appears velocity-profile related | 18: 4 `.avi`, 4 `.xlsx`, 8 `.png`, 1 `.csv`, 1 `.DS_Store` | Original videos are 960×600 with 599 and 598 frames; paired shortened/resized videos are 480×300 with the same respective frame counts. All report 5 FPS. Each video is independently frame ordered. | Four timestamped result folders contain analysis workbooks. Earlier workbooks include `Velocity data`, `Trackpy details`, `Summary`, and `Parameters used`; the later workbook includes frame/profile/statistics/parameter sheets plus CSV and plots. | No. | Relationship between original and resized videos is inferred from names. The later velocity-style result folder may represent a separate workflow or later implementation. Reference status of all outputs is unverified. |
| `Single_cell_tracking_fluorescence_app` | Fluorescence single-cell tracking | 5: 1 `.avi`, 1 `.xlsx`, 2 `.png`, 1 `.DS_Store` | `cd71_reticulocytes.avi` is 960×600, 599 frames, reported at 5 FPS. Video frames carry chronological order. | A timestamped result folder contains an analysis workbook with `Velocity data`, `Trackpy details`, `Summary`, and `Parameters used`, plus graph and pairplot PNGs. | No. | The workbook is useful historical evidence, but it has not been established as an approved parity oracle. Fluorescence thresholds and calibration need review. |
| `Velocity_app` | Microfluidic velocity profiling | 11: 2 `.avi`, 2 `.csv`, 2 `.xlsx`, 4 `.png`, 1 `.DS_Store` | `healthy_velocity.avi` is 262×92; `sepsis_pt_velocity.avi` is 214×76. Both contain 401 frames and report 5 FPS. Each video is independently frame ordered. | Two timestamped healthy result folders contain all-data CSV, analysis XLSX with frame/profile/statistics/parameter sheets, and profile/timecourse PNGs. | No modern GUI screen. The headless velocity core exists. | No matching sepsis output is present. AVI playback FPS is not necessarily the scientific analysis rate. The two healthy output sets need provenance review before parity use. |
| `Video_editing_test` | Legacy video/image editing utilities | 7: 2 `.avi`, 3 `.jpg`, 1 `.tif`, 1 `.DS_Store` | `Image_1.tif` is 1392×1040 grayscale; JPEGs are approximately 3809–3811×3800–3803 RGB. `Video_1.avi` is 262×92×401 frames; `Video_2.avi` is 960×600×1523 frames; both report 5 FPS. Image order is the numeric filename suffix when a sequence is required. Videos are independent inputs. | No outputs or parameter files are present. | No. | Intended edit operations, crop/resize targets, codec expectations, and reference outputs are not supplied. |

## Selected ROI validation sequence

The first optional integration target is:

```text
Multiscale_accumulation_surface/
└── Healthy/
    ├── 1_T0001_00001_Overlay.tif
    ├── 1_T0002_00001_Overlay.tif
    ├── 1_T0003_00001_Overlay.tif
    ├── 1_T0004_00001_Overlay.tif
    └── 1_T0005_00001_Overlay.tif
```

Tests sort the explicit four-digit `T` field rather than relying on filesystem
enumeration. They validate loading, visible order, Phase 3A execution,
table/plot-ready presentation, Phase 3B PNG/CSV/XLSX exports, and the PySide6
ROI screen. Source-directory names and SHA-256 content are compared before
and after execution.

The test parameters—RGB, red channel, threshold 50, calibration 1.0, and
unit-spaced time values—are operational smoke-test inputs only. They are not
validated biological settings or legacy reference parameters. Consequently,
these tests establish integration and GUI operability, not formal scientific
or legacy-output parity.

## Running the optional tests

In Windows PowerShell, point the variable at the local distribution root:

```powershell
$env:ICLOTS_TEST_DATA_DIR = "<local path>"
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -m local_data
```

For the repository-local layout described here, `<local path>` is the
`iCLOTS_test_data` directory itself, not its parent `data` directory.

When the environment variable or selected dataset is absent, the explicitly
selected local tests skip cleanly. Ordinary `python -m pytest`, `-m unit`,
and `-m gui` runs deselect local-data tests unless `local_data` appears
explicitly in the marker expression.

All test outputs use automatically cleaned temporary directories outside the
source dataset. The tests never use the source dataset as an export
destination.
