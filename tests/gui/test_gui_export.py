"""Phase 3B output integration through the modern ROI screen."""

from __future__ import annotations

from pathlib import Path

import pytest

from iclotspython.application import run_roi_accumulation
from iclotspython.gui import roi_screen as roi_screen_module
from iclotspython.gui.roi_screen import ROIAccumulationScreen
from iclotspython.output.contracts import (
    IssueSeverity,
    ManifestStatus,
    OutputFileRecord,
    OutputFileStatus,
    OutputIssue,
    OutputManifest,
)
from tests.support.output_factory import workspace_output_directory


pytestmark = [pytest.mark.unit, pytest.mark.gui]


def _ready_screen() -> ROIAccumulationScreen:
    screen = ROIAccumulationScreen()
    screen.load_demo()
    screen._apply_result(run_roi_accumulation(screen.build_request()))
    return screen


def test_export_disabled_until_result_exists(qt_app):
    screen = ROIAccumulationScreen()
    try:
        assert not screen.export_button.isEnabled()
        assert screen.perform_export() == ()
        assert "No result" in screen.export_status.toPlainText()
    finally:
        screen.shutdown()


def test_gui_calls_phase3b_services_and_creates_only_selected_outputs(
    qt_app, monkeypatch
):
    screen = _ready_screen()
    plot_calls = []
    export_calls = []
    real_plot = roi_screen_module.render_roi_plot
    real_export = roi_screen_module.export_roi_data

    def observed_plot(request):
        plot_calls.append(request)
        return real_plot(request)

    def observed_export(request):
        export_calls.append(request)
        return real_export(request)

    monkeypatch.setattr(roi_screen_module, "render_roi_plot", observed_plot)
    monkeypatch.setattr(roi_screen_module, "export_roi_data", observed_export)
    try:
        with workspace_output_directory() as directory:
            screen.destination_edit.setText(str(directory))
            screen.export_xlsx.setChecked(True)
            manifests = screen.perform_export()

            assert len(plot_calls) == 1
            assert len(export_calls) == 1
            assert len(manifests) == 2
            files = sorted(path.name for path in directory.iterdir())
            assert files == [
                "synthetic_roi_demo_roi_data.csv",
                "synthetic_roi_demo_roi_data.xlsx",
                "synthetic_roi_demo_roi_plot.png",
            ]
            assert "successfully" in screen.export_status.toPlainText()
    finally:
        screen.shutdown()


def test_overwrite_requires_explicit_replace_policy(qt_app):
    screen = _ready_screen()
    try:
        with workspace_output_directory() as directory:
            screen.destination_edit.setText(str(directory))
            screen.export_png.setChecked(False)
            screen.export_xlsx.setChecked(False)
            first = screen.perform_export()
            csv_path = next(directory.iterdir())
            original = csv_path.read_bytes()

            second = screen.perform_export(overwrite=False)
            assert second[0].status is ManifestStatus.FAILED
            assert csv_path.read_bytes() == original
            assert "failed" in screen.export_status.toPlainText().lower()

            third = screen.perform_export(overwrite=True)
            assert third[0].status is ManifestStatus.SUCCESS
            assert third[0].files[0].status is OutputFileStatus.REPLACED
            assert len(tuple(directory.iterdir())) == 1
            assert first[0].files[0].path == third[0].files[0].path
    finally:
        screen.shutdown()


def test_manifest_partial_and_failed_states_are_displayed_accurately(qt_app):
    screen = _ready_screen()
    issue = OutputIssue(
        severity=IssueSeverity.ERROR,
        code="write_failed",
        message="Could not write output.",
        detail="Synthetic test failure.",
    )
    success_file = OutputFileRecord(
        kind="table",
        format="csv",
        path="result.csv",
        suggested_filename="result.csv",
        status=OutputFileStatus.CREATED,
    )
    failed_file = OutputFileRecord(
        kind="table",
        format="xlsx",
        path="result.xlsx",
        suggested_filename="result.xlsx",
        status=OutputFileStatus.FAILED,
        issues=(issue,),
    )
    partial = OutputManifest(
        workflow_id="roi_accumulation",
        destination_directory=".",
        status=ManifestStatus.PARTIAL,
        files=(success_file, failed_file),
        issues=(issue,),
    )
    failed = OutputManifest(
        workflow_id="roi_accumulation",
        destination_directory=".",
        status=ManifestStatus.FAILED,
        files=(failed_file,),
        issues=(issue,),
    )
    try:
        screen._display_manifests((partial,))
        text = screen.export_status.toPlainText()
        assert "partial success" in text
        assert "write_failed" in text
        screen._display_manifests((failed,))
        assert screen.export_status.toPlainText().startswith("Export failed.")
    finally:
        screen.shutdown()


def test_empty_or_invalid_destination_is_a_controlled_failure(qt_app):
    screen = _ready_screen()
    try:
        screen.destination_edit.clear()
        assert screen.perform_export() == ()
        assert "Choose an export destination" in screen.export_status.toPlainText()

        screen.destination_edit.setText(str(Path("missing") / "nested"))
        assert screen.perform_export() == ()
        assert "failed" in screen.export_status.toPlainText().lower()
    finally:
        screen.shutdown()
