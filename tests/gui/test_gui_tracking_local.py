"""Opt-in complete representative tracking videos, smoke parameters only."""

import pytest

from iclotspython.gui.tracking_screen import TrackingScreen
from tests.gui.test_gui_roi_workflow import _process_until
from tests.support.local_test_data import content_snapshot
from tests.support.output_factory import workspace_output_directory

pytestmark = [pytest.mark.local_data, pytest.mark.integration, pytest.mark.gui]


@pytest.mark.parametrize("policy,folder,filename", [
    ("general", "Single_cell_tracking_brightfield_app", "Control_BFC_shortened-0-600_resized-0p5.avi"),
    ("deformability", "Single_cell_tracking_brightfield_app", "Control_BFC_shortened-0-600_resized-0p5.avi"),
    ("transient_adhesion", "Adhesion_video_app", "WBC_adhesion.avi"),
])
def test_local_tracking_video(local_test_data_root, qt_app, policy, folder, filename):
    pytest.importorskip("trackpy")
    path = local_test_data_root / folder / filename
    if not path.is_file():
        pytest.skip("Selected tracking video absent")
    before = content_snapshot([path])
    screen = TrackingScreen(policy)
    try:
        screen.add_images(paths=[str(path)])
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None, timeout=180)
        assert screen.result is not None, screen.validation_feedback.text()
        assert dict(screen.result.provenance)["decoded_frames"] > 100
        assert screen.result.table("Trackpy details").rows
        with workspace_output_directory() as output:
            screen.destination_edit.setText(str(output))
            screen.export_xlsx.setChecked(True)
            assert screen.perform_export()[0].status.value == "success"
    finally:
        screen.shutdown()
        assert content_snapshot([path]) == before
