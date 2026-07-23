"""Qt image-loading adapter for ROI accumulation requests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PySide6.QtGui import QImage, QImageReader


SUPPORTED_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


class ImageLoadingError(Exception):
    """Controlled, user-presentable image-loading failure."""

    def __init__(
        self,
        code: str,
        user_message: str,
        detail: str,
        path: str | None = None,
    ) -> None:
        super().__init__(user_message)
        self.code = code
        self.user_message = user_message
        self.detail = detail
        self.path = path


@dataclass(frozen=True)
class LoadedImages:
    """Read-only RGB arrays plus caller-visible source order."""

    frames_rgb: tuple[NDArray[np.uint8], ...]
    labels: tuple[str, ...]
    source_identifiers: tuple[str, ...]
    width: int
    height: int
    synthetic: bool = False


def qimage_to_rgb_array(image: QImage) -> NDArray[np.uint8]:
    """Copy a QImage into a tightly packed, read-only RGB array."""
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    height = converted.height()
    width = converted.width()
    raw = np.frombuffer(
        converted.bits(), dtype=np.uint8, count=converted.sizeInBytes()
    )
    rows = raw.reshape(height, converted.bytesPerLine())
    array = rows[:, : width * 3].reshape(height, width, 3).copy()
    array.setflags(write=False)
    return array


def load_image_files(paths: tuple[str, ...] | list[str]) -> LoadedImages:
    """Load images in the exact supplied order and validate dimensions."""
    if not paths:
        raise ImageLoadingError(
            "no_image_paths",
            "Select at least one image.",
            "The file-selection result was empty.",
        )
    frames = []
    labels = []
    sources = []
    expected: tuple[int, int] | None = None
    for raw_path in paths:
        path = Path(raw_path)
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            raise ImageLoadingError(
                "unsupported_image_format",
                "The selected image format is not supported.",
                f"Unsupported suffix {path.suffix!r}.",
                str(path),
            )
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            detail = reader.errorString()
            reader.setFileName("")
            raise ImageLoadingError(
                "unreadable_image",
                f"Could not read {path.name}.",
                detail,
                str(path),
            )
        # Release the Windows file handle before validation can raise.
        reader.setFileName("")
        dimensions = (image.width(), image.height())
        if expected is None:
            expected = dimensions
        elif dimensions != expected:
            raise ImageLoadingError(
                "inconsistent_image_dimensions",
                "All ROI images must have identical dimensions.",
                f"{path.name} is {dimensions[0]}×{dimensions[1]}; "
                f"expected {expected[0]}×{expected[1]}.",
                str(path),
            )
        frames.append(qimage_to_rgb_array(image))
        labels.append(path.stem)
        sources.append(str(path.resolve()))
    assert expected is not None
    return LoadedImages(
        frames_rgb=tuple(frames),
        labels=tuple(labels),
        source_identifiers=tuple(sources),
        width=expected[0],
        height=expected[1],
    )
