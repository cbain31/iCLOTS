"""Qt-compatible in-window plot driven by presentation series."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from iclotspython.presentation import ROIAccumulationResult, roi_plot_series


class ROIPlotCanvas(FigureCanvasQTAgg):
    """Display ROI area and accumulation without legacy plotting code."""

    def __init__(self, parent=None) -> None:
        self.figure = Figure(figsize=(7, 4), tight_layout=True)
        super().__init__(self.figure)
        self.setParent(parent)
        self.clear_result()

    def clear_result(self) -> None:
        self.figure.clear()
        axis = self.figure.add_subplot(111)
        axis.text(
            0.5,
            0.5,
            "Run ROI accumulation to display results",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
        axis.set_axis_off()
        self.draw()

    def set_result(self, result: ROIAccumulationResult) -> None:
        self.figure.clear()
        area_axis, accumulation_axis = self.figure.subplots(1, 2)
        for series in roi_plot_series(result):
            axis = area_axis if series.quantity == "area" else accumulation_axis
            axis.plot(series.x, series.y, marker="o", label=series.channel)
        area_axis.set_title("ROI area")
        area_axis.set_xlabel("Timepoint")
        area_axis.set_ylabel("Area (µm²)")
        accumulation_axis.set_title("ROI accumulation")
        accumulation_axis.set_xlabel("Timepoint")
        accumulation_axis.set_ylabel("Accumulation (µm²/timepoint)")
        area_axis.legend()
        accumulation_axis.legend()
        self.draw()
