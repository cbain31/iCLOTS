"""First modern workflow screen: ROI accumulation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from iclotspython.application import (
    ChannelConvention,
    ColorChannel,
    ROIAccumulationRequest,
    WorkflowMetadata,
)
from iclotspython.application.errors import ApplicationError, RequestValidationError
from iclotspython.application.validation import validate_roi_accumulation_request
from iclotspython.output import (
    ExportFormat,
    ExportRequest,
    FailurePolicy,
    ManifestStatus,
    OverwritePolicy,
    PlotRequest,
    export_roi_data,
    render_roi_plot,
    suggest_export_filename,
    suggest_plot_filename,
)
from iclotspython.output.errors import OutputServiceError
from iclotspython.presentation import ROIAccumulationResult, roi_table

from .demo import create_synthetic_demo
from .image_loader import (
    ImageLoadingError,
    LoadedImages,
    SUPPORTED_IMAGE_SUFFIXES,
    load_image_files,
)
from .plot_canvas import ROIPlotCanvas
from .table_model import ResultTableModel
from .workers import AnalysisWorker


class ROIAccumulationScreen(QWidget):
    """End-to-end ROI workflow using Phase 3A and Phase 3B boundaries."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("roi_accumulation_screen")
        self._loaded: LoadedImages | None = None
        self.result: ROIAccumulationResult | None = None
        self._thread: QThread | None = None
        self._worker: AnalysisWorker | None = None
        self._build_ui()
        self._connect_material_changes()
        self._update_input_state()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        heading = QLabel("ROI Accumulation")
        heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        description = QLabel(
            "Load an ordered same-field image sequence or use the deterministic "
            "synthetic demonstration. Calculations use the tested headless core."
        )
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("roi_workspace_splitter")
        splitter.addWidget(self._build_controls())
        splitter.addWidget(self._build_results())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

    def _build_controls(self) -> QWidget:
        content = QWidget()
        controls = QVBoxLayout(content)

        input_group = QGroupBox("1. Input images")
        input_layout = QVBoxLayout(input_group)
        button_row = QHBoxLayout()
        self.add_button = QPushButton("Add images…")
        self.add_button.setObjectName("add_images_button")
        self.remove_button = QPushButton("Remove selected")
        self.remove_button.setObjectName("remove_images_button")
        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("clear_inputs_button")
        self.demo_button = QPushButton("Load synthetic demo")
        self.demo_button.setObjectName("load_demo_button")
        for button in (
            self.add_button,
            self.remove_button,
            self.clear_button,
            self.demo_button,
        ):
            button_row.addWidget(button)
        input_layout.addLayout(button_row)
        self.image_list = QListWidget()
        self.image_list.setObjectName("ordered_image_list")
        self.image_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        input_layout.addWidget(self.image_list)
        self.input_summary = QLabel("No images loaded")
        self.input_summary.setObjectName("image_summary")
        input_layout.addWidget(self.input_summary)

        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_label = QLabel("No preview")
        self.preview_label.setObjectName("image_preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(280, 180)
        self.preview_label.setStyleSheet("border: 1px solid palette(mid);")
        self.preview_details = QLabel("Select an image to inspect its name and dimensions.")
        self.preview_details.setObjectName("preview_details")
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_details)

        parameter_group = QGroupBox("2. Parameters")
        parameter_layout = QFormLayout(parameter_group)
        self.convention_combo = QComboBox()
        self.convention_combo.setObjectName("channel_convention")
        self.convention_combo.addItems(["RGB", "BGR"])
        self.convention_combo.setToolTip(
            "Explicit array channel order. Qt-loaded images are normalized to your selection."
        )
        parameter_layout.addRow("Channel convention", self.convention_combo)

        self.channel_widgets = {}
        for channel, display in (
            (ColorChannel.RED, "Red"),
            (ColorChannel.GREEN, "Green"),
            (ColorChannel.BLUE, "Blue"),
        ):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            checkbox = QCheckBox(display)
            checkbox.setObjectName(f"{channel.value}_channel_checkbox")
            threshold = QSpinBox()
            threshold.setObjectName(f"{channel.value}_threshold")
            threshold.setRange(0, 255)
            threshold.setValue(50)
            threshold.setSuffix(" a.u.")
            threshold.setEnabled(False)
            threshold.setToolTip(
                "Strict threshold: only values greater than this setting count."
            )
            checkbox.toggled.connect(threshold.setEnabled)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(threshold, 1)
            parameter_layout.addRow(f"{display} channel", row)
            self.channel_widgets[channel] = (checkbox, threshold)

        self.calibration_spin = QDoubleSpinBox()
        self.calibration_spin.setObjectName("calibration_spin")
        self.calibration_spin.setRange(0.0, 1000000.0)
        self.calibration_spin.setDecimals(6)
        self.calibration_spin.setValue(1.0)
        self.calibration_spin.setSuffix(" µm/pixel")
        parameter_layout.addRow("Calibration", self.calibration_spin)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setObjectName("time_interval_spin")
        self.interval_spin.setRange(0.000001, 1000000.0)
        self.interval_spin.setDecimals(6)
        self.interval_spin.setValue(1.0)
        self.interval_spin.setSuffix(" timepoint")
        self.interval_spin.setToolTip(
            "Observed frames use interval, 2×interval, … after the compatibility baseline."
        )
        parameter_layout.addRow("Frame interval", self.interval_spin)

        run_group = QGroupBox("3. Run")
        run_layout = QVBoxLayout(run_group)
        run_buttons = QHBoxLayout()
        self.run_button = QPushButton("Run analysis")
        self.run_button.setObjectName("run_analysis_button")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancel_analysis_button")
        self.cancel_button.setEnabled(False)
        self.clear_result_button = QPushButton("Clear results")
        self.clear_result_button.setObjectName("clear_results_button")
        run_buttons.addWidget(self.run_button)
        run_buttons.addWidget(self.cancel_button)
        run_buttons.addWidget(self.clear_result_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("analysis_progress")
        self.progress_bar.setRange(0, 100)
        self.progress_message = QLabel("Ready")
        self.progress_message.setObjectName("progress_message")
        self.validation_feedback = QLabel("")
        self.validation_feedback.setObjectName("validation_feedback")
        self.validation_feedback.setWordWrap(True)
        run_layout.addLayout(run_buttons)
        run_layout.addWidget(self.progress_bar)
        run_layout.addWidget(self.progress_message)
        run_layout.addWidget(self.validation_feedback)

        controls.addWidget(input_group)
        controls.addWidget(preview_group)
        controls.addWidget(parameter_group)
        controls.addWidget(run_group)
        controls.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("roi_controls_scroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setMinimumWidth(390)
        return scroll

    def _build_results(self) -> QWidget:
        self.result_tabs = QTabWidget()
        self.result_tabs.setObjectName("result_tabs")

        self.summary_text = QPlainTextEdit()
        self.summary_text.setObjectName("summary_result")
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlainText("No result")
        self.result_tabs.addTab(self.summary_text, "Summary")

        self.table_model = ResultTableModel(parent=self)
        self.table_view = QTableView()
        self.table_view.setObjectName("result_table")
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        self.result_tabs.addTab(self.table_view, "Data table")

        self.plot_canvas = ROIPlotCanvas()
        self.plot_canvas.setObjectName("result_plot")
        self.result_tabs.addTab(self.plot_canvas, "Plot")

        self.warning_text = QPlainTextEdit()
        self.warning_text.setObjectName("warnings_provenance")
        self.warning_text.setReadOnly(True)
        self.warning_text.setPlainText("No warnings or provenance")
        self.result_tabs.addTab(self.warning_text, "Warnings & provenance")

        export_widget = QWidget()
        export_layout = QVBoxLayout(export_widget)
        destination_row = QHBoxLayout()
        self.destination_edit = QLineEdit()
        self.destination_edit.setObjectName("export_destination")
        self.destination_button = QPushButton("Choose destination…")
        self.destination_button.setObjectName("choose_export_destination")
        destination_row.addWidget(self.destination_edit, 1)
        destination_row.addWidget(self.destination_button)
        export_layout.addLayout(destination_row)
        format_row = QHBoxLayout()
        self.export_png = QCheckBox("PNG plot")
        self.export_png.setObjectName("export_png")
        self.export_png.setChecked(True)
        self.export_csv = QCheckBox("CSV data")
        self.export_csv.setObjectName("export_csv")
        self.export_csv.setChecked(True)
        self.export_xlsx = QCheckBox("XLSX workbook")
        self.export_xlsx.setObjectName("export_xlsx")
        for checkbox in (self.export_png, self.export_csv, self.export_xlsx):
            format_row.addWidget(checkbox)
        export_layout.addLayout(format_row)
        self.export_button = QPushButton("Export selected outputs")
        self.export_button.setObjectName("export_button")
        self.export_button.setEnabled(False)
        self.export_status = QPlainTextEdit()
        self.export_status.setObjectName("export_manifest")
        self.export_status.setReadOnly(True)
        self.export_status.setPlainText("Run an analysis before exporting.")
        export_layout.addWidget(self.export_button)
        export_layout.addWidget(self.export_status, 1)
        self.result_tabs.addTab(export_widget, "Export")
        return self.result_tabs

    def _connect_material_changes(self) -> None:
        self.add_button.clicked.connect(self.add_images)
        self.remove_button.clicked.connect(self.remove_selected_images)
        self.clear_button.clicked.connect(self.clear_inputs)
        self.demo_button.clicked.connect(self.load_demo)
        self.image_list.currentRowChanged.connect(self._update_preview)
        self.run_button.clicked.connect(self.start_analysis)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        self.clear_result_button.clicked.connect(self.clear_result)
        self.destination_button.clicked.connect(self.choose_destination)
        self.export_button.clicked.connect(self._export_clicked)
        self.convention_combo.currentTextChanged.connect(self._material_changed)
        self.calibration_spin.valueChanged.connect(self._material_changed)
        self.interval_spin.valueChanged.connect(self._material_changed)
        for checkbox, threshold in self.channel_widgets.values():
            checkbox.toggled.connect(self._material_changed)
            threshold.valueChanged.connect(self._material_changed)

    def add_images(self, checked=False, paths=None) -> None:
        if paths is None:
            pattern = " ".join(f"*{suffix}" for suffix in SUPPORTED_IMAGE_SUFFIXES)
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Add ROI images in analysis order",
                "",
                f"Images ({pattern})",
            )
        if not paths:
            return
        try:
            incoming = load_image_files(tuple(paths))
            if self._loaded is not None:
                if (incoming.width, incoming.height) != (
                    self._loaded.width,
                    self._loaded.height,
                ):
                    raise ImageLoadingError(
                        "inconsistent_image_dimensions",
                        "Added images must match the current dimensions.",
                        f"Received {incoming.width}×{incoming.height}; expected "
                        f"{self._loaded.width}×{self._loaded.height}.",
                    )
                incoming = LoadedImages(
                    frames_rgb=self._loaded.frames_rgb + incoming.frames_rgb,
                    labels=self._loaded.labels + incoming.labels,
                    source_identifiers=(
                        self._loaded.source_identifiers
                        + incoming.source_identifiers
                    ),
                    width=incoming.width,
                    height=incoming.height,
                )
            self._set_loaded(incoming)
        except ImageLoadingError as exc:
            self._show_inline_error(exc.user_message, exc.detail)

    def load_demo(self) -> None:
        self.convention_combo.setCurrentText("RGB")
        self.channel_widgets[ColorChannel.RED][0].setChecked(True)
        self.channel_widgets[ColorChannel.GREEN][0].setChecked(False)
        self.channel_widgets[ColorChannel.BLUE][0].setChecked(False)
        self.channel_widgets[ColorChannel.RED][1].setValue(50)
        self.calibration_spin.setValue(1.0)
        self.interval_spin.setValue(1.0)
        self._set_loaded(create_synthetic_demo())
        self.progress_message.setText("Synthetic demonstration loaded")

    def _set_loaded(self, loaded: LoadedImages) -> None:
        self._loaded = loaded
        self.image_list.clear()
        self.image_list.addItems(loaded.labels)
        self.image_list.setCurrentRow(0)
        self._update_input_state()
        self.invalidate_result("Inputs changed; run analysis to refresh results.")

    def remove_selected_images(self) -> None:
        if self._loaded is None:
            return
        removed = {index.row() for index in self.image_list.selectedIndexes()}
        if not removed:
            return
        keep = [index for index in range(len(self._loaded.frames_rgb)) if index not in removed]
        if not keep:
            self.clear_inputs()
            return
        self._set_loaded(
            LoadedImages(
                frames_rgb=tuple(self._loaded.frames_rgb[index] for index in keep),
                labels=tuple(self._loaded.labels[index] for index in keep),
                source_identifiers=tuple(
                    self._loaded.source_identifiers[index] for index in keep
                ),
                width=self._loaded.width,
                height=self._loaded.height,
                synthetic=self._loaded.synthetic,
            )
        )

    def clear_inputs(self) -> None:
        self._loaded = None
        self.image_list.clear()
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("No preview")
        self.preview_details.setText(
            "Select an image to inspect its name and dimensions."
        )
        self._update_input_state()
        self.invalidate_result("Inputs cleared.")

    def _update_input_state(self) -> None:
        if self._loaded is None:
            self.input_summary.setText("No images loaded")
            self.remove_button.setEnabled(False)
        else:
            source = "synthetic demo" if self._loaded.synthetic else "loaded files"
            self.input_summary.setText(
                f"{len(self._loaded.frames_rgb)} images • "
                f"{self._loaded.width}×{self._loaded.height} RGB • {source}"
            )
            self.remove_button.setEnabled(True)

    def _update_preview(self, row: int) -> None:
        if self._loaded is None or row < 0 or row >= len(self._loaded.frames_rgb):
            return
        frame = self._loaded.frames_rgb[row]
        image = QImage(
            frame.data,
            self._loaded.width,
            self._loaded.height,
            self._loaded.width * 3,
            QImage.Format.Format_RGB888,
        ).copy()
        pixmap = QPixmap.fromImage(image).scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setText("")
        self.preview_label.setPixmap(pixmap)
        self.preview_details.setText(
            f"{self._loaded.labels[row]} • "
            f"{self._loaded.width}×{self._loaded.height} pixels"
        )

    def _material_changed(self, *args) -> None:
        if self.result is not None:
            self.invalidate_result(
                "Parameters changed; previous results were invalidated."
            )

    def build_request(self) -> ROIAccumulationRequest:
        if self._loaded is None:
            raise RequestValidationError(
                "no_frames",
                "Load one or more images before running.",
                "The GUI has no in-memory frames.",
                field="frames",
            )
        selected = tuple(
            channel
            for channel, (checkbox, _) in self.channel_widgets.items()
            if checkbox.isChecked()
        )
        if not selected:
            raise RequestValidationError(
                "no_selected_channels",
                "Select at least one channel.",
                "No ROI channel checkbox is selected.",
                field="selected_channels",
            )
        convention = ChannelConvention(self.convention_combo.currentText())
        if convention is ChannelConvention.RGB:
            frames = self._loaded.frames_rgb
        else:
            converted = []
            for frame in self._loaded.frames_rgb:
                bgr = frame[:, :, ::-1].copy()
                bgr.setflags(write=False)
                converted.append(bgr)
            frames = tuple(converted)
        thresholds = {
            channel: float(self.channel_widgets[channel][1].value())
            for channel in selected
        }
        interval = self.interval_spin.value()
        times = tuple(
            interval * (index + 1)
            for index in range(len(self._loaded.frames_rgb))
        )
        request = ROIAccumulationRequest(
            frames=frames,
            selected_channels=selected,
            thresholds=thresholds,
            micrometres_per_pixel=self.calibration_spin.value(),
            channel_convention=convention,
            frame_labels=self._loaded.labels,
            time_values=times,
            metadata=WorkflowMetadata(
                source_identifiers=self._loaded.source_identifiers,
                attributes=(
                    (
                        "source_type",
                        "synthetic_demo" if self._loaded.synthetic else "image_files",
                    ),
                ),
                suggested_export_stem=(
                    "synthetic_roi_demo"
                    if self._loaded.synthetic
                    else self._loaded.labels[0]
                ),
            ),
        )
        validate_roi_accumulation_request(request)
        return request

    def start_analysis(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            self._show_inline_error(
                "Analysis is already running.",
                "Overlapping runs are disabled.",
            )
            return
        try:
            request = self.build_request()
        except ApplicationError as exc:
            self._show_inline_error(exc.user_message, exc.detail)
            return
        self.validation_feedback.setText("")
        self.progress_bar.setValue(0)
        self.progress_message.setText("Starting analysis…")
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.export_button.setEnabled(False)

        thread = QThread(self)
        worker = AnalysisWorker(request)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.succeeded.connect(self._on_success)
        worker.failed.connect(self._on_failure)
        worker.cancelled.connect(self._on_cancelled)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    def cancel_analysis(self) -> None:
        if self._worker is not None:
            self._worker.request_cancellation()
            self.progress_message.setText("Cancellation requested…")

    def _on_progress(self, event) -> None:
        self.progress_bar.setValue(round(event.fraction_complete * 100))
        self.progress_message.setText(event.message)

    def _on_success(self, result: ROIAccumulationResult) -> None:
        self._apply_result(result)
        self.progress_bar.setValue(100)
        self.progress_message.setText("Analysis complete")

    def _on_failure(self, error) -> None:
        if isinstance(error, ApplicationError):
            self._show_inline_error(error.user_message, error.detail)
        else:
            self._show_inline_error(
                "Analysis failed.",
                f"{type(error).__name__}: {error}",
            )
        self.progress_message.setText("Analysis failed")

    def _on_cancelled(self, error) -> None:
        self.progress_message.setText("Analysis cancelled")
        self.validation_feedback.setText(
            getattr(error, "user_message", "The analysis was cancelled.")
        )

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.export_button.setEnabled(self.result is not None)

    def _apply_result(self, result: ROIAccumulationResult) -> None:
        self.result = result
        summary_lines = [
            f"Workflow: {result.workflow_id}",
            f"Observed frames: {result.provenance.frame_count}",
            f"Channels: {', '.join(result.provenance.selected_channels)}",
            f"Calibration: {result.provenance.micrometres_per_pixel:g} µm/pixel",
            "",
        ]
        for channel in result.channels:
            summary_lines.extend(
                [
                    f"{channel.channel.title()} final area: "
                    f"{channel.area_micrometres_squared[-1]:g} µm²",
                    f"{channel.channel.title()} net change from prior frame: "
                    f"{channel.accumulation_micrometres_squared[-1]:g} "
                    "µm²/timepoint",
                ]
            )
        self.summary_text.setPlainText("\n".join(summary_lines))
        self.table_model.set_table(roi_table(result))
        self.table_view.resizeColumnsToContents()
        self.plot_canvas.set_result(result)
        warning_lines = ["Warnings"]
        if result.warnings:
            for warning in result.warnings:
                warning_lines.append(
                    f"• [{warning.code.value}] {warning.message}\n  {warning.detail}"
                )
        else:
            warning_lines.append("None")
        warning_lines.extend(
            [
                "",
                "Provenance",
                f"Workflow contract: {result.provenance.workflow_contract_version}",
                f"Application version: {result.provenance.application_version}",
                f"Scientific core: {result.provenance.scientific_core_module}",
                f"Convention: {result.provenance.channel_convention}",
                f"Thresholds: {result.provenance.thresholds}",
                f"Sources: {result.provenance.source_identifiers}",
            ]
        )
        self.warning_text.setPlainText("\n".join(warning_lines))
        self.export_status.setPlainText("Result ready for export.")
        self.export_button.setEnabled(
            self._thread is None or not self._thread.isRunning()
        )

    def invalidate_result(self, reason: str) -> None:
        self.result = None
        self.summary_text.setPlainText("No result")
        self.table_model.set_table(roi_table_placeholder())
        self.plot_canvas.clear_result()
        self.warning_text.setPlainText("No warnings or provenance")
        self.export_status.setPlainText("Run an analysis before exporting.")
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.validation_feedback.setText(reason)

    def clear_result(self) -> None:
        self.invalidate_result("Results cleared; inputs and parameters were preserved.")

    def _show_inline_error(self, message: str, detail: str) -> None:
        self.validation_feedback.setText(f"{message}\n{detail}")

    def choose_destination(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Choose export destination"
        )
        if directory:
            self.destination_edit.setText(directory)

    def _export_clicked(self) -> None:
        if self.result is None:
            return
        destination_text = self.destination_edit.text().strip()
        if not destination_text:
            self.export_status.setPlainText("Choose an export destination.")
            return
        destination = Path(destination_text)
        targets = []
        if self.export_png.isChecked():
            targets.append(destination / suggest_plot_filename(self.result))
        for selected, format in (
            (self.export_csv.isChecked(), ExportFormat.CSV),
            (self.export_xlsx.isChecked(), ExportFormat.EXCEL),
        ):
            if selected:
                targets.append(
                    destination / suggest_export_filename(self.result, format)
                )
        existing = [path.name for path in targets if path.exists()]
        overwrite = False
        if existing:
            answer = QMessageBox.question(
                self,
                "Replace existing outputs?",
                "The following files already exist:\n"
                + "\n".join(existing)
                + "\n\nReplace them explicitly?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            overwrite = answer is QMessageBox.StandardButton.Yes
        self.perform_export(overwrite=overwrite)

    def perform_export(self, overwrite: bool = False):
        if self.result is None:
            self.export_status.setPlainText("No result is available for export.")
            return ()
        destination_text = self.destination_edit.text().strip()
        if not destination_text:
            self.export_status.setPlainText("Choose an export destination.")
            return ()
        overwrite_policy = (
            OverwritePolicy.REPLACE
            if overwrite
            else OverwritePolicy.FAIL_IF_EXISTS
        )
        manifests = []
        try:
            if self.export_png.isChecked():
                manifests.append(
                    render_roi_plot(
                        PlotRequest(
                            result=self.result,
                            destination_directory=destination_text,
                            overwrite=overwrite_policy,
                        )
                    )
                )
            formats = []
            if self.export_csv.isChecked():
                formats.append(ExportFormat.CSV)
            if self.export_xlsx.isChecked():
                formats.append(ExportFormat.EXCEL)
            if formats:
                manifests.append(
                    export_roi_data(
                        ExportRequest(
                            result=self.result,
                            destination_directory=destination_text,
                            formats=tuple(formats),
                            overwrite=overwrite_policy,
                            failure_policy=FailurePolicy.CONTINUE,
                        )
                    )
                )
        except OutputServiceError as exc:
            self.export_status.setPlainText(
                f"Export request failed [{exc.code}]\n"
                f"{exc.user_message}\n{exc.detail}"
            )
            return ()
        if not manifests:
            self.export_status.setPlainText("Select at least one output format.")
            return ()
        self._display_manifests(manifests)
        return tuple(manifests)

    def _display_manifests(self, manifests) -> None:
        lines = []
        for manifest in manifests:
            lines.append(f"Manifest: {manifest.status.value.upper()}")
            for record in manifest.files:
                lines.append(
                    f"• {record.format.upper()} — {record.status.value}: {record.path}"
                )
                for issue in record.issues:
                    lines.append(f"  [{issue.code}] {issue.message}")
        overall = {
            manifest.status for manifest in manifests
        }
        if overall == {ManifestStatus.SUCCESS}:
            lines.insert(0, "Export completed successfully.")
        elif ManifestStatus.PARTIAL in overall or (
            ManifestStatus.SUCCESS in overall and ManifestStatus.FAILED in overall
        ):
            lines.insert(0, "Export completed with partial success.")
        else:
            lines.insert(0, "Export failed.")
        self.export_status.setPlainText("\n".join(lines))

    def shutdown(self) -> None:
        if self._worker is not None:
            self._worker.request_cancellation()
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)


def roi_table_placeholder():
    """Avoid a mutable GUI-only empty-table representation."""
    from iclotspython.presentation.models import TableData

    return TableData(columns=(), rows=())
