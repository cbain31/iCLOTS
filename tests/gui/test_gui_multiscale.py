"""Real worker, navigation, tables and export for both new image workflows."""

import pytest

from iclotspython.gui.workflow_screen import MultiscaleScreen
from tests.gui.test_gui_roi_workflow import _process_until

pytestmark = [pytest.mark.unit, pytest.mark.gui]


@pytest.mark.parametrize("mode", ["device", "microchannel"])
def test_multiscale_gui_executes_and_exports(qt_app, tmp_path, mode):
    screen = MultiscaleScreen(mode)
    try:
        screen.load_demo()
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None)
        assert screen.result is not None, screen.validation_feedback.text()
        assert screen.table_model.rowCount() > 0
        assert screen.result.workflow_id == f"{mode}_accumulation"
        assert len(screen.plot_canvas.figure.axes) == 2
        screen.export_xlsx.setChecked(True)
        screen.destination_edit.setText(str(tmp_path))
        manifests = screen.perform_export()
        assert manifests[0].status.value == "success", screen.export_status.toPlainText()
        assert {p.suffix for p in tmp_path.iterdir()} == {".csv", ".xlsx", ".png", ".json"}
        screen.crop_enabled.setChecked(True)
        assert screen.result is None
    finally:
        screen.shutdown()
