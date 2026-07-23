# Tracking compatibility policy

This Phase 1 specification records current source behavior separately from GUI/help wording and general scientific invariants. The pure helpers and synthetic tests under `tests/` remain independent evidence and executable specifications. Phase 2 production measurements now live in `iclotspython.core.tracking`; TrackPy detection and linking remain in legacy adapters.

## Source trace and cross-workflow comparison

| Workflow | Linking and filtering | Measurement table and IDs | Endpoint displacement and threshold | Time and velocity | Size / fluorescence |
|---|---|---|---|---|---|
| General brightfield single-cell tracking | `tp.link_df` uses the GUI search range, `memory=1`, adaptive stop 1 and step 0.95; `filter_stubs(tr, 3)` | Loop bound is the last filtered row's particle ID, used as the exclusive end of `range`; each ID is measured from unfiltered `tr` | 2-D Euclidean endpoint distance; strict `d > GUI minimum / 3` | `(last frame - first frame) / FPS`; calibrated distance divided by time | Mean TrackPy `mass / 255`, reported as relative area in pixels |
| Fluorescence single-cell tracking | Same linking and three-observation stub filter as general tracking | Same exclusive last-ID bound and unfiltered-table measurement | 2-D Euclidean endpoint distance; strict `d > GUI minimum / 3` | Same endpoint duration and velocity | Area is `pi * mean(size)^2`; fluorescence is mean track `mass`, plotted as summed fluorescence intensity |
| Brightfield deformability | Search range is ROI width / 3, `memory=1`; `filter_stubs(tr, 3)` | Same exclusive last-ID bound and unfiltered-table measurement | Signed x endpoint displacement; strict `ROI width / 3 < d < ROI width`, therefore forward-direction only | Same endpoint duration; signed calibrated x displacement divided by time | Mean `mass / 255`, relative pixels |
| Transient adhesion | Search range is ROI width / 10, `memory=3`; `filter_stubs(tr, 10)` | Same exclusive last-ID bound and unfiltered-table measurement | Signed x endpoint displacement; strict `d < ROI width` only, so zero and reverse-x tracks pass this criterion | Same endpoint duration and signed velocity | Mean `mass / 255 * (um/pixel)^2`; mean `ecc` is labeled circularity; no fluorescence metric |

TrackPy creates linked labels; Phase 1 does not test detection or linking. The observed-frame requirements are three detections for general, fluorescence, and deformability tracking and ten for adhesion. `memory=1` permits one missing frame during linking, while adhesion uses `memory=3`. Filtering counts observations, not the numerical span between first and last frame.

## Exact legacy regression behavior

The reference regression suite preserves these checked-out source semantics:

- measurements use first and last rows of each selected trajectory;
- general and fluorescence distance is unsigned 2-D Euclidean displacement;
- deformability and adhesion use signed x displacement;
- elapsed time is the endpoint frame-index difference divided by FPS;
- general and fluorescence thresholds are strict and divide the GUI minimum by three;
- deformability uses strict lower and upper ROI-width bounds;
- adhesion applies only a strict signed upper bound;
- particle IDs are `range(last_filtered_row_particle)`, excluding that ID;
- numeric gaps in that range select empty trajectories and fail when endpoints are indexed;
- filtered IDs establish only the loop bound; measurements come from the unfiltered linked table;
- an empty filtered table fails when its last row is indexed;
- zero-duration division produces legacy non-finite output rather than a controlled result.

These are confirmed current behaviors, not claims about intent. Fluorescence tracking has a GUI error branch when the initial detected table is empty, but if detections link and `filter_stubs` returns no rows it reaches the same last-row indexing failure. The other three workflows do not guard the empty detected/filtered path before their linking and selection sequence.

## Intended and documented behavior

The shared single-cell help states that cells must be present in at least three frames, that the minimum-distance field is the minimum detected distance for a valid point, and that velocity is calculated from first/last positions. The deformability help documents three frames, x-only distance, and ROI-width/3 search and minimum-distance rules. Adhesion help describes area, circularity, and transit-time outputs but does not state its ten-frame filter or signed-direction rule.

The intended reference specification therefore requires:

- only rows belonging to tracks that survive stub filtering are measured;
- every retained particle label is considered, including the highest and noncontiguous labels;
- the general/fluorescence GUI minimum-distance value is applied literally and inclusively;
- empty selections return an empty summary;
- one-frame tracks are rejected by the workflow observation minimum;
- zero-duration velocity is rejected explicitly;
- particle labels do not affect physical measurements.

These tests exercise intended reference helpers only. They document target behavior but do not assert that the GUI-bound production code currently conforms. Production conformance is deferred until a Phase 2 extraction provides a testable boundary.

## Scientific invariants

- zero endpoint displacement gives zero distance and, for positive duration, zero velocity;
- velocity scales linearly with FPS;
- displacement and velocity scale linearly with micrometres/pixel;
- longer duration at fixed endpoint displacement lowers velocity;
- identical endpoints and duration give identical endpoint velocity regardless of intermediate path;
- horizontal Euclidean and absolute-axial distances agree;
- vertical motion has zero axial but nonzero Euclidean displacement;
- diagonal Euclidean displacement exceeds its absolute-axial component;
- signed-x workflows preserve reverse-motion sign;
- renumbering particle labels or reordering input rows does not alter physical measurements.

Endpoint-only velocity is the current measurement definition; this policy does not claim it is universally preferable to path-length or per-frame velocity.

## Known legacy quirks and unresolved intent

The unfiltered-table lookup, exclusive last-ID loop bound, contiguous-ID assumption, one-third GUI threshold, and empty-filter failure are preserved as documented evidence, not endorsed as permanent scientific requirements. The source comment describing general brightfield Euclidean distance as “x direction only” is internally inconsistent; executed mathematics is authoritative for legacy regression. Fluorescence “summed” intensity is a mean of per-detection TrackPy `mass`, and adhesion's mean `ecc` is labeled circularity; whether those labels or calculations should change is unresolved. The desired direction policy for adhesion and exact inclusive/exclusive threshold policy require scientific-owner review before production changes.
