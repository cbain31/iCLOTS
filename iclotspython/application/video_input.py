"""Explicit streaming video input, decoded without a GUI dependency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

from .common import Region, invalid
from .errors import RequestValidationError


@dataclass(frozen=True)
class VideoInput:
    path: str | None = None
    frames_rgb: Sequence | None = None
    source_identifier: str = "synthetic://video"


def iter_video_rgb(source: VideoInput, roi: Region | None = None):
    """Yield copied uint8 RGB frames in source order and always release capture."""
    if (source.path is None) == (source.frames_rgb is None):
        invalid("video", "Provide exactly one video path or in-memory RGB sequence.")
    capture = None
    expected = None
    count = 0
    try:
        if source.path is not None:
            import cv2

            path = Path(source.path)
            if not path.is_file():
                invalid("video", "The selected video file is unavailable.")
            capture = cv2.VideoCapture(str(path))
            if not capture.isOpened():
                invalid("video", "The selected video could not be opened by OpenCV.")
            declared_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

            def decoded():
                index = 0
                while True:
                    ok, bgr = capture.read()
                    if not ok:
                        if declared_frames > 0 and index < declared_frames:
                            invalid("video", f"Video decoding stopped at frame {index}; expected {declared_frames} frames. No partial result was published.")
                        break
                    index += 1
                    yield cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

            iterator = decoded()
        else:
            iterator = iter(source.frames_rgb)
        for frame in iterator:
            frame = np.asarray(frame)
            if frame.ndim != 3 or frame.shape[-1] != 3 or not frame.shape[0] or not frame.shape[1] or frame.dtype != np.uint8:
                invalid("video", "Video frames must be nonempty uint8 RGB arrays (height, width, 3).")
            if expected is None:
                expected = frame.shape
            elif frame.shape != expected:
                invalid("video", "All video frames must have identical dimensions.")
            if roi:
                ys, xs = roi.slices(frame.shape)
                frame = frame[ys, xs]
            count += 1
            yield np.ascontiguousarray(frame).copy()
        if count < 2:
            invalid("video", "At least two decoded frames are required for video analysis.")
    finally:
        if capture is not None:
            capture.release()


def preview_video(path):
    """Read a single frame for preview without retaining the capture handle."""
    iterator = iter_video_rgb(VideoInput(path=str(path)))
    try:
        return next(iterator)
    finally:
        iterator.close()


def source_name(source):
    return Path(source.path).stem if source.path else "synthetic_video"


def source_id(source):
    return source.path or source.source_identifier
