# iCLOTS historical velocity validation

## 1. Executive summary

The strongest direct comparison is `control_500` (`70um500s…croppedroi`) versus `sepsis_500`. Their archived frame-wise mean/maximum time courses reproduce main-manuscript Figure 4C source values at four-decimal publication precision, and their 19-bin profiles reproduce Figure 4D at the same precision. This directly confirms the archived workbooks as the numerical precursors of the representative Figure 4C/4D values, while not proving that every plotted PNG or video frame was used in final figure assembly.

Across every requested transparent shape metric, the representative sepsis profile is flatter: higher wall/max ratios and lower normalized range, profile CV, and normalized quadratic curvature. This is a descriptive comparison of one representative pair, not an inferential group conclusion.

Absolute velocity and shape remain separate. Archived velocities already match the publication source values, so the scaling factor needed for alignment is essentially 1.0. All four archives imply 0.875 μm/pixel, but the AVI files encode 5 FPS while workbook time steps imply approximately 159.9 FPS; encoded playback FPS was therefore not the analysis FPS.

Environment limitation: the bundled runtime lacked OpenCV/FFmpeg/video-decoding libraries and Matplotlib. AVI headers were parsed directly, calculations used NumPy, and figures were drawn with Pillow. XVID frame decoding/contact sheets were not attempted.

## 2. Data inventory

- Existing files inspected: 148 (4 AVI, 7 XLSX, 136 PNG, 1 `.DS_Store`).
- The four AVI files are XVID/AVI, internally consistent at 5 encoded FPS, and approximately 1,600 frames each.
- Prepared frame dimensions are: control 250 220×82; sepsis 250 174×78; control 500 224×82; sepsis 500 194×74.
- Width exceeds height for every video, supporting a horizontal channel/long axis. Control filenames explicitly record resizing by 0.5, rotation, and ROI cropping; sepsis filenames do not preserve preprocessing provenance.
- The 136 PNGs consist of annotated frames and saved result plots. Their dimensions/formats are catalogued in `data_inventory.csv`.
- All seven workbooks and all sheets are catalogued in `workbook_inventory.csv`. No formulas were found; they store values rather than live spreadsheet calculations.

## 3. Parameter reconstruction

No archived analysis workbook contains a dedicated parameter sheet. Parameters recoverable from the numerical outputs are:

| Parameter | Control 250 | Sepsis 250 | Control 500 | Sepsis 500 | Evidence |
|---|---:|---:|---:|---:|---|
| μm/pixel | 0.875000 | 0.875000 | 0.875000 | 0.875000 | Final bin edge divided by AVI height |
| Analysis FPS | 159.900374 | 159.900187 | 159.899812 | 159.900249 | Reciprocal median workbook time step |
| Encoded AVI FPS | 5 | 5 | 5 | 5 | AVI `avih` and `strh` headers |
| Profile values / edges | 19 / 20 | 19 / 20 | 19 / 20 | 19 / 20 | `Profile` and `Bins` sheets |
| Maximum observed features/frame | 250 | 237 | 250 | 250 | `all points`; ceiling strongly supports 250 max corners |

ROI x/y, block size, and KLT window dimensions are not recorded. Current GUI defaults are μm/pixel=1, FPS=1, 7 bins, 500 features, block=5, x-window=50, y-window=20. Current analysis hard-codes quality level 0.01, while help says 0.1. The full comparison is in `historical_parameters.csv`.

The stored profile convention contains 20 edges but 19 means. Reconstruction using `np.digitize`-equivalent intervals reproduces stored profile means to a maximum absolute difference of 5.68e-14 μm/s.

## 4. Candidate sample pairings

1. **Control 500 versus sepsis 500 — confirmed representative pairing.** Same condition label, same inferred calibration/FPS/profile structure, and direct rounded-value identity with Figure 4C/4D.
2. **Control 250 versus sepsis 250 — strongly supported secondary pairing.** Filename, parameters, duration, and profile structure align, but no exact main-manuscript Figure 4 source table was found for this pair.

No cross-condition pair was treated as a direct comparison.

## 5. Archived time-course findings

| Sample | Feature observations | Frames | Duration (s) | Mean reconstructed frame minimum (μm/s) | Mean of stored frame means (μm/s) | Mean of stored frame maxima (μm/s) | Overall feature mean ± SD (μm/s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Control 500 | 399,250 | 1,597 | 9.9812 | 365.8662 | 507.2346 | 605.1426 | 507.2346 ± 41.0571 |
| Sepsis 500 | 371,093 | 1,604 | 10.0250 | 340.4535 | 561.7388 | 701.1677 | 561.6802 ± 63.3894 |

Frame-wise minima are reconstructed from `all points` because the historical workbook stores frame-wise mean and maximum sheets but no frame-minimum sheet. Stored mean/max series were preserved rather than replaced by recalculation.

For this representative pair, sepsis has higher mean and maximum velocity. This is confirmed for the representative archived/source-data series, not established as an inferential population result.

## 6. Archived profile-shape findings

### Wall-to-maximum ratio

| Wall definition | Control | Sepsis | Flatter by this metric |
|---|---:|---:|---|
| outermost one bin each side | 0.880343 | 0.972542 | Sepsis |
| outermost two bins each side | 0.896412 | 0.974982 | Sepsis |
| outer 10% of represented profile width | 0.896412 | 0.974982 | Sepsis |

The outer-10% rule selects the same bins as the outermost-two rule for 19 evenly spaced represented positions; it is reported separately rather than treated as independent confirmation.

### Other shape metrics

| Metric | Control | Sepsis | Flatter profile |
|---|---:|---:|---|
| Center-to-wall contrast, outermost one | 0.119657 | 0.027458 | Sepsis (lower) |
| Normalized profile range | 0.124538 | 0.033722 | Sepsis (lower) |
| Profile coefficient of variation | 0.043622 | 0.008703 | Sepsis (lower) |
| Raw quadratic coefficient (μm/s per μm²) | -0.05553961 | -0.01359466 | Not scale-invariant |
| Normalized quadratic coefficient (per μm²) | -0.00010489 | -0.00002388 | Sepsis (closer to zero) |
| Quadratic R² / improvement over constant | 0.981132 | 0.834625 | Both curved, control has greater normalized curvature magnitude |
| Maximum absolute quadratic residual (μm/s) | 6.4144 | 3.9749 | Descriptive residual only |

The constant-model SSE equals total variation around the mean; quadratic improvement is therefore reported as R². Negative curvature denotes center-fast parabolicity. The normalized coefficient is the appropriate coefficient for shape comparison because the raw coefficient scales with absolute velocity.

**Evidence classification:** “the strongest sepsis profile is flatter than control” is **confirmed directly from archived data for the representative pair** and robust across the specified wall definitions. It is not a statistical group conclusion.

## 7. Comparison with publication source data

- Figure 4C: 1597 control and 1604 sepsis time points pair with the publication source. Maximum absolute archived/source difference across mean and max series is 5e-05 μm/s; values match when rounded to the publication’s four decimals.
- Figure 4D: all 19 control and 19 sepsis profile values match at four-decimal precision. Maximum absolute difference is 4.96524e-05 μm/s.
- Figure 4E contains 3 control/sepsis replicate pairs. Sepsis exceeds its paired control in 3/3 rows; mean source ratios are 0.745769 control and 0.758405 sepsis.
- No archived replicate identifiers or wall-definition calculation links Figure 4E rows to the representative videos. `Full_analysis` → Figure 4E is therefore unsupported with current provenance.

`publication_comparison.csv` contains every pairable time-course/profile point plus the unpaired Figure 4E rows.

## 8. Calibration assessment

All archived outputs imply 0.875 μm/pixel. The scaling factors required to align archived representative profiles to publication values are 0.999999986 control and 1.000000002 sepsis—effectively 1.0, with differences attributable to four-decimal publication rounding. Calibration uncertainty is therefore unnecessary to explain the archived-versus-source comparison.

A uniform change in μm/pixel scales all velocities and the raw quadratic coefficient linearly. Wall/max ratio, center/wall contrast, normalized range, profile CV, normalized profile, normalized quadratic coefficient, and quadratic R² are invariant to uniform velocity scaling. Position calibration does affect the coefficient’s per-μm² magnitude because it also rescales x.

The publication labels the profile from −35 to +35 μm. Archived final edges imply widths of 71.75 μm control and 64.75 μm sepsis, so the publication used a common conceptual 70-μm presentation while archived prepared-frame heights differ. This does not alter bin-order shape metrics but limits literal coordinate matching.

## 9. Limitations and missing provenance

- No historical parameter sheet records ROI coordinates, block size, KLT windows, quality level, or pyramid settings.
- `displacement` in archived raw sheets numerically behaves as already calibrated velocity; its header is ambiguous.
- `all points` and `Raw velocities` have matching row counts and sampled content, but only `all points` was used for calculations.
- No video decoder was available for XVID; orientation is supported by header dimensions, names, and existing annotated-frame dimensions, not newly decoded raw frames.
- AVI playback metadata (5 FPS) conflicts with manual analysis FPS (~159.9), but is internally consistent within each AVI.
- Control preparation steps are encoded in filenames; equivalent sepsis preparation provenance is absent.
- Figure 4E wall definitions and replicate/video identifiers are absent.
- This audit does not rerun KLT and does not test the current implementation choices against raw frames.

## 10. Recommended controlled reproduction experiment

1. Preserve these archived workbooks as reference fixtures.
2. Recover original uncropped acquisitions and exact historical parameters from maintainers/build records.
3. Decode each prepared AVI with a documented codec stack and confirm frame pixels/checksums.
4. Reproduce archived outputs first using the historical implementation/environment.
5. Run controlled synthetic translations with known x/y motion to isolate feature-frame and window-axis behavior.
6. Compare per-feature, per-frame, and bin-level outputs—not only plots.
7. Vary μm/pixel separately from shape parameters to demonstrate scaling invariance.
8. Pre-register wall definitions before comparing groups.
9. Use multiple independent control/sepsis experiments before inferential statistics.

## Evidence classification

| Conclusion | Classification | Basis |
|---|---|---|
| Strongest sepsis profile is flatter | Confirmed directly from archived data, representative pair only | All requested shape metrics agree |
| Sepsis has higher representative mean velocity | Confirmed directly from archived and publication data | Figure 4C paired series |
| Sepsis has higher representative maximum velocity | Confirmed directly from archived and publication data | Figure 4C paired series |
| Wall/max ratio is higher in sepsis | Confirmed for archived representative definitions; strongly supported at publication experiment level | All archived definitions; 3/3 source pairs higher |
| Absolute magnitude differences could result from calibration | Plausible generally, but unnecessary for archive/source alignment | Linear formula; alignment factor ≈1 |
| `Full_analysis` links to Figure 4C | Confirmed directly from archived/source values | All points match at publication precision |
| `Full_analysis` links to Figure 4D | Confirmed directly from archived/source values | All 19 bins match at publication precision |
| `Full_analysis` links to Figure 4E | Unsupported with current evidence | No replicate IDs or wall definitions |

## 11. Exact commands run

Commands were run from the repository root unless noted:

```text
Get-Content -Raw -Encoding UTF8 'C:\Users\cbain\.codex\attachments\6ed5a22a-e635-4884-8a33-b0441b046dd7\pasted-text.txt'
git --git-dir=.git --work-tree=. branch --show-current
git --git-dir=.git --work-tree=. status --short
git --git-dir=.git --work-tree=. ls-files -- data
git --git-dir=.git --work-tree=. ls-files -- audit_outputs
git --git-dir=.git --work-tree=. check-ignore -v data audit_outputs
rg --files 'data/Full_analysis' 'data/iCLOTS_source_data'
& 'C:\Users\cbain\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 'C:\Users\cbain\AppData\Local\Temp\iclots_velocity_validation.py'
```

The generation command was rerun after two audit-script corrections: one sparse publication-time row and one pixel-to-micrometre binning conversion. Read-only Python spot checks inspected headers, workbook rows, CSV row counts, UTF-8 text, and PNG dimensions. No package installation or application/KLT execution occurred.

## 12. Exact files read

- `analysis/velocity.py`
- `data/Full_analysis/.DS_Store`
- `data/Full_analysis/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi.avi`
- `data/Full_analysis/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi.avi`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_analysis.xlsx`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_0.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_1.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_10.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_11.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_12.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_13.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_14.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_15.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_16.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_17.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_18.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_19.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_2.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_20.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_21.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_22.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_23.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_24.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_25.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_26.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_27.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_28.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_29.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_3.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_4.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_5.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_6.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_7.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_8.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_frame_9.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_graph.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_profile_graph.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_profile_scatter_graph.png`
- `data/Full_analysis/Results/70um250s-01122022143907-0000_resized-0p5x_rotate_2_croppedroi_profile_scatter_graph_crop.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_analysis.xlsx`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_0.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_1.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_10.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_11.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_12.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_13.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_14.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_15.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_16.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_17.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_18.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_19.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_2.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_20.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_21.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_22.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_23.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_24.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_25.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_26.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_27.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_28.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_29.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_3.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_4.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_5.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_6.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_7.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_8.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_frame_9.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_graph.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_profile_graph.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_profile_scatter_graph.png`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_profile_scatter_graph_crop.png`
- `data/Full_analysis/Results/sepsis 250_analysis.xlsx`
- `data/Full_analysis/Results/sepsis 250_frame_0.png`
- `data/Full_analysis/Results/sepsis 250_frame_1.png`
- `data/Full_analysis/Results/sepsis 250_frame_10.png`
- `data/Full_analysis/Results/sepsis 250_frame_11.png`
- `data/Full_analysis/Results/sepsis 250_frame_12.png`
- `data/Full_analysis/Results/sepsis 250_frame_13.png`
- `data/Full_analysis/Results/sepsis 250_frame_14.png`
- `data/Full_analysis/Results/sepsis 250_frame_15.png`
- `data/Full_analysis/Results/sepsis 250_frame_16.png`
- `data/Full_analysis/Results/sepsis 250_frame_17.png`
- `data/Full_analysis/Results/sepsis 250_frame_18.png`
- `data/Full_analysis/Results/sepsis 250_frame_19.png`
- `data/Full_analysis/Results/sepsis 250_frame_2.png`
- `data/Full_analysis/Results/sepsis 250_frame_20.png`
- `data/Full_analysis/Results/sepsis 250_frame_21.png`
- `data/Full_analysis/Results/sepsis 250_frame_22.png`
- `data/Full_analysis/Results/sepsis 250_frame_23.png`
- `data/Full_analysis/Results/sepsis 250_frame_24.png`
- `data/Full_analysis/Results/sepsis 250_frame_25.png`
- `data/Full_analysis/Results/sepsis 250_frame_26.png`
- `data/Full_analysis/Results/sepsis 250_frame_27.png`
- `data/Full_analysis/Results/sepsis 250_frame_28.png`
- `data/Full_analysis/Results/sepsis 250_frame_29.png`
- `data/Full_analysis/Results/sepsis 250_frame_3.png`
- `data/Full_analysis/Results/sepsis 250_frame_4.png`
- `data/Full_analysis/Results/sepsis 250_frame_5.png`
- `data/Full_analysis/Results/sepsis 250_frame_6.png`
- `data/Full_analysis/Results/sepsis 250_frame_7.png`
- `data/Full_analysis/Results/sepsis 250_frame_8.png`
- `data/Full_analysis/Results/sepsis 250_frame_9.png`
- `data/Full_analysis/Results/sepsis 250_graph.png`
- `data/Full_analysis/Results/sepsis 250_profile_graph.png`
- `data/Full_analysis/Results/sepsis 250_profile_scatter_graph.png`
- `data/Full_analysis/Results/sepsis 250_profile_scatter_graph_crop.png`
- `data/Full_analysis/Results/sepsis 500_analysis.xlsx`
- `data/Full_analysis/Results/sepsis 500_frame_0.png`
- `data/Full_analysis/Results/sepsis 500_frame_1.png`
- `data/Full_analysis/Results/sepsis 500_frame_10.png`
- `data/Full_analysis/Results/sepsis 500_frame_11.png`
- `data/Full_analysis/Results/sepsis 500_frame_12.png`
- `data/Full_analysis/Results/sepsis 500_frame_13.png`
- `data/Full_analysis/Results/sepsis 500_frame_14.png`
- `data/Full_analysis/Results/sepsis 500_frame_15.png`
- `data/Full_analysis/Results/sepsis 500_frame_16.png`
- `data/Full_analysis/Results/sepsis 500_frame_17.png`
- `data/Full_analysis/Results/sepsis 500_frame_18.png`
- `data/Full_analysis/Results/sepsis 500_frame_19.png`
- `data/Full_analysis/Results/sepsis 500_frame_2.png`
- `data/Full_analysis/Results/sepsis 500_frame_20.png`
- `data/Full_analysis/Results/sepsis 500_frame_21.png`
- `data/Full_analysis/Results/sepsis 500_frame_22.png`
- `data/Full_analysis/Results/sepsis 500_frame_23.png`
- `data/Full_analysis/Results/sepsis 500_frame_24.png`
- `data/Full_analysis/Results/sepsis 500_frame_25.png`
- `data/Full_analysis/Results/sepsis 500_frame_26.png`
- `data/Full_analysis/Results/sepsis 500_frame_27.png`
- `data/Full_analysis/Results/sepsis 500_frame_28.png`
- `data/Full_analysis/Results/sepsis 500_frame_29.png`
- `data/Full_analysis/Results/sepsis 500_frame_3.png`
- `data/Full_analysis/Results/sepsis 500_frame_4.png`
- `data/Full_analysis/Results/sepsis 500_frame_5.png`
- `data/Full_analysis/Results/sepsis 500_frame_6.png`
- `data/Full_analysis/Results/sepsis 500_frame_7.png`
- `data/Full_analysis/Results/sepsis 500_frame_8.png`
- `data/Full_analysis/Results/sepsis 500_frame_9.png`
- `data/Full_analysis/Results/sepsis 500_graph.png`
- `data/Full_analysis/Results/sepsis 500_profile_graph.png`
- `data/Full_analysis/Results/sepsis 500_profile_scatter_graph.png`
- `data/Full_analysis/Results/sepsis 500_profile_scatter_graph_crop.png`
- `data/Full_analysis/Results/Summary.xlsx`
- `data/Full_analysis/sepsis 250.avi`
- `data/Full_analysis/sepsis 500.avi`
- `data/iCLOTS_source_data/iCLOTS_source_data_main_manuscript.xlsx`
- `data/iCLOTS_source_data/iCLOTS_source_data_supplement.xlsx`
- `gui/velocity.py`
- `help/velocityhelp.py`

## 13. Exact files created

- `audit_outputs/velocity_validation/data_inventory.csv`
- `audit_outputs/velocity_validation/workbook_inventory.csv`
- `audit_outputs/velocity_validation/archived_profile_metrics.csv`
- `audit_outputs/velocity_validation/historical_parameters.csv`
- `audit_outputs/velocity_validation/publication_comparison.csv`
- `audit_outputs/velocity_validation/candidate_sample_pairs.csv`
- `audit_outputs/velocity_validation/archived_profiles_raw.png`
- `audit_outputs/velocity_validation/archived_profiles_centered.png`
- `audit_outputs/velocity_validation/archived_profiles_normalized.png`
- `audit_outputs/velocity_validation/archived_timecourses.png`
- `audit_outputs/velocity_validation/shape_metric_comparison.png`
- `audit_outputs/velocity_validation/publication_comparison.png`
- `audit_outputs/velocity_validation/velocity_validation_report.md`

The temporary analysis script is outside the repository at `C:/Users/cbain/AppData/Local/Temp/iclots_velocity_validation.py` and is not a project artifact.

## 14. Modification confirmation

No existing source or data file was edited, renamed, moved, deleted, or overwritten. All repository outputs created by this audit are confined to `audit_outputs/velocity_validation/`.

## 15. Final repository state

- Branch: `audit/repository-baseline`
- Final `git status --short`:

  ```text
  ?? .gitignore
  ?? audit_outputs/
  ```

- `.gitignore` was pre-existing and was not modified by this audit.
- `data/` and `audit_outputs/` have no tracked files. `data/` remains ignored, untracked, and unmodified.
- All files created inside the repository are confined to `audit_outputs/velocity_validation/`.
