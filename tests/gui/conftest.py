"""Shared fixtures for headless Phase 3C interface tests."""

from __future__ import annotations

import os

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qt_app():
    """Provide one headless QApplication without requiring pytest-qt."""
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
    application.closeAllWindows()
    application.processEvents()

