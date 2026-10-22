"""Velocity GUI uses the real OpenCV service and standard output services."""

import pytest

from iclotspython.gui.video_screen import VelocityScreen
from tests.gui.test_gui_roi_workflow import _process_until

pytestmark = [pytest.mark.unit, pytest.mark.gui]


def test_velocity_gui_demo_and_export(qt_app, tmp_path):
    screen = VelocityScreen()
    try:
        screen.load_demo()
        screen.fps_spin.setValue(10)
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None)
        assert screen.result is not None, screen.validation_feedback.text()
        assert screen.result.workflow_id == "velocity_profile"
        assert screen.result.table("All events").rows
        screen.table_selector.setCurrentText("Profile data")
        assert screen.table_model.rowCount() == 7
        screen.destination_edit.setText(str(tmp_path))
        screen.export_xlsx.setChecked(True)
        assert screen.perform_export()[0].status.value == "success"
        screen.fps_spin.setValue(11)
        assert screen.result is None
    finally:
        screen.shutdown()
