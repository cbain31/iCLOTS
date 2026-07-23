"""Phase 3B request, manifest, and filename contract tests."""

from __future__ import annotations

import dataclasses

import pytest

from iclotspython.output.contracts import (
    ExportFormat,
    ExportRequest,
    OverwritePolicy,
    PlotRequest,
)
from iclotspython.output.exporting import suggest_export_filename
from iclotspython.output.plotting import suggest_plot_filename
from tests.support.output_factory import roi_result


pytestmark = pytest.mark.unit


def test_plot_and_export_requests_are_frozen():
    plot = PlotRequest(result=roi_result(), destination_directory=".")
    export = ExportRequest(result=roi_result(), destination_directory=".")
    with pytest.raises(dataclasses.FrozenInstanceError):
        plot.dpi = 300
    with pytest.raises(dataclasses.FrozenInstanceError):
        export.overwrite = OverwritePolicy.REPLACE


def test_suggested_filenames_are_deterministic_and_sanitized():
    result = roi_result("Patient-free synthetic ROI")
    assert (
        suggest_plot_filename(result)
        == "Patient-free_synthetic_ROI_roi_plot.png"
    )
    assert (
        suggest_export_filename(result, ExportFormat.CSV)
        == "Patient-free_synthetic_ROI_roi_data.csv"
    )
    assert (
        suggest_export_filename(result, ExportFormat.EXCEL)
        == "Patient-free_synthetic_ROI_roi_data.xlsx"
    )


def test_contracts_carry_result_as_the_only_numerical_input():
    plot_fields = {field.name for field in dataclasses.fields(PlotRequest)}
    export_fields = {field.name for field in dataclasses.fields(ExportRequest)}
    assert "result" in plot_fields and "result" in export_fields
    assert not {
        "frames",
        "thresholds",
        "micrometres_per_pixel",
        "signal_pixels",
    } & (plot_fields | export_fields)

