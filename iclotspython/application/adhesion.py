"""Static brightfield, fluorescence and filopodia application workflows."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from iclotspython.core.adhesion import brightfield_area, segment_legacy_cells
from iclotspython.presentation.models import PlotSeries, TableData
from iclotspython.presentation.workflows import NamedTable, PlotPanel, WorkflowResult

from .common import Region, checkpoint, environment_versions, integer, invalid, positive
from .contracts import ROIAccumulationRequest
from .roi_accumulation import _CHANNEL_INDEX, _export_stem
from .validation import validate_roi_accumulation_request


@dataclass(frozen=True)
class AdhesionRequest:
    images: ROIAccumulationRequest
    mode: str = "fluorescence"
    primary_channel: str = "grayscale"
    functional_channel: str = "none"
    minarea: float = 0
    maxarea: float = 10000
    primary_threshold: float = 50
    functional_threshold: float = 30
    harris_k: float = 0.2
    threshold_rel: float = 0.5
    min_distance: int = 5
    diameter: int = 15
    minmass: float = 1000
    invert: bool = True
    roi: Region | None = None


def run_adhesion(request: AdhesionRequest, progress=None, is_cancelled=None):
    workflow = f"adhesion_{request.mode}"
    checkpoint(workflow, progress, is_cancelled, 0, 1, "Validating adhesion request")
    if request.mode not in {"brightfield", "fluorescence", "filopodia"}:
        invalid("mode", "Unsupported static adhesion mode.")
    raw_frames = tuple(request.images.frames)
    labels = tuple(request.images.frame_labels) if request.images.frame_labels is not None else tuple(f"image_{i + 1}" for i in range(len(raw_frames)))
    if len(labels) != len(raw_frames) or not raw_frames:
        invalid("frames", "Provide one label per image and at least one image.")
    sources = tuple(request.images.metadata.source_identifiers)
    if sources and len(sources) != len(raw_frames):
        invalid("sources", "Provide one source identifier per image when supplied.")
    # Images are independent specimens and may have different dimensions.
    normalized = [validate_roi_accumulation_request(replace(request.images, frames=(frame,), frame_labels=(label,), time_values=None,
                  metadata=replace(request.images.metadata, source_identifiers=(sources[i],) if sources else ()))).request
                  for i, (frame, label) in enumerate(zip(raw_frames, labels))]
    validated = replace(normalized[0], frames=tuple(item.frames[0] for item in normalized), frame_labels=labels,
                        metadata=replace(normalized[0].metadata, source_identifiers=sources))
    if request.primary_channel not in {"grayscale", "red", "green", "blue"} or request.functional_channel not in {"none", "red", "green", "blue"}:
        invalid("channel", "Choose an explicit primary and functional channel.")
    minarea = positive(request.minarea, "minarea", allow_zero=True)
    maxarea = positive(request.maxarea, "maxarea")
    if minarea >= maxarea:
        invalid("maxarea", "Maximum area must exceed minimum area (strict bounds).")
    for field in ("primary_threshold", "functional_threshold"):
        value = positive(getattr(request, field), field, allow_zero=True)
        if value > 255:
            invalid(field, "Thresholds must be between 0 and 255.")
    k = positive(request.harris_k, "harris_k", allow_zero=True)
    rel = positive(request.threshold_rel, "threshold_rel", allow_zero=True)
    if k > 1 or rel > 1:
        invalid("corner_parameters", "Harris k and relative threshold must be between 0 and 1.")
    mindistance = integer(request.min_distance, "min_distance")
    diameter = integer(request.diameter, "diameter", 3)
    if diameter % 2 == 0:
        invalid("diameter", "Cell diameter must be odd.")
    minmass = positive(request.minmass, "minmass", allow_zero=True)
    import cv2

    rows, image_stats = [], []
    calibration = validated.micrometres_per_pixel
    warnings = ["Legacy output 'Circularity (a.u.)' is eccentricity, not a circularity formula. Strict size/threshold comparisons and population texture SD are retained."]
    if request.mode == "filopodia":
        warnings.append("Filopodia lengths retain the legacy swapped row/column center convention on the convex bounding image with a 10-pixel border. No geometric correction is applied.")
    for index, (label, frame) in enumerate(zip(validated.frame_labels, validated.frames)):
        checkpoint(workflow, progress, is_cancelled, index, len(validated.frames) + 1, f"Analyzing {label}")
        if request.roi:
            ys, xs = request.roi.slices(frame.shape)
            frame = frame[ys, xs]
        if frame.dtype != np.uint8:
            invalid("frames", "Static adhesion currently requires uint8 images; no intensity rescaling is applied.")
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY if validated.channel_convention.value == "RGB" else cv2.COLOR_BGR2GRAY)
        count_before = len(rows)
        if request.mode == "brightfield":
            import trackpy as tp

            found = tp.locate(gray, diameter, minmass=minmass, invert=request.invert)
            for cell_index, cell in enumerate(found.itertuples(index=False)):
                area, area_um = brightfield_area(cell.size, calibration)
                rows.append((label, cell_index, float(cell.x), float(cell.y), area, area_um, float(cell.ecc), float(cell.mass), float(cell.size)))
        else:
            layers = _CHANNEL_INDEX[validated.channel_convention]
            primary = gray if request.primary_channel == "grayscale" else frame[:, :, layers[next(c for c in layers if c.value == request.primary_channel)]]
            functional = np.zeros_like(primary) if request.functional_channel == "none" else frame[:, :, layers[next(c for c in layers if c.value == request.functional_channel)]]
            cells = segment_legacy_cells(primary, functional, calibration, minarea, maxarea, request.primary_threshold, request.functional_threshold,
                filopodia=request.mode == "filopodia", harris_k=k, threshold_rel=rel, min_distance=mindistance)
            for cell_index, cell in enumerate(cells):
                row = (label, cell_index, cell.x, cell.y, cell.area_pixels, cell.area_micrometres_squared, cell.eccentricity, cell.texture)
                row += ((cell.filopodia_count, cell.filopodia_min, cell.filopodia_mean, cell.filopodia_max, cell.filopodia_stdev)
                        if request.mode == "filopodia" else (cell.functional_signal, cell.functional_intensity))
                rows.append(row)
        n = len(rows) - count_before
        area_mm = frame.shape[0] * frame.shape[1] * calibration * calibration / 1E6
        image_stats.append((label, n, area_mm, n / area_mm))
    columns = ("Image", "Index", "x", "y", "Area (pix)", "Area (µm²)", "Circularity (a.u.)")
    if request.mode == "brightfield":
        columns += ("Mass (a.u.)", "Radius (pix)")
    elif request.mode == "filopodia":
        columns += ("Texture (a.u.)", "Filopodia (n)", "Min. filopodia length (µm)", "Mean filopodia length (µm)", "Max. filopodia length (µm)", "Stdev. filopodia length (µm)")
    else:
        columns += ("Texture (a.u.)", "Signal (binary)", "Fn. stain intensity (a.u.)")
    summaries = []
    for label in (*validated.frame_labels, "All images"):
        selected = rows if label == "All images" else [r for r in rows if r[0] == label]
        for col in range(4, len(columns)):
            values = [r[col] for r in selected]
            summaries.append((label, columns[col], len(values), float(np.min(values)) if values else float("nan"),
                float(np.mean(values)) if values else float("nan"), float(np.max(values)) if values else float("nan"), float(np.std(values, ddof=1)) if len(values) > 1 else float("nan")))
    image_stats.append(("All images", len(rows), sum(r[2] for r in image_stats), len(rows) / sum(r[2] for r in image_stats)))
    tables = (NamedTable("Measurements", TableData(columns, tuple(rows))), NamedTable("Image summary", TableData(("Image", "n cells", "Image area (mm²)", "Cell density (cells/mm²)"), tuple(image_stats))),
              NamedTable("Descriptive statistics", TableData(("Image", "Measurement", "n", "Min", "Mean", "Max", "Stdev (sample)"), tuple(summaries))))
    plots = (PlotPanel("Cell area", "Cell (combined index)", "Area (µm²)", (PlotSeries("Area", "", "area", tuple(map(float, range(len(rows)))), tuple(r[5] for r in rows), "cell", "µm²"),)),)
    parameters = tuple((field, getattr(request, field)) for field in request.__dataclass_fields__ if field != "images") + (("micrometres_per_pixel", calibration), ("channel_convention", validated.channel_convention.value))
    provenance = (("contract_version", "1.0"), ("scientific_policy", "legacy-compatible"), ("scientific_core", "iclotspython.core.adhesion"),
                  ("sources", validated.metadata.source_identifiers), ("environment", environment_versions("opencv-python", "scikit-image", "trackpy")))
    checkpoint(workflow, progress, is_cancelled, 1, 1, "Analysis complete")
    return WorkflowResult(workflow, tables, plots, parameters, provenance, tuple(warnings), _export_stem(request.images))
