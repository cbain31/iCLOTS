"""Opt-in real-video velocity execution and export; no historical parity claim."""

import pytest

from iclotspython.gui.video_screen import VelocityScreen
from tests.gui.test_gui_roi_workflow import _process_until
from tests.support.local_test_data import content_snapshot
from tests.support.output_factory import workspace_output_directory

pytestmark = [pytest.mark.local_data, pytest.mark.integration, pytest.mark.gui]


@pytest.mark.parametrize("filename", ["healthy_velocity.avi", "sepsis_pt_velocity.avi"])
def test_local_velocity_video(local_test_data_root, qt_app, filename):
    path = local_test_data_root / "Velocity_app" / filename
    if not path.is_file():
        pytest.skip("Selected velocity video absent")
    before = content_snapshot([path])
    screen = VelocityScreen()
    try:
        screen.add_images(paths=[str(path)])
        # Explicit smoke-test acquisition rate, not AVI playback metadata.
        screen.fps_spin.setValue(1)
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None, timeout=55)
        assert screen.result is not None, screen.validation_feedback.text()
        assert screen.result.table("All events").rows
        assert dict(screen.result.provenance)["decoded_frames"] == 401
        with workspace_output_directory() as output:
            screen.destination_edit.setText(str(output))
            screen.export_xlsx.setChecked(True)
            assert screen.perform_export()[0].status.value == "success"
    finally:
        screen.shutdown()
        assert content_snapshot([path]) == before
