"""QApplication construction and process entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

from .main_window import MainWindow


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Return the existing QApplication or construct one safely."""
    existing = QApplication.instance()
    if existing is not None:
        return existing
    application = QApplication(list(argv) if argv is not None else sys.argv)
    if not QFontDatabase.families():
        # Some restricted/offscreen environments expose no system fonts.
        # Matplotlib is already a desktop dependency and supplies this font.
        from matplotlib import get_data_path

        font_path = Path(get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            application.setFont(QFont(families[0], 9))
    return application


def run(argv: Sequence[str] | None = None) -> int:
    """Show one main window and return Qt's process exit code."""
    application = create_application(argv)
    window = MainWindow()
    window.show()
    return int(application.exec())

