"""Shared Qt client for multi-table application services; no analysis math."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QGroupBox, QLabel, QMessageBox, QSpinBox, QVBoxLayout, QWidget

from iclotspython.application.common import Region
from iclotspython.application.contracts import ColorChannel
from iclotspython.application.multiscale import MultiscaleRequest, run_multiscale
from iclotspython.output import OverwritePolicy
from iclotspython.output.errors import OutputServiceError
from iclotspython.output.workflows import export_workflow, output_targets, result_report

from .roi_screen import ROIAccumulationScreen
from .workers import AnalysisWorker


class WorkflowScreen(ROIAccumulationScreen):
    """Reuse ordered image inputs, worker lifecycle, tables and export feedback."""

    def _build_controls(self):
        scroll = super()._build_controls()
        group = QGroupBox("Region of interest")
        form = QFormLayout(group)
        self.crop_enabled = QCheckBox("Crop to explicit rectangle")
        form.addRow(self.crop_enabled)
        self.roi_spins = {}
        for key in ("x", "y", "width", "height"):
            spin = QSpinBox()
            spin.setRange(0, 1000000)
            spin.setObjectName(f"roi_{key}")
            spin.valueChanged.connect(self._material_changed)
            form.addRow(key.title() + " (pixels)", spin)
            self.roi_spins[key] = spin
        self.crop_enabled.toggled.connect(self._material_changed)
        scroll.widget().layout().insertWidget(2, group)
        return scroll

    def _build_results(self):
        tabs = super()._build_results()
        self.table_selector = QComboBox()
        self.table_selector.currentTextChanged.connect(self._select_table)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Result table"))
        layout.addWidget(self.table_selector)
        layout.addWidget(tabs, 1)
        return container

    def region(self):
        if self.crop_enabled.isChecked():
            return Region(**{key: spin.value() for key, spin in self.roi_spins.items()})
        return None

    def create_worker(self, request):
        return AnalysisWorker(request, self.service)

    def _apply_result(self, result):
        import json

        self.result = result
        self.table_selector.clear()
        self.table_selector.addItems([t.name for t in result.tables])
        self._select_table(self.table_selector.currentText())
        self.summary_text.setPlainText("\n".join(
            [f"Workflow: {result.workflow_id}"] + [f"{t.name}: {len(t.data.rows)} rows" for t in result.tables]
        ))
        self.warning_text.setPlainText(json.dumps(result_report(result), indent=2, ensure_ascii=False))
        self.plot_canvas.set_result(result)
        self.export_status.setPlainText("Result ready. Exports include a JSON reproducibility report.")

    def _select_table(self, name):
        if self.result is not None and name:
            self.table_model.set_table(self.result.table(name))
            self.table_view.resizeColumnsToContents()

    def selected_formats(self):
        return tuple(name for name, widget in (("csv", self.export_csv), ("xlsx", self.export_xlsx), ("png", self.export_png)) if widget.isChecked())

    def _export_clicked(self):
        if self.result is None:
            return
        destination = Path(self.destination_edit.text().strip())
        existing = [name for name, _, _ in output_targets(self.result, self.selected_formats()) if (destination / name).exists()]
        overwrite = False
        if existing:
            answer = QMessageBox.question(self, "Replace existing outputs?", "Replace these outputs?\n" + "\n".join(existing),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            overwrite = True
        self.perform_export(overwrite)

    def perform_export(self, overwrite=False):
        if self.result is None:
            return ()
        if not self.destination_edit.text().strip():
            self.export_status.setPlainText("Choose an export destination.")
            return ()
        try:
            manifest = export_workflow(self.result, self.destination_edit.text().strip(), self.selected_formats(),
                overwrite=OverwritePolicy.REPLACE if overwrite else OverwritePolicy.FAIL_IF_EXISTS)
        except OutputServiceError as exc:
            self.export_status.setPlainText(f"{exc.user_message}\n{exc.detail}")
            return ()
        self._display_manifests((manifest,))
        return (manifest,)


class MultiscaleScreen(WorkflowScreen):
    service = staticmethod(run_multiscale)

    def __init__(self, mode):
        self.mode = mode
        self.workflow_title = f"{mode.title()} Accumulation"
        super().__init__()
        self.interval_spin.setEnabled(mode == "device")
        if mode == "microchannel":
            for checkbox, spin in self.channel_widgets.values():
                checkbox.toggled.disconnect(spin.setEnabled)
                spin.setEnabled(True)
                spin.setToolTip("All channel thresholds define final-frame geometry, including unselected colors.")

    def build_request(self):
        images = super().build_request()
        images = replace(images, thresholds={c: float(spin.value()) for c, (_, spin) in self.channel_widgets.items()})
        return MultiscaleRequest(images, self.mode, self.region())
