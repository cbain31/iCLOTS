"""End-to-end ROI screen, worker, state, progress, and cancellation tests."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from iclotspython.application import run_roi_accumulation
from iclotspython.application.errors import WorkflowCancelled
from iclotspython.gui.roi_screen import ROIAccumulationScreen
from iclotspython.gui import workers


pytestmark = [pytest.mark.unit, pytest.mark.gui]
ROOT = Path(__file__).parents[2]


def _process_until(qt_app, predicate, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.005)
    qt_app.processEvents()
    assert predicate(), "Qt operation did not finish before the test timeout"


def _run_demo(qt_app, screen: ROIAccumulationScreen) -> None:
    screen.load_demo()
    screen.start_analysis()
    _process_until(qt_app, lambda: screen._thread is None)


def test_demo_builds_explicit_valid_request(qt_app):
    screen = ROIAccumulationScreen()
    try:
        screen.load_demo()
        request = screen.build_request()
        assert len(request.frames) == 3
        assert request.channel_convention.value == "RGB"
        assert tuple(channel.value for channel in request.selected_channels) == ("red",)
        assert dict(request.thresholds)[request.selected_channels[0]] == 50
        assert request.time_values == (1.0, 2.0, 3.0)
        assert request.metadata.source_identifiers[0].startswith("synthetic://")
    finally:
        screen.shutdown()


def test_validation_feedback_for_missing_inputs_channels_and_calibration(qt_app):
    screen = ROIAccumulationScreen()
    try:
        screen.start_analysis()
        assert "Load one or more images" in screen.validation_feedback.text()

        screen.load_demo()
        screen.channel_widgets[next(iter(screen.channel_widgets))][0].setChecked(False)
        screen.start_analysis()
        assert "Select at least one channel" in screen.validation_feedback.text()

        screen.load_demo()
        screen.calibration_spin.setValue(0)
        screen.start_analysis()
        assert "finite and positive" in screen.validation_feedback.text()
        assert screen._thread is None
    finally:
        screen.shutdown()


def test_worker_delegates_to_application_service_and_populates_results(
    qt_app, monkeypatch
):
    screen = ROIAccumulationScreen()
    calls = []
    production = workers.run_roi_accumulation

    def observed_call(request, progress=None, is_cancelled=None):
        calls.append(request)
        return production(request, progress=progress, is_cancelled=is_cancelled)

    monkeypatch.setattr(workers, "run_roi_accumulation", observed_call)
    try:
        before = {path.name for path in ROOT.iterdir()}
        _run_demo(qt_app, screen)
        after = {path.name for path in ROOT.iterdir()}
        assert len(calls) == 1
        assert after == before
        assert screen.result is not None
        assert screen.result.provenance.scientific_core_module == (
            "iclotspython.core.accumulation"
        )
        assert screen.table_model.rowCount() == 4
        assert screen.table_model.columnCount() > 1
        assert len(screen.plot_canvas.figure.axes) == 2
        assert screen.progress_bar.value() == 100
        assert screen.progress_message.text() == "Analysis complete"
        assert screen.export_button.isEnabled()
        changes = screen.result.channels[0].accumulation_pixels
        assert any(value > 0 for value in changes)
        assert any(value < 0 for value in changes)
    finally:
        screen.shutdown()


def test_parameter_change_invalidates_stale_result_and_rerun_replaces_it(qt_app):
    screen = ROIAccumulationScreen()
    try:
        _run_demo(qt_app, screen)
        first = screen.result
        screen.channel_widgets[next(iter(screen.channel_widgets))][1].setValue(75)
        assert screen.result is None
        assert not screen.export_button.isEnabled()
        assert "invalidated" in screen.validation_feedback.text()

        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None)
        assert screen.result is not None
        assert screen.result is not first
        screen.clear_result()
        assert screen.result is None
        assert screen.image_list.count() == 3
        screen.clear_inputs()
        assert screen.image_list.count() == 0
    finally:
        screen.shutdown()


def test_overlapping_run_is_rejected_and_cancellation_stops_worker(
    qt_app, monkeypatch
):
    screen = ROIAccumulationScreen()

    def cancellable(request, progress=None, is_cancelled=None):
        for _ in range(200):
            if is_cancelled is not None and is_cancelled():
                raise WorkflowCancelled()
            time.sleep(0.002)
        return run_roi_accumulation(request, progress, is_cancelled)

    monkeypatch.setattr(workers, "run_roi_accumulation", cancellable)
    try:
        screen.load_demo()
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is not None)
        active_thread = screen._thread
        screen.start_analysis()
        assert screen._thread is active_thread
        assert "already running" in screen.validation_feedback.text()
        screen.cancel_analysis()
        _process_until(qt_app, lambda: screen._thread is None)
        assert screen.result is None
        assert screen.progress_message.text() == "Analysis cancelled"
        assert screen.run_button.isEnabled()
        assert not screen.cancel_button.isEnabled()
    finally:
        screen.shutdown()
