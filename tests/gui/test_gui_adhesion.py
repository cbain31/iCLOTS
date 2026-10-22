"""Every static adhesion screen runs and exports with independent images."""

import pytest

from iclotspython.gui.adhesion_screen import AdhesionScreen
from iclotspython.gui.image_loader import LoadedImages
from tests.gui.test_gui_roi_workflow import _process_until
from tests.unit.test_adhesion_workflow import cell_image

pytestmark = [pytest.mark.unit, pytest.mark.gui]


@pytest.mark.parametrize("mode", ["brightfield", "fluorescence", "filopodia"])
def test_adhesion_screen_runs_and_exports(qt_app, tmp_path, mode):
    if mode == "brightfield":
        pytest.importorskip("trackpy")
    screen = AdhesionScreen(mode)
    rgb = cell_image()
    try:
        screen._set_loaded(LoadedImages((rgb, rgb[:30]), ("first", "second"), ("synthetic://first", "synthetic://second"), 80, 64, True))
        screen.primary_combo.setCurrentText("red")
        screen.invert_checkbox.setChecked(False)
        if mode == "brightfield":
            screen.adhesion_parameters["minmass"].setValue(10)
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None, timeout=30)
        assert screen.result is not None, screen.validation_feedback.text()
        assert screen.result.table("Measurements").rows
        screen.destination_edit.setText(str(tmp_path))
        screen.export_xlsx.setChecked(True)
        assert screen.perform_export()[0].status.value == "success"
        screen.calibration_spin.setValue(2)
        assert screen.result is None
    finally:
        screen.shutdown()
