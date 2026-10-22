"""Opt-in local clustering inputs; feature choices are operability checks."""

import pytest
from PySide6.QtCore import Qt

from iclotspython.application.clustering import load_clustering_workbooks
from iclotspython.application.errors import RequestValidationError
from iclotspython.gui.clustering_screen import ClusteringScreen
from tests.gui.test_gui_roi_workflow import _process_until
from tests.support.local_test_data import directory_snapshot
from tests.support.output_factory import workspace_output_directory

pytestmark = [pytest.mark.local_data, pytest.mark.integration, pytest.mark.gui]


@pytest.mark.parametrize("folder", ["Machine_learning_artifical_data", "Machine_learning_set2"])
def test_local_clustering_workbooks(local_test_data_root, qt_app, folder):
    directory = local_test_data_root / folder
    if not directory.is_dir():
        pytest.skip("Selected clustering dataset absent")
    paths = sorted(directory.glob("*.xlsx"))
    if not paths:
        pytest.skip("No clustering workbook available")
    before = directory_snapshot(directory)
    screen = ClusteringScreen()
    try:
        screen.choose_workbooks(paths=[str(path) for path in paths])
        assert screen.feature_list.count() >= 2, screen.validation_feedback.text()
        for i in range(2):
            screen.feature_list.item(i).setCheckState(Qt.CheckState.Checked)
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None, timeout=120)
        assert screen.result is not None, screen.validation_feedback.text()
        assert screen.result.table("Labeled data").rows
        with workspace_output_directory() as output:
            screen.destination_edit.setText(str(output))
            screen.export_xlsx.setChecked(True)
            assert screen.perform_export()[0].status.value == "success"
    finally:
        screen.shutdown()
        assert directory_snapshot(directory) == before


def test_known_multisheet_input_is_rejected(local_test_data_root):
    path = local_test_data_root / "Machine_learning_set1" / "Error_test.xlsx"
    if not path.is_file():
        pytest.skip("Selected malformed workbook absent")
    before = directory_snapshot(path.parent)
    with pytest.raises(RequestValidationError, match="exactly one worksheet"):
        load_clustering_workbooks((str(path),))
    assert directory_snapshot(path.parent) == before
