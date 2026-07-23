"""QApplication construction and process entrypoint."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Return the existing QApplication or construct one safely."""
    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication(list(argv) if argv is not None else sys.argv)


def run(argv: Sequence[str] | None = None) -> int:
    """Show one main window and return Qt's process exit code."""
    application = create_application(argv)
    window = MainWindow()
    window.show()
    return int(application.exec())

