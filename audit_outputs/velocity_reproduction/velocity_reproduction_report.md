# iCLOTS velocity reproduction audit

## 1. Executive summary

The checked-out legacy algorithm does **not** exactly reproduce the archived `control_500` and `sepsis_500` outputs under OpenCV 5.0.0. With the predefined joint-ranking policy, the best legacy parameter trial was `A08` ({'block_size': 5, 'gui_win_x': 50, 'gui_win_y': 20, 'quality': 0.01, 'max_corners': 500}); its classifications were **partial numerical reproduction** for control and **partial numerical reproduction** for sepsis. Numerical agreement, rather than the expected biological direction, determined this selection.

The prepared videos decode completely and already represent the cropped analysis ROI. The representative biological comparison remains descriptive: variant-specific preservation is listed in section 12.

## 2. Environment and decoder setup

An isolated temporary environment was created at `C:\Users\cbain\AppData\Local\Temp\iclots_velocity_reproduction_env` with system-site access to the bundled scientific stack. Missing OpenCV and Matplotlib were reported before installation. Exact versions are recorded in `environment_manifest.txt`. OpenCV's bundled FFmpeg backend decodes XVID; no standalone FFmpeg executable was installed.

## 3. Video integrity and preprocessing assessment

| Sample | SHA-256 | Size | Frames | Encoded FPS | Duration | Codec | Decode |
|---|---|---:|---:|---:|---:|---|---|
| control | `40f1bb0b9d912b99e6c1d0363056b6adf713a4da48ccf8bd72f2ee21d5c91304` | 224×82 | 1598 | 5.000 | 319.600 s | XVID/AVI; OpenCV reports FMP4 | complete |
| sepsis | `e1cb872f5c16454550a8ea43668634ba5904d9ad365e727336bbc96d9d21aba5` | 194×74 | 1605 | 5.000 | 321.000 s | XVID/AVI; OpenCV reports FMP4 | complete |

Both channels are horizontal. Video heights equal the archived analyzed profile heights implied by the 0.875 μm/pixel calibration; filenames and dimensions support that these are prepared/cropped ROI videos rather than original full fields. The AVI byte stream records `XVID`; OpenCV's FFmpeg backend normalizes the reported decoder FOURCC to `FMP4`, so both identifiers are retained in `video_metadata.csv`.

## 4. Archived reference definition

The workbooks were opened read-only. `all points` maps channel position/frame/displacement; `Mean velocity by frame` and `Max velocity by frame` supply immutable frame targets; `Profile` and `Bins` supply 19 means and 20 upper-edge coordinates. `Raw velocities` duplicates the per-feature row count. No profile-standard-deviation worksheet exists, so bin SDs were reconstructed once from `all points` without altering the archive. Full mappings and arrays are in `reference_summary.csv`.

## 5. Legacy-source reconstruction

The standalone script reproduces: frame read/crop/grayscale (source lines 79–99); destination-frame Shi–Tomasi detection and parameters (43–56, 101–105); legacy swapped/halved KLT window, pyramid, and termination (58–69); status filtering and `p0` interpretation (105–112); 2-D unsigned displacement/FPS/calibration (114–117); destination y-position (119–122); frame grouping (151–162); and `np.linspace`/`np.digitize` profile behavior including empty means (164–178). It does not import Tkinter.

## 6. Parameter-search procedure

The grid was declared before full execution and is recorded exhaustively in `parameter_trials.csv`. Parameters were identical for control and sepsis. Joint ranking was lexicographic: profile RMSE, frame-mean RMSE, frame-maximum RMSE, then count MAE.

1. A08: joint profile RMSE 9.3698, frame-mean RMSE 7.9423, frame-max RMSE 27.0488, count MAE 195.8425
2. A02: joint profile RMSE 10.0877, frame-mean RMSE 9.9174, frame-max RMSE 27.5839, count MAE 9.3226
3. A01: joint profile RMSE 10.8401, frame-mean RMSE 10.0476, frame-max RMSE 24.3638, count MAE 9.3226
4. A07: joint profile RMSE 10.8405, frame-mean RMSE 10.0485, frame-max RMSE 24.4019, count MAE 9.3008
5. A03: joint profile RMSE 11.7295, frame-mean RMSE 10.5013, frame-max RMSE 27.3752, count MAE 8.9988
6. A05: joint profile RMSE 348.2130, frame-mean RMSE 347.7198, frame-max RMSE 378.3932, count MAE 9.3226
7. A04: joint profile RMSE 348.7587, frame-mean RMSE 348.3924, frame-max RMSE 378.4492, count MAE 9.3226
8. A06: joint profile RMSE 349.0032, frame-mean RMSE 348.7690, frame-max RMSE 378.1665, count MAE 8.9988

## 7. Reproduction accuracy

| Sample | Legacy class | Profile RMSE | Frame-mean RMSE | Frame-max RMSE | Count MAE | Profile r |
|---|---|---:|---:|---:|---:|---:|
| Control | partial numerical reproduction | 5.5862 | 3.0715 | 30.8221 | 245.9524 | 0.9860 |
| Sepsis | partial numerical reproduction | 13.1534 | 12.8132 | 23.2754 | 145.7325 | 0.9127 |

Thresholds were predefined: exact = all three velocity RMSEs ≤1e-6 μm/s and exact counts; near-exact = velocity RMSEs ≤1% of reproduced mean and count MAE ≤1; partial = all velocity RMSEs ≤10% and profile correlation ≥0.8; trend-only = numerical thresholds fail but all six representative directions hold; failed = neither.

## 8. Variant comparisons

Variants A–E implement the requested definitions. F and G isolate swap and halving. All fixed variants share `A08` parameters. `variant_metrics.csv`, `frame_comparison.csv`, and `profile_comparison.csv` contain the full metrics and rows.

## 9. Effect of each source-code implementation choice

- **Destination versus source-frame detection** (A_legacy → B_conventional_frames): control: Δ profile RMSE +0.036, Δ mean RMSE +0.453, Δ wall/max +0.00159; sepsis: Δ profile RMSE +0.141, Δ mean RMSE +0.419, Δ wall/max +0.00112.
- **Window swapping at half-size** (B_conventional_frames → F_half_no_swap): control: Δ profile RMSE +11.459, Δ mean RMSE +2.728, Δ wall/max -0.07067; sepsis: Δ profile RMSE +102.531, Δ mean RMSE +102.354, Δ wall/max -0.09287.
- **Window halving with swapped axes** (B_conventional_frames → G_swap_no_half): control: Δ profile RMSE +289.233, Δ mean RMSE +290.790, Δ wall/max +0.12699; sepsis: Δ profile RMSE +389.243, Δ mean RMSE +389.472, Δ wall/max +0.01826.
- **Legacy versus direct windows** (B_conventional_frames → C_direct_windows): control: Δ profile RMSE +5.621, Δ mean RMSE +2.219, Δ wall/max -0.03038; sepsis: Δ profile RMSE -6.115, Δ mean RMSE -5.548, Δ wall/max +0.01733.
- **2-D versus absolute-x displacement** (C_direct_windows → D_axial): control: Δ profile RMSE -0.034, Δ mean RMSE -0.098, Δ wall/max -0.00002; sepsis: Δ profile RMSE -0.250, Δ mean RMSE -0.248, Δ wall/max -0.00017.
- **Destination versus source y-position** (D_axial → E_minimal_conventional): control: Δ profile RMSE -0.015, Δ mean RMSE +0.000, Δ wall/max +0.00003; sepsis: Δ profile RMSE -0.007, Δ mean RMSE +0.000, Δ wall/max +0.00020.

Historical time vector: archived workbooks use frame/FPS, while checked-out source line 157 uses `linspace(0, n, n)/FPS`, ending one frame interval later. This changes time coordinates but not velocities or profiles. Upper-edge versus center reporting shifts only x coordinates by half a bin; it does not change bin membership, velocity, or shape metrics.

## 10. Synthetic validation

Deterministic textured frame pairs tested +x, −x, y, diagonal, plug, parabolic-by-y, and near-window-limit displacement. Results are in `synthetic_results.csv`. Axial variants intentionally return near-zero velocity for pure-y motion; 2-D variants return its magnitude. Plug and parabolic targets test profile recovery without smoothing.

## 11. Calibration and FPS sensitivity

Sensitivity tests used ±5% around 0.875 μm/pixel and each sample's reconstructed FPS, plus encoded 5 FPS as a negative control. Absolute velocities scale linearly. Wall/max, normalized range, profile CV, normalized curvature, and quadratic R² remain invariant to uniform velocity scaling (within floating-point error). Calibration/FPS cannot reconcile nonuniform frame/profile residuals.

## 12. Biological-trend preservation

Each line reports six predefined descriptive directions for the representative pair:

- A_legacy: higher_sepsis_frame_mean=True, higher_sepsis_frame_max=True, higher_sepsis_wall_max=True, lower_sepsis_normalized_range=True, lower_sepsis_profile_cv=True, lower_sepsis_curvature_magnitude=True
- B_conventional_frames: higher_sepsis_frame_mean=True, higher_sepsis_frame_max=True, higher_sepsis_wall_max=True, lower_sepsis_normalized_range=True, lower_sepsis_profile_cv=True, lower_sepsis_curvature_magnitude=True
- C_direct_windows: higher_sepsis_frame_mean=True, higher_sepsis_frame_max=True, higher_sepsis_wall_max=True, lower_sepsis_normalized_range=True, lower_sepsis_profile_cv=True, lower_sepsis_curvature_magnitude=True
- D_axial: higher_sepsis_frame_mean=True, higher_sepsis_frame_max=True, higher_sepsis_wall_max=True, lower_sepsis_normalized_range=True, lower_sepsis_profile_cv=True, lower_sepsis_curvature_magnitude=True
- E_minimal_conventional: higher_sepsis_frame_mean=True, higher_sepsis_frame_max=True, higher_sepsis_wall_max=True, lower_sepsis_normalized_range=True, lower_sepsis_profile_cv=True, lower_sepsis_curvature_magnitude=True
- F_half_no_swap: higher_sepsis_frame_mean=True, higher_sepsis_frame_max=True, higher_sepsis_wall_max=True, lower_sepsis_normalized_range=True, lower_sepsis_profile_cv=True, lower_sepsis_curvature_magnitude=True
- G_swap_no_half: higher_sepsis_frame_mean=False, higher_sepsis_frame_max=False, higher_sepsis_wall_max=False, lower_sepsis_normalized_range=False, lower_sepsis_profile_cv=False, lower_sepsis_curvature_magnitude=False

No inferential or clinical conclusion is made from this single pair.

## 13. Evidence classification

| Statement | Classification | Basis |
|---|---|---|
| Current legacy source reproduces archives | contradicted if exact is claimed; actual class shown in section 7 | direct controlled execution |
| Unique historical parameter set recoverable | unresolved | bounded grid and dependency mismatch |
| Destination-frame detection materially changes real-data summaries | contradicted at the 5% materiality threshold; small measurable changes remain | A/B profile-RMSE deltas 0.036–0.141 μm/s and wall/max deltas 0.0011–0.0016; synthetic recovery is materially worse for the legacy convention |
| Swapped/halved windows materially change results | confirmed directly | B/F/G/C paired runs include changes exceeding 100 μm/s for sepsis and reversal under G |
| 2-D displacement materially changes real-data profile shape | contradicted at the 5% materiality threshold | C/D profile-RMSE changes ≤0.250 μm/s; synthetic pure-y/diagonal cases confirm the expected definitional effect |
| Source/destination y-coordinate materially changes results | contradicted at the 5% materiality threshold | D/E profile-RMSE changes ≤0.015 μm/s and wall/max changes ≤0.00020 |
| Sepsis/control trend survives all tested variants | contradicted | all six directions survive A–F but reverse under G; they survive all required A–E variants |
| Exact reproduction requires historical dependencies | plausible, not proven | current OpenCV mismatch and absent environment lockfile |

## 14. Remaining uncertainty

The historical OpenCV/NumPy versions, exact GUI selections, and export implementation are not recorded. The archived workbook layout differs from the checked-out exporter. OpenCV 5.0.0 may produce different corner/KLT results than the historical binary. The bounded grid cannot establish uniqueness outside tested values.

## 15. Recommended next step

Recover the historical executable/environment or maintainer parameter record, then rerun the same immutable comparisons. If unavailable, preserve this audit as a dependency-pinned baseline before modifying production code; evaluate changes on synthetic ground truth and multiple independent experiments, not solely on this pair.

## 16. Exact commands run

```text
git --git-dir=.git --work-tree=. branch --show-current
git --git-dir=.git --work-tree=. status --short
& 'C:/Users/cbain/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m venv --system-site-packages 'C:/Users/cbain/AppData/Local/Temp/iclots_velocity_reproduction_env'
& 'C:/Users/cbain/AppData/Local/Temp/iclots_velocity_reproduction_env/Scripts/python.exe' -m pip install opencv-python-headless matplotlib
& 'C:/Users/cbain/AppData/Local/Temp/iclots_velocity_reproduction_env/Scripts/python.exe' -X utf8 'C:/Users/cbain/AppData/Local/Temp/iclots_velocity_reproduction.py'
```

Additional read-only `Get-Content`, `rg`, `Get-FileHash`, import/version, OpenCV decoder, CSV, image, and Git containment checks were run during setup and verification.

## 17. Exact files read

- `C:/Users/cbain/AppData/Local/Temp/iclots_velocity_reproduction.py`
- `C:/Users/cbain/.codex/attachments/ae52b324-1130-49e4-ba89-767d1b7f431e/pasted-text.txt`
- `C:/Users/cbain/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.715.12143/skills/spreadsheets/SKILL.md`
- `C:/Users/cbain/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.715.12143/skills/spreadsheets/style_guidelines.md`
- `C:/Users/cbain/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.715.12143/skills/spreadsheets/artifact_tool_docs/API_QUICK_START.md`
- `C:/Users/cbain/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.715.12143/skills/spreadsheets/domain_guidance/scientific_research.md`
- `analysis/velocity.py`
- `audit_outputs/velocity_validation/archived_profile_metrics.csv`
- `audit_outputs/velocity_validation/historical_parameters.csv`
- `audit_outputs/velocity_validation/publication_comparison.csv`
- `audit_outputs/velocity_validation/velocity_validation_report.md`
- `data/Full_analysis/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi.avi`
- `data/Full_analysis/Results/70um500s-01122022143625-0000_resized-0p5x_rotate_2_croppedroi_analysis.xlsx`
- `data/Full_analysis/Results/sepsis 500_analysis.xlsx`
- `data/Full_analysis/sepsis 500.avi`
- `gui/velocity.py`
- `help/velocityhelp.py`

## 18. Exact files created

- `audit_outputs/velocity_reproduction/decoded_video_contact_sheets.png`
- `audit_outputs/velocity_reproduction/video_metadata.csv`
- `audit_outputs/velocity_reproduction/reference_summary.csv`
- `audit_outputs/velocity_reproduction/parameter_trials.csv`
- `audit_outputs/velocity_reproduction/variant_metrics.csv`
- `audit_outputs/velocity_reproduction/frame_comparison.csv`
- `audit_outputs/velocity_reproduction/profile_comparison.csv`
- `audit_outputs/velocity_reproduction/legacy_vs_archived_timecourses_control.png`
- `audit_outputs/velocity_reproduction/legacy_vs_archived_timecourses_sepsis.png`
- `audit_outputs/velocity_reproduction/legacy_vs_archived_profiles.png`
- `audit_outputs/velocity_reproduction/variant_profile_comparison.png`
- `audit_outputs/velocity_reproduction/variant_error_summary.png`
- `audit_outputs/velocity_reproduction/feature_count_comparison.png`
- `audit_outputs/velocity_reproduction/synthetic_translation_results.png`
- `audit_outputs/velocity_reproduction/synthetic_profile_results.png`
- `audit_outputs/velocity_reproduction/synthetic_results.csv`
- `audit_outputs/velocity_reproduction/fps_calibration_sensitivity.png`
- `audit_outputs/velocity_reproduction/environment_manifest.txt`
- `audit_outputs/velocity_reproduction/velocity_reproduction_report.md`

The temporary script and environment are outside the repository and are listed separately in sections 2 and 16.

## 19. Modification confirmation

No existing source, data, workbook, historical validation output, Git configuration, or repository metadata was modified. Repository-created files are confined to `audit_outputs/velocity_reproduction/`.

## 20. Final repository integrity

- Branch: `audit/repository-baseline`
- Final `git status --short`:

  ```text
  ?? .gitignore
  ?? audit_outputs/
  ```

- `.gitignore` and `audit_outputs/velocity_validation/` predated this task and were not modified.
- All 19 files created by this task are listed in section 18 and confined to `audit_outputs/velocity_reproduction/`.
- `data/` remains ignored, untracked, and unmodified; no existing source or workbook was modified.
- The only new environment is the isolated temporary environment at `C:/Users/cbain/AppData/Local/Temp/iclots_velocity_reproduction_env`, containing audit-installed `opencv-python-headless==5.0.0.93` and `matplotlib==3.11.1`.
