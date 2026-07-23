"""Headless ROI plot rendering and overwrite-policy tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from iclotspython.output.contracts import (
    ManifestStatus,
    OutputFileStatus,
    OverwritePolicy,
    PlotRequest,
)
from iclotspython.output.errors import (
    InvalidDestinationError,
    InvalidOutputRequestError,
)
from iclotspython.output.plotting import render_roi_plot
from tests.support.output_factory import (
    roi_result,
    workspace_output_directory,
)


pytestmark = pytest.mark.unit


def test_plot_success_creates_only_requested_png_with_manifest():
    with workspace_output_directory() as destination:
        manifest = render_roi_plot(
            PlotRequest(result=roi_result(), destination_directory=destination)
        )
        assert manifest.status is ManifestStatus.SUCCESS
        assert len(manifest.files) == 1
        record = manifest.files[0]
        assert record.status is OutputFileStatus.CREATED
        path = Path(record.path)
        assert path.name == "sample_ROI_roi_plot.png"
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert record.size_bytes == path.stat().st_size
        assert len(record.sha256) == 64
        assert manifest.generated_files == (record,)
        assert {item.name for item in destination.iterdir()} == {path.name}


def test_missing_destination_requires_explicit_creation():
    with workspace_output_directory() as parent:
        missing = parent / "new-output"
        with pytest.raises(InvalidDestinationError):
            render_roi_plot(
                PlotRequest(
                    result=roi_result(), destination_directory=missing
                )
            )
        manifest = render_roi_plot(
            PlotRequest(
                result=roi_result(),
                destination_directory=missing,
                create_destination=True,
            )
        )
        assert manifest.status is ManifestStatus.SUCCESS
        assert missing.is_dir()


def test_file_destination_is_invalid():
    with workspace_output_directory() as destination:
        file_path = destination / "not-a-directory"
        file_path.write_text("sentinel", encoding="utf-8")
        with pytest.raises(InvalidDestinationError):
            render_roi_plot(
                PlotRequest(
                    result=roi_result(), destination_directory=file_path
                )
            )


def test_plot_does_not_silently_overwrite_and_explicit_replace_is_recorded():
    with workspace_output_directory() as destination:
        target = destination / "sample_ROI_roi_plot.png"
        target.write_bytes(b"original")
        failed = render_roi_plot(
            PlotRequest(result=roi_result(), destination_directory=destination)
        )
        assert failed.status is ManifestStatus.FAILED
        assert failed.files[0].status is OutputFileStatus.FAILED
        assert failed.files[0].issues[0].code == "target_exists"
        assert target.read_bytes() == b"original"

        replaced = render_roi_plot(
            PlotRequest(
                result=roi_result(),
                destination_directory=destination,
                overwrite=OverwritePolicy.REPLACE,
            )
        )
        assert replaced.status is ManifestStatus.SUCCESS
        assert replaced.files[0].status is OutputFileStatus.REPLACED
        assert replaced.files[0].issues[0].code == "target_replaced"
        assert target.read_bytes().startswith(b"\x89PNG")


def test_custom_plot_filename_must_be_a_png_leaf():
    with workspace_output_directory() as destination:
        with pytest.raises(InvalidOutputRequestError):
            render_roi_plot(
                PlotRequest(
                    result=roi_result(),
                    destination_directory=destination,
                    filename="nested/plot.png",
                )
            )
        with pytest.raises(InvalidOutputRequestError):
            render_roi_plot(
                PlotRequest(
                    result=roi_result(),
                    destination_directory=destination,
                    filename="plot.jpg",
                )
            )


def test_plot_failure_is_structured_and_leaves_no_partial_file(monkeypatch):
    from iclotspython.output import plotting

    with workspace_output_directory() as destination:
        def fail_render(*args, **kwargs):
            raise RuntimeError("synthetic renderer failure")

        monkeypatch.setattr(plotting, "_render_figure", fail_render)
        manifest = render_roi_plot(
            PlotRequest(result=roi_result(), destination_directory=destination)
        )
        assert manifest.status is ManifestStatus.FAILED
        assert manifest.files[0].issues[0].code == "plot_render_failed"
        assert tuple(destination.iterdir()) == ()

