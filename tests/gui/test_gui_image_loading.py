"""Image-loading and deterministic demonstration tests."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor, QImage

from iclotspython.gui.demo import create_synthetic_demo
from iclotspython.gui.image_loader import ImageLoadingError, load_image_files
from tests.support.output_factory import workspace_output_directory


pytestmark = [pytest.mark.unit, pytest.mark.gui]


def _save_image(path, width: int, height: int, color: str) -> None:
    image = QImage(width, height, QImage.Format.Format_RGB888)
    image.fill(QColor(color))
    assert image.save(str(path))


def test_loader_preserves_selection_order_and_rgb_dimensions(qt_app):
    with workspace_output_directory() as directory:
        second = directory / "second.png"
        first = directory / "first.png"
        _save_image(second, 5, 3, "red")
        _save_image(first, 5, 3, "blue")

        loaded = load_image_files([str(second), str(first)])

        assert loaded.labels == ("second", "first")
        assert loaded.width == 5
        assert loaded.height == 3
        assert tuple(loaded.frames_rgb[0][0, 0]) == (255, 0, 0)
        assert tuple(loaded.frames_rgb[1][0, 0]) == (0, 0, 255)
        assert not loaded.frames_rgb[0].flags.writeable


def test_loader_reports_inconsistent_dimensions_as_controlled_failure(qt_app):
    with workspace_output_directory() as directory:
        first = directory / "first.png"
        second = directory / "second.png"
        _save_image(first, 5, 3, "red")
        _save_image(second, 6, 3, "red")

        with pytest.raises(ImageLoadingError) as captured:
            load_image_files([str(first), str(second)])

        assert captured.value.code == "inconsistent_image_dimensions"
        assert "identical dimensions" in captured.value.user_message


def test_synthetic_demo_is_deterministic_and_non_persistent():
    before = create_synthetic_demo()
    after = create_synthetic_demo()

    assert before.synthetic is True
    assert before.labels == after.labels
    assert before.source_identifiers == after.source_identifiers
    assert before.width == 64
    assert before.height == 48
    for left, right in zip(before.frames_rgb, after.frames_rgb):
        assert (left == right).all()
