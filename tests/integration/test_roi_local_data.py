"""Optional end-to-end ROI validation against locally distributed test data."""

from __future__ import annotations

import pytest

from iclotspython.application import (
    ChannelConvention,
    ColorChannel,
    ROIAccumulationRequest,
    WorkflowMetadata,
    run_roi_accumulation,
)
from iclotspython.gui.image_loader import load_image_files
from iclotspython.output import (
    ExportFormat,
    ExportRequest,
    ManifestStatus,
    PlotRequest,
    export_roi_data,
    render_roi_plot,
)
from iclotspython.presentation import roi_plot_series, roi_table
from tests.support.local_test_data import directory_snapshot
from tests.support.output_factory import workspace_output_directory


pytestmark = [pytest.mark.local_data, pytest.mark.integration]


def test_roi_surface_sequence_runs_and_exports_without_changing_source(
    roi_surface_paths,
):
    source_directory = roi_surface_paths[0].parent
    before = directory_snapshot(source_directory)
    loaded = load_image_files([str(path) for path in roi_surface_paths])

    assert loaded.labels == tuple(path.stem for path in roi_surface_paths)
    assert (loaded.width, loaded.height) == (960, 720)
    assert len(loaded.frames_rgb) == 5

    relative_sources = tuple(
        f"Multiscale_accumulation_surface/Healthy/{path.name}"
        for path in roi_surface_paths
    )
    request = ROIAccumulationRequest(
        frames=loaded.frames_rgb,
        selected_channels=(ColorChannel.RED,),
        thresholds={ColorChannel.RED: 50.0},
        micrometres_per_pixel=1.0,
        channel_convention=ChannelConvention.RGB,
        frame_labels=loaded.labels,
        time_values=(1.0, 2.0, 3.0, 4.0, 5.0),
        metadata=WorkflowMetadata(
            source_identifiers=relative_sources,
            attributes=(("validation_scope", "operability_only"),),
            suggested_export_stem="local_roi_surface_healthy",
        ),
    )

    result = run_roi_accumulation(request)
    table = roi_table(result)
    plot_series = roi_plot_series(result)

    assert result.provenance.frame_count == 5
    assert table.rows
    assert len(table.rows) == 6  # compatibility baseline plus five source frames
    assert {series.quantity for series in plot_series} == {"area", "accumulation"}

    with workspace_output_directory() as output_directory:
        plot_manifest = render_roi_plot(
            PlotRequest(result=result, destination_directory=output_directory)
        )
        export_manifest = export_roi_data(
            ExportRequest(
                result=result,
                destination_directory=output_directory,
                formats=(ExportFormat.CSV, ExportFormat.EXCEL),
            )
        )

        assert plot_manifest.status is ManifestStatus.SUCCESS
        assert export_manifest.status is ManifestStatus.SUCCESS
        assert len(tuple(output_directory.iterdir())) == 3
    assert directory_snapshot(source_directory) == before
