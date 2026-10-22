"""Explicit workbook/feature selection for the existing clustering workflow."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFileDialog, QLabel, QListWidget, QListWidgetItem, QProgressBar,
    QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget)

from iclotspython.application.clustering import ClusteringRequest, load_clustering_workbooks, numeric_features, run_clustering
from iclotspython.application.errors import ApplicationError, RequestValidationError
from iclotspython.presentation.models import TableData

from .workflow_screen import WorkflowScreen


class ClusteringScreen(WorkflowScreen):
    workflow_title = "Clustering"
    workflow_description = "Choose single-sheet XLSX inputs, select at least two numeric features, and set the cluster count. Features retain their input units; excluded rows and library settings are reported."
    service = staticmethod(run_clustering)

    def __init__(self):
        self.data = None
        self.sources = ()
        super().__init__()

    def _build_controls(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        self.add_button = QPushButton("Choose XLSX workbooks…")
        self.demo_button = QPushButton("Load synthetic clustering demo")
        self.input_summary = QLabel("No workbooks loaded")
        self.input_summary.setWordWrap(True)
        self.feature_list = QListWidget()
        self.feature_list.setObjectName("clustering_features")
        self.clusters_spin = QSpinBox()
        self.clusters_spin.setRange(2, 1000)
        self.clusters_spin.setValue(2)
        self.run_button = QPushButton("Run clustering")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.clear_result_button = QPushButton("Clear results")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_message = QLabel("Ready")
        self.validation_feedback = QLabel("")
        self.validation_feedback.setWordWrap(True)
        for widget in (self.add_button, self.demo_button, self.input_summary, QLabel("Select numerical features"), self.feature_list,
                       QLabel("Number of clusters"), self.clusters_spin, self.run_button, self.cancel_button, self.clear_result_button,
                       self.progress_bar, self.progress_message, self.validation_feedback):
            layout.addWidget(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _connect_material_changes(self):
        self.add_button.clicked.connect(self.choose_workbooks)
        self.demo_button.clicked.connect(self.load_demo)
        self.run_button.clicked.connect(self.start_analysis)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        self.clear_result_button.clicked.connect(self.clear_result)
        self.destination_button.clicked.connect(self.choose_destination)
        self.export_button.clicked.connect(self._export_clicked)
        self.feature_list.itemChanged.connect(self._material_changed)
        self.clusters_spin.valueChanged.connect(self._material_changed)

    def _update_input_state(self):
        pass

    def choose_workbooks(self, checked=False, paths=None):
        if paths is None:
            paths, _ = QFileDialog.getOpenFileNames(self, "Choose single-sheet workbooks", "", "Excel workbooks (*.xlsx)")
        if not paths:
            return
        try:
            data = load_clustering_workbooks(paths)
        except ApplicationError as exc:
            self._show_inline_error(exc.user_message, exc.detail)
            return
        self._set_data(data, tuple(map(str, paths)))

    def _set_data(self, data, sources):
        self.data, self.sources = data, sources
        self.feature_list.clear()
        for feature in numeric_features(data):
            item = QListWidgetItem(feature)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.feature_list.addItem(item)
        self.input_summary.setText(f"{len(sources)} input(s), {len(data.rows)} rows\n" + "\n".join(sources))
        self.invalidate_result("Choose features and run clustering.")

    def load_demo(self):
        rows = tuple(("synthetic", float(i % 3) + (10 if i >= 6 else 0), float(i % 2) + (12 if i >= 6 else 0)) for i in range(12))
        self._set_data(TableData(("Sample", "Area", "Texture"), rows), ("synthetic://clustering",))
        for i in range(self.feature_list.count()):
            self.feature_list.item(i).setCheckState(Qt.CheckState.Checked)

    def build_request(self):
        if self.data is None:
            raise RequestValidationError("no_workbooks", "Choose workbooks or a synthetic demo.", "No clustering input.")
        features = tuple(self.feature_list.item(i).text() for i in range(self.feature_list.count()) if self.feature_list.item(i).checkState() == Qt.CheckState.Checked)
        return ClusteringRequest(self.data, features, self.clusters_spin.value(), self.sources)
