"""Stable GUI-independent result and presentation contracts."""

from .models import (
    ChannelAccumulationSeries,
    PlotSeries,
    Provenance,
    ROIAccumulationResult,
    TableData,
    WarningCode,
    WarningRecord,
)
from .tables import roi_export_records, roi_plot_series, roi_table

__all__ = [
    "ChannelAccumulationSeries",
    "PlotSeries",
    "Provenance",
    "ROIAccumulationResult",
    "TableData",
    "WarningCode",
    "WarningRecord",
    "roi_export_records",
    "roi_plot_series",
    "roi_table",
]

