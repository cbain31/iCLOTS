"""Static adhesion controls shared by the three legacy image workflows."""

from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox

from iclotspython.application.adhesion import AdhesionRequest, run_adhesion
from iclotspython.application.contracts import ROIAccumulationRequest, WorkflowMetadata
from iclotspython.application.errors import RequestValidationError

from .workflow_screen import WorkflowScreen


class AdhesionScreen(WorkflowScreen):
    service = staticmethod(run_adhesion)
    requires_same_dimensions = False
    workflow_description = "Analyze independent images, which may differ in size. The legacy measurement definitions and strict thresholds are preserved."

    def __init__(self, mode):
        self.mode = mode
        self.workflow_title = {"brightfield": "Brightfield Adhesion", "fluorescence": "Fluorescence Adhesion", "filopodia": "Filopodia"}[mode]
        super().__init__()
        self.interval_spin.hide()
        self.convention_combo.hide()
        for checkbox, spin in self.channel_widgets.values():
            checkbox.parentWidget().hide()

    def _build_controls(self):
        scroll = super()._build_controls()
        group = QGroupBox("Adhesion parameters (legacy defaults)")
        form = QFormLayout(group)
        self.primary_combo = QComboBox()
        self.primary_combo.addItems(["grayscale", "red", "green", "blue"])
        self.functional_combo = QComboBox()
        self.functional_combo.addItems(["none", "red", "green", "blue"])
        self.primary_combo.currentTextChanged.connect(self._material_changed)
        self.functional_combo.currentTextChanged.connect(self._material_changed)
        if self.mode != "brightfield":
            form.addRow("Primary channel", self.primary_combo)
        if self.mode == "fluorescence":
            form.addRow("Functional channel", self.functional_combo)
        self.adhesion_parameters = {}
        definitions = (("diameter", "Cell diameter (odd pixels)", 15, 10001), ("minmass", "Minimum mass (a.u.)", 1000, 1E9)) if self.mode == "brightfield" else (
            ("minarea", "Min. area, exclusive (pixels)", 0, 1E9), ("maxarea", "Max. area, exclusive (pixels)", 10000, 1E9),
            ("primary_threshold", "Primary threshold (a.u.)", 50, 255),
        )
        if self.mode == "fluorescence":
            definitions += (("functional_threshold", "Functional threshold (a.u.)", 30, 255),)
        if self.mode == "filopodia":
            definitions += (("harris_k", "Harris k", 0.2, 1), ("threshold_rel", "Relative corner threshold", 0.5, 1), ("min_distance", "Min. corner distance (pixels)", 5, 10000))
        for name, label, default, maximum in definitions:
            spin = QDoubleSpinBox()
            spin.setDecimals(4 if name in {"harris_k", "threshold_rel"} else 0)
            spin.setRange(0, maximum)
            spin.setValue(default)
            spin.valueChanged.connect(self._material_changed)
            form.addRow(label, spin)
            self.adhesion_parameters[name] = spin
        self.invert_checkbox = QCheckBox("Dark cells on a light background")
        self.invert_checkbox.setChecked(True)
        self.invert_checkbox.toggled.connect(self._material_changed)
        if self.mode == "brightfield":
            form.addRow(self.invert_checkbox)
        scroll.widget().layout().insertWidget(2, group)
        return scroll

    def build_request(self):
        if self._loaded is None:
            raise RequestValidationError("no_images", "Load one or more independent images.", "No static images loaded.")
        images = ROIAccumulationRequest(self._loaded.frames_rgb, ("red",), {"red": 50}, self.calibration_spin.value(), "RGB",
            frame_labels=self._loaded.labels, metadata=WorkflowMetadata(source_identifiers=self._loaded.source_identifiers,
            suggested_export_stem="synthetic_adhesion" if self._loaded.synthetic else self._loaded.labels[0]))
        params = {name: spin.value() for name, spin in self.adhesion_parameters.items()}
        for name in ("diameter", "min_distance"):
            if name in params:
                params[name] = int(params[name])
        return AdhesionRequest(images, self.mode, self.primary_combo.currentText(), self.functional_combo.currentText(),
            **params, invert=self.invert_checkbox.isChecked(), roi=self.region())
