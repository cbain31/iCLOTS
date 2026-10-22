"""Opt-in independent local adhesion images; no source modification."""

import pytest

from iclotspython.gui.adhesion_screen import AdhesionScreen
from tests.gui.test_gui_roi_workflow import _process_until
from tests.support.local_test_data import directory_snapshot
from tests.support.output_factory import workspace_output_directory

pytestmark = [pytest.mark.local_data, pytest.mark.integration, pytest.mark.gui]


@pytest.mark.parametrize("mode,folder", [("brightfield", "Adhesion_brightfield_app"), ("fluorescence", "Adhesion_fluorescence_app"), ("filopodia", "Adhesion_filopodia_app")])
def test_local_static_adhesion(local_test_data_root, qt_app, mode, folder):
    if mode == "brightfield":
        pytest.importorskip("trackpy")
    directory = local_test_data_root / folder
    if not directory.is_dir():
        pytest.skip("Selected static adhesion images absent")
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in {".png", ".tif", ".tiff"})
    if not paths:
        pytest.skip("No static images available")
    before = directory_snapshot(directory)
    screen = AdhesionScreen(mode)
    try:
        screen.add_images(paths=[str(p) for p in paths])
        assert screen.image_list.count() == len(paths), screen.validation_feedback.text()
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None, timeout=180)
        assert screen.result is not None, screen.validation_feedback.text()
        assert len(screen.result.table("Image summary").rows) == len(paths) + 1
        with workspace_output_directory() as output:
            screen.destination_edit.setText(str(output))
            screen.export_xlsx.setChecked(True)
            assert screen.perform_export()[0].status.value == "success"
    finally:
        screen.shutdown()
        assert directory_snapshot(directory) == before
