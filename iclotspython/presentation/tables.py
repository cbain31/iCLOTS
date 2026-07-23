"""Presentation conversions for ROI accumulation results."""

from __future__ import annotations

from typing import Any

from .models import PlotSeries, ROIAccumulationResult, TableData


def roi_table(result: ROIAccumulationResult) -> TableData:
    """Return a stable wide table suitable for a GUI table model."""
    columns = ["frame_label", "time"]
    for series in result.channels:
        prefix = series.channel
        columns.extend(
            [
                f"{prefix}_signal_pixels",
                f"{prefix}_area_um2",
                f"{prefix}_accumulation_pixels",
                f"{prefix}_accumulation_um2",
            ]
        )
    rows = []
    for index, (label, time_value) in enumerate(
        zip(result.frame_labels, result.time_values)
    ):
        row: list[Any] = [label, time_value]
        for series in result.channels:
            row.extend(
                [
                    series.signal_pixels[index],
                    series.area_micrometres_squared[index],
                    series.accumulation_pixels[index],
                    series.accumulation_micrometres_squared[index],
                ]
            )
        rows.append(tuple(row))
    return TableData(columns=tuple(columns), rows=tuple(rows))


def roi_export_records(
    result: ROIAccumulationResult,
) -> tuple[dict[str, Any], ...]:
    """Return export-neutral row mappings without writing a file."""
    table = roi_table(result)
    return tuple(dict(zip(table.columns, row)) for row in table.rows)


def roi_plot_series(
    result: ROIAccumulationResult,
) -> tuple[PlotSeries, ...]:
    """Return area and signed-accumulation series for each selected channel."""
    plots = []
    for series in result.channels:
        plots.extend(
            [
                PlotSeries(
                    name=f"{series.channel} ROI area",
                    channel=series.channel,
                    quantity="area",
                    x=result.time_values,
                    y=series.area_micrometres_squared,
                    x_unit="timepoint",
                    y_unit="µm²",
                ),
                PlotSeries(
                    name=f"{series.channel} ROI accumulation",
                    channel=series.channel,
                    quantity="accumulation",
                    x=result.time_values,
                    y=series.accumulation_micrometres_squared,
                    x_unit="timepoint",
                    y_unit="µm²/timepoint",
                ),
            ]
        )
    return tuple(plots)
