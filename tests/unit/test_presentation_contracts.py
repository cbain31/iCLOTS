"""Stable Phase 3A result and presentation-helper tests."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from iclotspython.application.contracts import (
    ChannelConvention,
    ColorChannel,
    ROIAccumulationRequest,
    WorkflowMetadata,
)
from iclotspython.application.roi_accumulation import run_roi_accumulation
from iclotspython.presentation.models import WarningCode
from iclotspython.presentation.tables import (
    roi_export_records,
    roi_plot_series,
    roi_table,
)


pytestmark = pytest.mark.unit


def _result():
    first = np.zeros((1, 2, 3), dtype=np.uint8)
    second = np.zeros((1, 2, 3), dtype=np.uint8)
    first[0, 0, 2] = 60
    second[0, :, 2] = 60
    request = ROIAccumulationRequest(
        frames=(first, second),
        selected_channels=(ColorChannel.RED,),
        thresholds={ColorChannel.RED: 50},
        micrometres_per_pixel=0.5,
        channel_convention=ChannelConvention.BGR,
        frame_labels=("before", "after"),
        time_values=(1.0, 2.0),
        metadata=WorkflowMetadata(
            source_identifiers=("sample frame 1", "sample frame 2"),
            attributes=(("operator_note", "synthetic"),),
            suggested_export_stem="sample ROI result",
        ),
    )
    return run_roi_accumulation(request)


def test_result_and_nested_series_are_frozen():
    result = _result()
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.workflow_id = "changed"
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.channels[0].threshold = 1


def test_result_has_stable_units_labels_parameters_and_export_stem():
    result = _result()
    assert result.frame_labels == ("baseline", "before", "after")
    assert result.time_values == (0.0, 1.0, 2.0)
    assert dict(result.units)["area"] == "µm²"
    assert dict(result.units)["accumulation"] == "µm²/timepoint"
    assert dict(result.parameters)["channel_convention"] == "BGR"
    assert result.suggested_export_stem == "sample_ROI_result"


def test_table_ready_output_is_wide_and_deterministic():
    table = roi_table(_result())
    assert table.columns == (
        "frame_label",
        "time",
        "red_signal_pixels",
        "red_area_um2",
        "red_accumulation_pixels",
        "red_accumulation_um2",
    )
    assert table.rows == (
        ("baseline", 0.0, 0.0, 0.0, 0.0, 0.0),
        ("before", 1.0, 1.0, 0.25, 1.0, 0.25),
        ("after", 2.0, 2.0, 0.5, 1.0, 0.25),
    )


def test_export_records_are_file_format_neutral():
    records = roi_export_records(_result())
    assert records[1]["frame_label"] == "before"
    assert records[2]["red_area_um2"] == pytest.approx(0.5)


def test_plot_ready_output_contains_area_and_accumulation_without_plotting():
    plots = roi_plot_series(_result())
    assert [(plot.channel, plot.quantity) for plot in plots] == [
        ("red", "area"),
        ("red", "accumulation"),
    ]
    assert plots[0].x == (0.0, 1.0, 2.0)
    assert plots[0].y == (0.0, 0.25, 0.5)
    assert plots[1].y_unit == "µm²/timepoint"


def test_provenance_contains_reproducibility_fields_and_warning_codes():
    result = _result()
    provenance = result.provenance
    assert provenance.workflow_name == "roi_accumulation"
    assert provenance.workflow_contract_version == "1.0"
    assert provenance.application_version == "unversioned"
    assert provenance.scientific_core_module == "iclotspython.core.accumulation"
    assert provenance.selected_channels == ("red",)
    assert provenance.thresholds == (("red", 50.0),)
    assert provenance.frame_count == 2
    assert provenance.source_identifiers == (
        "sample frame 1",
        "sample frame 2",
    )
    assert WarningCode.ARTIFICIAL_BASELINE_INCLUDED.value in provenance.warning_codes

