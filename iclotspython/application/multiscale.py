"""Device and microchannel accumulation, delegating all measurements to core."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from iclotspython.core import accumulation as core
from iclotspython.presentation.models import PlotSeries, TableData
from iclotspython.presentation.workflows import NamedTable, PlotPanel, WorkflowResult

from .common import Region, checkpoint, environment_versions, invalid
from .contracts import ColorChannel, ROIAccumulationRequest
from .roi_accumulation import _CHANNEL_INDEX, _export_stem
from .validation import validate_roi_accumulation_request


@dataclass(frozen=True)
class MultiscaleRequest:
    images: ROIAccumulationRequest
    mode: str
    roi: Region | None = None


def run_multiscale(request: MultiscaleRequest, progress=None, is_cancelled=None):
    if request.mode not in {"device", "microchannel"}:
        invalid("mode", "Choose device or microchannel accumulation.")
    workflow = f"{request.mode}_accumulation"
    checkpoint(workflow, progress, is_cancelled, 0, 1, "Validating images")
    outcome = validate_roi_accumulation_request(request.images)
    validated = outcome.request
    # Unselected colors also define microchannel geometry; require their
    # thresholds explicitly instead of silently substituting defaults.
    if request.mode == "microchannel":
        geometry = validate_roi_accumulation_request(replace(
            request.images, selected_channels=tuple(ColorChannel)
        )).request
    else:
        geometry = validated
    frames = validated.frames
    if request.roi:
        ys, xs = request.roi.slices(frames[0].shape)
        frames = tuple(frame[ys, xs] for frame in frames)
    layers = _CHANNEL_INDEX[validated.channel_convention]
    bgr = tuple(frame if validated.channel_convention.value == "BGR" else frame[:, :, ::-1]
                for frame in frames)
    thresholds = {channel.value: value for channel, value in geometry.thresholds}
    if request.mode == "device":
        map_mask = core.legacy_device_map(np.stack(bgr), map_threshold=10)
    else:
        map_mask = core.legacy_microchannel_map(bgr[-1], thresholds)
    warnings = [f"[{w.code.value}] {w.message}" for w in outcome.warnings]
    tables, plot_groups = [], [[], []]
    total = len(frames) * len(validated.selected_channels) + 1
    current = 0
    all_rows, raw_rows, summary_rows = [], [], []
    for color in validated.selected_channels:
        masks = []
        for label, frame in zip(validated.frame_labels, frames):
            checkpoint(workflow, progress, is_cancelled, current, total, f"Processing {color.value}: {label}")
            masks.append(core.threshold_channel(frame[:, :, layers[color]], validated.threshold_for(color)))
            current += 1
        if request.mode == "device":
            series = core.legacy_series_with_zero_baseline([core.count_signal_pixels(m) for m in masks])
            area = tuple(core.calibrated_area(v, validated.micrometres_per_pixel) for v in series.values)
            changes = tuple(core.calibrated_area(v, validated.micrometres_per_pixel) for v in series.changes)
            percent = (0.0, *(core.legacy_percent_occlusion(m, map_mask) for m in masks))
            times = (0.0, *validated.time_values)
            labels = ("baseline", *validated.frame_labels)
            for i, label in enumerate(labels):
                all_rows.append((color.value, label, times[i], float(series.values[i]), area[i], percent[i], float(series.changes[i]), changes[i]))
            plot_groups[0].append(PlotSeries(color.value, color.value, "occlusion", times, percent, "timepoint", "%"))
            plot_groups[1].append(PlotSeries(color.value, color.value, "accumulation", times, changes, "timepoint", "µm²/timepoint"))
        else:
            measurements = core.legacy_microchannel_series(masks, map_mask, validated.micrometres_per_pixel)
            for m in measurements:
                all_rows.append((color.value, m.frame, validated.frame_labels[m.frame], m.channel, m.row_start, m.row_end,
                                 m.mean_occlusion_percent, m.max_occlusion_percent, m.area_pixels, m.accumulation_pixels,
                                 m.area_micrometres_squared, m.accumulation_micrometres_squared))
                raw_rows.append((color.value, m.frame, m.channel, *map(float, m.column_occupancy_percent)))
            mean_occ, mean_acc = [], []
            for frame in range(len(frames)):
                items = [m for m in measurements if m.frame == frame]
                if not items:
                    continue
                values = tuple(float(np.mean([getattr(m, attr) for m in items])) for attr in (
                    "mean_occlusion_percent", "max_occlusion_percent", "area_pixels", "accumulation_pixels",
                    "area_micrometres_squared", "accumulation_micrometres_squared"))
                summary_rows.append((color.value, frame, *values))
                mean_occ.append(values[0])
                mean_acc.append(values[-1])
            times = tuple(float(i) for i in range(len(mean_occ)))
            plot_groups[0].append(PlotSeries(color.value, color.value, "occlusion", times, tuple(mean_occ), "frame", "%"))
            plot_groups[1].append(PlotSeries(color.value, color.value, "accumulation", times, tuple(mean_acc), "frame", "µm²/timepoint"))
    if request.mode == "device":
        columns = ("Color", "Image", "Timepoint", "Occlusion (pix)", "Occlusion (µm²)", "Occlusion (% device)", "Accumulation (pix/timepoint)", "Accumulation (µm²/timepoint)")
        warnings.append("Legacy device map: signal >10 in any layer of any frame; numerator is unrestricted. Percentages may exceed 100% or be NaN/Inf. Artificial zero baseline included.")
    else:
        columns = ("Color", "Frame", "Image", "Channel", "Row start", "Row end (exclusive)", "Mean occlusion (%)", "Max. occlusion (%)", "Area (pix)", "Accumulation (pix)", "Area (µm²)", "Accumulation (µm²)")
        tables.extend((
            NamedTable("Column occupancy", TableData(("Color", "Frame", "Channel", *(str(i) for i in range(frames[0].shape[1]))), tuple(raw_rows))),
            NamedTable("Frame summary", TableData(("Color", "Frame", *columns[6:]), tuple(summary_rows))),
        ))
        warnings.append("Legacy microchannel geometry uses all three colors in the final frame, full-width horizontal bands. Changes are signed from a per-channel zero baseline; no artificial frame row is added.")
        if not all_rows:
            warnings.append("No horizontal microchannels detected in the final frame.")
    tables.insert(0, NamedTable("Measurements", TableData(columns, tuple(all_rows))))
    # Compact exact geometry, rather than a full image embedded in every result.
    # Device maps can contain millions of pixels: report count, not coordinate rows.
    if request.mode == "microchannel":
        tables.append(NamedTable("Geometry", TableData(("Row start", "Row end (exclusive)"), core.horizontal_row_regions(map_mask))))
    parameters = (("mode", request.mode), ("thresholds", thresholds), ("selected_channels", tuple(c.value for c in validated.selected_channels)),
                  ("channel_convention", validated.channel_convention.value), ("micrometres_per_pixel", validated.micrometres_per_pixel),
                  ("roi", request.roi), ("device_map_threshold", 10), ("map_pixels", core.count_signal_pixels(map_mask)))
    provenance = (("contract_version", "1.0"), ("scientific_core", "iclotspython.core.accumulation"),
                  ("sources", validated.metadata.source_identifiers), ("source_metadata", validated.metadata.attributes),
                  ("environment", environment_versions()), ("scientific_policy", "legacy-compatible"))
    checkpoint(workflow, progress, is_cancelled, total, total, "Analysis complete")
    return WorkflowResult(workflow, tuple(tables), (
        PlotPanel("Occlusion", "Timepoint" if request.mode == "device" else "Frame", "Occlusion (%)", tuple(plot_groups[0])),
        PlotPanel("Accumulation", "Timepoint" if request.mode == "device" else "Frame", "Accumulation (µm²/timepoint)", tuple(plot_groups[1])),
    ), parameters, provenance, tuple(warnings), _export_stem(request.images))
