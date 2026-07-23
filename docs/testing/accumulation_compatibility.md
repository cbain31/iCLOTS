# Accumulation and occlusion compatibility policy

This Phase 1 specification separates checked-out numerical behavior from GUI/help terminology, scientific invariants, and unresolved workflow decisions. The synthetic helpers are executable references, not production replacements.

## Cross-workflow comparison

| Property | ROI / surface accumulation | Device-map accumulation | Microchannel accumulation |
|---|---|---|---|
| Accepted images | One image or a same-field series of BGR images | Same; the GUI also builds a map from the complete series | One image or a same-field series containing horizontal channel portions |
| Threshold | Per selected BGR layer; OpenCV binary threshold is strict `value > threshold` | Same analysis threshold; map uses strict `> 10` across every frame and BGR layer | Per selected layer; map thresholds all BGR layers in the last file using their configured thresholds |
| Denominator | None | Number of nonzero device-map pixels | Bounding-band height per connected map region, independently for every x column |
| Area | Signal pixels and signal pixels × `(um/pixel)^2` | Same | Per-region signal pixels and calibrated area |
| Percentage | None | Raw ROI signal pixels / device-map pixels × 100; numerator is not restricted to the map | Per-column signal pixels / region bounding-band height × 100; mean and maximum across columns |
| Accumulation | Signed pixel-count change | Signed pixel-count change | Signed per-region area change |
| First point | Artificial zero row, followed by first observed area and its change from zero | Artificial zero row for area, percent, and accumulation | First observed frame is frame 0; accumulation is area minus an internal zero state |
| Spatial output | One value per frame/channel | One value per frame/channel | Frame, zero-based connected-region label, and zero-based ROI-relative x-column coordinates |
| Geometry source | User ROI only | Union of signal above 10 in all frames and all three color layers | Signal in the lexically last image, unioned across all three thresholded layers, collapsed by row, then expanded across ROI width |
| RGB overlap | Each selected layer counted independently | Same; map union counts location once | Same within each color analysis; map union counts location once |
| Main failure modes | Empty file list/crop or invalid calibration are not guarded | Zero map denominator yields non-finite percent; signal outside the map can exceed 100% | Empty map later reaches empty summaries/plotting; geometry depends on last frame and horizontal row runs |

Directory selection is lexical within each extension and concatenates PNG, JPG, then TIF groups. Consequently `frame1.png`, `frame10.png`, `frame2.png` are processed in that order. Help explicitly asks users to provide leading zeros.

## Exact legacy regression behavior

- Binary signal is `value > threshold`; equality does not count.
- BGR indices are blue 0, green 1, red 2.
- Selected colors are processed independently, so an overlapping pixel contributes once to each selected color.
- Pixel area converts to physical area by multiplying by calibration squared.
- ROI and device outputs prepend artificial zero time, area, and accumulation entries.
- The first observed ROI/device accumulation is its area minus artificial zero.
- Signed losses remain negative.
- The device map is the union of all pixels above fixed threshold 10 in any BGR layer of any analyzed image.
- Device percent uses all threshold-positive ROI pixels as numerator and device-map pixel count as denominator, without intersecting numerator and map.
- A zero device area produces legacy `NaN` for zero signal or signed infinity for nonzero signal.
- The microchannel map comes only from the final file, includes all three layers regardless of selected output colors, and expands any qualifying signal row across the full width when width is greater than one.
- Four-connected contiguous row bands become channel labels in top-to-bottom order.
- Microchannel measurement uses the full rectangular row bounding band, not the original signal geometry, and reports x coordinates `0..width-1` relative to the ROI.
- Microchannel first-frame accumulation is area minus an internal zero state; no separate artificial output row is added.

## Intended and documented behavior

The help describes sequential same-field images, thresholded selected colors, calibrated area, signed accumulation, device/channel maps, and microchannel percent-y occlusion. It also warns that filenames must already sort in experimental order and that complete signal is needed to form geometry.

The intended reference specification adds controlled behavior without claiming production compliance:

- callers may supply chronological order explicitly;
- the first observed frame is distinguishable from any display baseline;
- an empty mask returns zero area and an empty region summary;
- a zero-area device map returns a controlled zero summary;
- device percentages count signal inside the device and remain within 0–100%;
- channel labels are deterministically mapped to red, green, and blue outputs;
- every detected connected region is included in deterministic top-left order;
- incomplete horizontal geometry produces a clear validation error rather than silent row expansion.

Passing intended-helper tests do not establish that GUI-bound production currently conforms.

## Scientific invariants

- zero signal has zero raw and physical area;
- a full binary mask has area equal to its pixel count;
- doubling micrometres/pixel multiplies physical area by four;
- identical sequential masks have zero signed change;
- signal loss has negative signed accumulation;
- device percentage is independent of physical calibration;
- adding positive pixels cannot reduce the same color's area;
- independent RGB overlap does not change another channel's count;
- channel ordering does not change per-channel values;
- translation inside a fixed device does not change total raw area;
- changing device-map area changes percentage but not raw signal area;
- splitting a mask into disconnected regions preserves total raw area;
- a known rectangular band yields its expected column-occupancy pattern.

## Known quirks and unresolved scientific intent

Artificial display baselines, signal-derived maps, last-frame dependence, overlap double counting across colors, lexical ordering, unrestricted device numerators, and missing zero-area guards are documented evidence, not permanent scientific requirements. Whether a device map should be supplied independently, whether percentages should always be map-intersected, whether first-frame accumulation should be zero or area-from-baseline, and whether overlapping fluorophores should be combined or reported independently require workflow-owner review. The help describes left-to-right channel indexing, while source labels vertically separated horizontal row bands top-to-bottom; the desired terminology is unresolved.

