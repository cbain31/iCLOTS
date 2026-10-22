"""Video workflow parameters and preview backed by application services."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QSpinBox

from iclotspython.application.errors import ApplicationError, RequestValidationError
from iclotspython.application.velocity import VelocityRequest, run_velocity
from iclotspython.application.video_input import VideoInput, preview_video

from .image_loader import LoadedImages
from .workflow_screen import WorkflowScreen


class VelocityScreen(WorkflowScreen):
    workflow_title = "Velocity Profiling"
    workflow_description = "Choose one video or a clearly labeled synthetic demonstration. Set the scientific acquisition rate explicitly; decoding and analysis run in a background worker."
    service = staticmethod(run_velocity)

    def __init__(self):
        self.video_path = None
        super().__init__()
        self.add_button.setText("Choose video…")
        self.remove_button.hide()
        self.interval_spin.hide()
        self.convention_combo.hide()
        for checkbox, spin in self.channel_widgets.values():
            checkbox.parentWidget().hide()

    def _build_controls(self):
        scroll = super()._build_controls()
        group = QGroupBox("Velocity parameters (legacy defaults)")
        form = QFormLayout(group)
        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setDecimals(6)
        self.fps_spin.setRange(0, 1000000)
        self.fps_spin.setValue(1)
        self.fps_spin.setToolTip("Scientific acquisition rate; playback metadata is not substituted.")
        form.addRow("Acquisition rate (frames/s)", self.fps_spin)
        self.fps_spin.valueChanged.connect(self._material_changed)
        self.video_parameters = {}
        for name, label, default in self.parameter_definitions():
            spin = QSpinBox()
            spin.setRange(0, 1000000)
            spin.setValue(default)
            spin.setObjectName(name)
            spin.valueChanged.connect(self._material_changed)
            form.addRow(label, spin)
            self.video_parameters[name] = spin
        scroll.widget().layout().insertWidget(2, group)
        return scroll

    def parameter_definitions(self):
        return (("bins", "Profile bins", 7), ("corners", "Max. corners", 500),
                ("block_size", "Block size (pixels)", 5), ("window_x", "Window x (pixels)", 50), ("window_y", "Window y (pixels)", 20))

    def add_images(self, checked=False, paths=None):
        if paths is None:
            path, _ = QFileDialog.getOpenFileName(self, "Choose a video", "", "Videos (*.avi *.mp4 *.mov *.m4v *.mkv)")
            paths = [path] if path else []
        if not paths:
            return
        if len(paths) != 1:
            self._show_inline_error("Choose exactly one video.", "Run independent videos separately.")
            return
        try:
            frame = preview_video(str(paths[0]))
        except ApplicationError as exc:
            self._show_inline_error(exc.user_message, exc.detail)
            return
        frame.setflags(write=False)
        self.video_path = str(Path(paths[0]).resolve())
        self._set_loaded(LoadedImages((frame,), (Path(paths[0]).stem,), (self.video_path,), frame.shape[1], frame.shape[0]))
        self.input_summary.setText(f"{Path(paths[0]).name} • preview of first frame • video streams during analysis")

    def video_input(self):
        if self._loaded is None:
            raise RequestValidationError("no_video", "Choose a video or load a synthetic demo.", "No video input.")
        return VideoInput(path=self.video_path) if self.video_path else VideoInput(frames_rgb=self._loaded.frames_rgb)

    def build_request(self):
        return VelocityRequest(self.video_input(), self.calibration_spin.value(), self.fps_spin.value(),
            **{name: spin.value() for name, spin in self.video_parameters.items()}, roi=self.region())

    def load_demo(self):
        from .video_demo import moving_video_demo

        self.video_path = None
        frames = moving_video_demo()
        self._set_loaded(LoadedImages(frames, tuple(f"synthetic frame {i}" for i in range(len(frames))),
            ("synthetic://moving-particles",), frames[0].shape[1], frames[0].shape[0], True))

    def clear_inputs(self):
        self.video_path = None
        super().clear_inputs()
