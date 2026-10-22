"""Each enabled tracking screen executes through the real worker/service."""

import pytest

from iclotspython.gui.tracking_screen import TrackingScreen
from tests.gui.test_gui_roi_workflow import _process_until

pytestmark = [pytest.mark.unit, pytest.mark.gui]


@pytest.mark.parametrize("policy", ["general", "deformability", "transient_adhesion"])
def test_tracking_gui_executes_and_exports(qt_app, tmp_path, policy):
    pytest.importorskip("trackpy")
    screen = TrackingScreen(policy)
    try:
        screen.load_demo()
        screen.video_parameters["minimum_distance"].setValue(6)
        screen.video_parameters["minmass"].setValue(100)
        if policy == "transient_adhesion":
            screen.video_parameters["maxmass"].setValue(100000)
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None, timeout=40)
        assert screen.result is not None, screen.validation_feedback.text()
        assert screen.result.workflow_id == f"tracking_{policy}"
        assert screen.result.table("Trackpy details").rows
        screen.destination_edit.setText(str(tmp_path))
        screen.export_xlsx.setChecked(True)
        assert screen.perform_export()[0].status.value == "success"
    finally:
        screen.shutdown()
