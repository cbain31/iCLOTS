"""Optional headless GUI smoke test using the local ROI surface sequence."""

from __future__ import annotations

import time

import pytest

from iclotspython.application import ColorChannel
from iclotspython.gui.roi_screen import ROIAccumulationScreen
from tests.support.local_test_data import directory_snapshot


pytestmark = [pytest.mark.local_data, pytest.mark.integration, pytest.mark.gui]


def _process_until(qt_app, predicate, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.005)
    qt_app.processEvents()
    assert predicate(), "Local-data GUI analysis did not finish before timeout"


def test_roi_screen_loads_visible_order_and_runs_local_sequence(
    qt_app, roi_surface_paths
):
    source_directory = roi_surface_paths[0].parent
    before = directory_snapshot(source_directory)
    expected_labels = tuple(path.stem for path in roi_surface_paths)
    screen = ROIAccumulationScreen()
    try:
        screen.add_images(paths=[str(path) for path in roi_surface_paths])

        visible_labels = tuple(
            screen.image_list.item(index).text()
            for index in range(screen.image_list.count())
        )
        assert visible_labels == expected_labels
        assert "5 images" in screen.input_summary.text()
        assert "960×720" in screen.input_summary.text()

        screen.convention_combo.setCurrentText("RGB")
        screen.channel_widgets[ColorChannel.RED][0].setChecked(True)
        screen.channel_widgets[ColorChannel.RED][1].setValue(50)
        screen.calibration_spin.setValue(1.0)
        screen.interval_spin.setValue(1.0)
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None)

        assert screen.result is not None
        assert screen.result.provenance.frame_count == 5
        assert screen.table_model.rowCount() == 6
        assert len(screen.plot_canvas.figure.axes) == 2
        assert screen.export_button.isEnabled()
        assert screen.progress_bar.value() == 100
        assert directory_snapshot(source_directory) == before
    finally:
        screen.shutdown()
