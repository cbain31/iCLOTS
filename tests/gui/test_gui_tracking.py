"""Each enabled tracking screen executes through the real worker/service."""

import csv
import json

import pytest

from iclotspython.gui.tracking_screen import TrackingScreen
from tests.gui.test_gui_roi_workflow import _process_until

pytestmark = [pytest.mark.unit, pytest.mark.gui]


@pytest.mark.parametrize("policy", ["general", "deformability", "transient_adhesion"])
def test_tracking_demo_defaults_produce_measurements_and_exports(qt_app, tmp_path, policy):
    pytest.importorskip("trackpy")
    screen = TrackingScreen(policy)
    try:
        screen.demo_button.click()
        screen.run_button.click()
        _process_until(qt_app, lambda: screen._thread is None, timeout=40)
        assert screen.result is not None, screen.validation_feedback.text()
        assert screen.result.workflow_id == f"tracking_{policy}"
        assert screen.result.table("Trackpy details").rows
        measurements = screen.result.table("Velocity data")
        assert measurements.rows, "The demo must yield accepted measurements, not only detections"
        velocity_column = measurements.columns.index("Velocity (µm/s)")
        duration_column = measurements.columns.index("Transit time (s)")
        # The known motion is 2 pixels/frame. Legacy background subtraction can
        # shift endpoint centroids by one pixel as the foreground mask settles.
        assert all(abs(row[velocity_column] - 2.0) <= 1.1 / row[duration_column]
                   for row in measurements.rows)
        assert screen.result.plots[0].series[0].y
        assert not any("No tracks accepted" in warning for warning in screen.result.warnings)
        screen.destination_edit.setText(str(tmp_path))
        screen.export_xlsx.setChecked(True)
        assert screen.perform_export()[0].status.value == "success"
        report = json.loads(next(tmp_path.glob("*_report.json")).read_text(encoding="utf-8"))
        measurement_report = next(t for t in report["tables"] if t["name"] == "Velocity data")
        assert measurement_report["row_count"] == len(measurements.rows)
        assert report["provenance"]["source"] == f"synthetic://tracking/{policy}"
        assert "division" not in report["parameters"]["preprocessing"]
        with next(tmp_path.glob("*_Velocity_data.csv")).open(encoding="utf-8", newline="") as handle:
            exported = list(csv.DictReader(handle))
        assert len(exported) == len(measurements.rows)
    finally:
        screen.shutdown()


@pytest.mark.parametrize("policy", ["general", "deformability", "transient_adhesion"])
def test_reload_demo_restores_defaults_and_clears_previous_crop(qt_app, policy):
    screen = TrackingScreen(policy)
    try:
        screen.video_path = "previous_video.avi"
        screen.calibration_spin.setValue(3)
        screen.fps_spin.setValue(0)
        screen.video_parameters["diameter"].setValue(2)
        screen.video_parameters["minimum_distance"].setValue(999)
        screen.crop_enabled.setChecked(True)
        screen.roi_spins["x"].setValue(999)
        screen.demo_button.click()
        request = screen.build_request()
        assert request.video.path is None
        assert request.video.source_identifier == f"synthetic://tracking/{policy}"
        assert request.micrometres_per_pixel == request.fps == 1
        assert (request.diameter, request.minmass, request.maxmass,
                request.search_range, request.minimum_distance) == (15, 1000, 2500, 60, 100)
        assert request.roi is None
        assert len(request.video.frames_rgb) == 32
        assert all(not frame.flags.writeable for frame in request.video.frames_rgb)
    finally:
        screen.shutdown()
