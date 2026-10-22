"""Legacy video preprocessing, TrackPy orchestration and core measurements."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from iclotspython.core.tracking import LegacyTrackingPolicy, measure_legacy_tracks
from iclotspython.presentation.models import PlotSeries, TableData
from iclotspython.presentation.workflows import NamedTable, PlotPanel, WorkflowResult

from .common import Region, checkpoint, environment_versions, integer, invalid, positive
from .errors import ScientificCalculationError, WorkflowCancelled
from .video_input import VideoInput, iter_video_rgb, source_id, source_name


@dataclass(frozen=True)
class TrackingRequest:
    video: VideoInput
    policy: str = "general"
    micrometres_per_pixel: float = 1.0
    fps: float = 1.0
    diameter: int = 15
    minmass: float = 1000
    maxmass: float = 2500
    search_range: float = 60
    minimum_distance: float = 100
    roi: Region | None = None


def legacy_fluorescence_input(foreground, gray):
    """Reproduce the checked-in division exactly; callers reject nonfinite data."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.asarray(foreground) / np.asarray(gray)


def run_tracking(request: TrackingRequest, progress=None, is_cancelled=None):
    workflow = f"tracking_{request.policy}"
    checkpoint(workflow, progress, is_cancelled, 0, 1, "Validating tracking request")
    try:
        policy = LegacyTrackingPolicy(request.policy)
    except ValueError:
        invalid("policy", "Unsupported legacy tracking policy.")
    calibration = positive(request.micrometres_per_pixel, "micrometres_per_pixel")
    fps = positive(request.fps, "fps")
    diameter = integer(request.diameter, "diameter", 3)
    if diameter % 2 == 0:
        invalid("diameter", "Cell diameter must be an odd integer greater than one.")
    minmass = positive(request.minmass, "minmass", allow_zero=True)
    maxmass = positive(request.maxmass, "maxmass")
    search_range = positive(request.search_range, "search_range")
    minimum_distance = positive(request.minimum_distance, "minimum_distance", allow_zero=True)
    if policy is LegacyTrackingPolicy.TRANSIENT_ADHESION and maxmass <= minmass:
        invalid("maxmass", "Maximum mass must exceed minimum mass.")
    import cv2
    import trackpy as tp

    subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
    kernel = np.ones((5, 5), np.uint8)
    processed = []
    iterator = iter_video_rgb(request.video, request.roi)
    try:
        for index, frame in enumerate(iterator):
            checkpoint(workflow, progress, is_cancelled, index, index + 2, f"Preparing frame {index}")
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            if policy is LegacyTrackingPolicy.TRANSIENT_ADHESION:
                prepared = gray
            else:
                foreground = cv2.morphologyEx(subtractor.apply(gray), cv2.MORPH_CLOSE, kernel)
                prepared = legacy_fluorescence_input(foreground, gray) if policy is LegacyTrackingPolicy.FLUORESCENCE else foreground
                if not np.all(np.isfinite(prepared)):
                    raise ScientificCalculationError(
                        "Legacy fluorescence preprocessing divides foreground mask by grayscale intensity and produces NaN/Inf at zero pixels. A scientifically reviewed correction is required; no normalization or replacement was applied. See docs/testing/scientific_issue_register.md."
                    )
            processed.append(prepared)
    finally:
        iterator.close()
    width = processed[0].shape[1]
    if policy is LegacyTrackingPolicy.DEFORMABILITY:
        search_range, minimum_distance = width / 3, width
    elif policy is LegacyTrackingPolicy.TRANSIENT_ADHESION:
        search_range, minimum_distance = width / 10, width
    if policy is LegacyTrackingPolicy.FLUORESCENCE:
        minmass = 50
    checkpoint(workflow, progress, is_cancelled, len(processed), len(processed) + 2, "Detecting cells with TrackPy")
    def after_locate(frame_no, features):
        if is_cancelled and is_cancelled():
            raise WorkflowCancelled()
        return features

    features = tp.batch(processed, diameter, minmass=minmass, invert=False, processes=1, after_locate=after_locate)
    if policy is LegacyTrackingPolicy.TRANSIENT_ADHESION:
        features = features[features["mass"] < maxmass]
    memory, stub_length = (3, 10) if policy is LegacyTrackingPolicy.TRANSIENT_ADHESION else (1, 3)
    checkpoint(workflow, progress, is_cancelled, len(processed) + 1, len(processed) + 2, "Linking cells with legacy policy")
    warnings = ["Legacy particle enumeration excludes the last filtered particle ID; measurements use unfiltered linked rows. Selection and motion policies are preserved, including reverse transient motion."]
    if len(features):
        linked = tp.link_df(features, search_range=search_range, memory=memory, adaptive_stop=1, adaptive_step=0.95)
        filtered = tp.filter_stubs(linked, stub_length)
        if len(filtered):
            try:
                measurements = measure_legacy_tracks(filtered.to_dict("records"), linked.to_dict("records"), fps, calibration, policy, minimum_distance)
            except (IndexError, KeyError, ValueError) as exc:
                raise ScientificCalculationError(f"Legacy particle selection could not be evaluated: {exc}") from exc
        else:
            measurements = ()
    else:
        linked, filtered, measurements = features, features, ()
    if not measurements:
        warnings.append("No tracks accepted by the legacy policy. Empty measurements are reported without invented zeros.")
    if policy is LegacyTrackingPolicy.FLUORESCENCE:
        warnings.append("Legacy fluorescence preprocessing divides foreground mask by intensity (not multiplication). Scientific review pending; output is compatibility evidence only.")
    columns = ("Particle", "Source particle", "Start frame", "End frame", "Transit time (s)", "Distance traveled (µm)", "Velocity (µm/s)", "Area (pix)", "Fl. int. (a.u.)", "Area (µm²)", "Circularity (a.u.)")
    rows = tuple((i, m.source_particle, m.start_frame, m.end_frame, m.elapsed_seconds, m.distance_micrometres, m.velocity_micrometres_per_second,
                  m.area_pixels, m.fluorescence, m.area_micrometres_squared, m.circularity) for i, m in enumerate(measurements))
    accepted = {m.source_particle for m in measurements}
    linked_columns = tuple(str(c) for c in linked.columns)
    linked_rows = tuple(tuple(v.item() if isinstance(v, np.generic) else v for v in row) + (int(row[linked_columns.index("particle")]) in accepted if "particle" in linked_columns else False,)
                        for row in linked.itertuples(index=False, name=None))
    summaries = []
    for column in range(4, len(columns)):
        values = np.asarray([r[column] for r in rows if r[column] is not None], dtype=float)
        # Match pandas descriptive statistics: skip NaN, retain Inf.
        values = values[~np.isnan(values)]
        with np.errstate(invalid="ignore"):
            summaries.append((columns[column], len(values), float(np.min(values)) if values.size else float("nan"),
                float(np.mean(values)) if values.size else float("nan"), float(np.max(values)) if values.size else float("nan"),
                float(np.std(values, ddof=1)) if values.size > 1 else float("nan")))
    tables = (NamedTable("Velocity data", TableData(columns, rows)),
              NamedTable("Trackpy details", TableData((*linked_columns, "Accepted"), linked_rows)),
              NamedTable("Summary", TableData(("Measurement", "n", "Min", "Mean", "Max", "Stdev (sample)"), tuple(summaries))))
    plot = PlotPanel("Track velocity", "Particle (display index)", "Velocity (µm/s)", (
        PlotSeries("Velocity", "", "velocity", tuple(float(i) for i in range(len(rows))), tuple(m.velocity_micrometres_per_second for m in measurements), "particle", "µm/s"),))
    parameters = (("policy", policy.value), ("fps", fps), ("micrometres_per_pixel", calibration), ("diameter", diameter), ("minmass", minmass),
                  ("maxmass", maxmass if policy is LegacyTrackingPolicy.TRANSIENT_ADHESION else None), ("search_range", search_range),
                  ("memory", memory), ("stub_length", stub_length), ("adaptive_stop", 1), ("adaptive_step", 0.95),
                  ("distance_threshold_pixels", minimum_distance), ("roi", request.roi),
                  ("preprocessing", "grayscale" if policy is LegacyTrackingPolicy.TRANSIENT_ADHESION else "MOG2 detectShadows=False; MORPH_CLOSE 5x5; legacy division for fluorescence"))
    provenance = (("contract_version", "1.0"), ("scientific_policy", "legacy-compatible"), ("scientific_core", "iclotspython.core.tracking"),
                  ("source", source_id(request.video)), ("decoded_frames", len(processed)), ("environment", environment_versions("opencv-python", "trackpy", "pandas", "scipy", "numba")))
    checkpoint(workflow, progress, is_cancelled, 1, 1, "Analysis complete")
    return WorkflowResult(workflow, tables, (plot,), parameters, provenance, tuple(warnings), source_name(request.video))
