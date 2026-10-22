"""Clustering feature selection, real worker and multi-table exports."""

import pytest

from iclotspython.gui.clustering_screen import ClusteringScreen
from tests.gui.test_gui_roi_workflow import _process_until

pytestmark = [pytest.mark.unit, pytest.mark.gui]


def test_clustering_gui_executes_and_exports(qt_app, tmp_path):
    screen = ClusteringScreen()
    try:
        screen.load_demo()
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None, timeout=40)
        assert screen.result is not None, screen.validation_feedback.text()
        assert len(screen.result.table("Labeled data").rows) == 12
        screen.table_selector.setCurrentText("Counts")
        assert screen.table_model.rowCount() > 0
        screen.destination_edit.setText(str(tmp_path))
        screen.export_xlsx.setChecked(True)
        assert screen.perform_export()[0].status.value == "success"
        screen.clusters_spin.setValue(3)
        assert screen.result is None
    finally:
        screen.shutdown()
