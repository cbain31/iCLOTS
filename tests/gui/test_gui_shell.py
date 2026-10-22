"""Single-window shell and workflow navigation tests."""

from __future__ import annotations

import pytest

from iclotspython.gui.main_window import MainWindow


pytestmark = [pytest.mark.unit, pytest.mark.gui]


def test_main_window_exposes_implemented_workflows(qt_app):
    window = MainWindow()
    try:
        assert window.windowTitle() == "iCLOTS Modern"
        assert window.centralWidget() is not None
        assert window.statusBar() is not None
        assert window.navigation_items["ROI Accumulation"].isDisabled() is False
        future = [
            item
            for name, item in window.navigation_items.items()
            if name not in window.screens
        ]
        assert future
        assert all(item.isDisabled() for item in future)
        for name, screen in window.screens.items():
            assert not window.navigation_items[name].isDisabled()
            window.navigation.setCurrentItem(window.navigation_items[name])
            assert window.workspace.currentWidget() is screen
        window.navigation.setCurrentItem(window.navigation_items["ROI Accumulation"])
        assert window.workspace.currentWidget() is window.roi_screen
        assert window.roi_screen.result_tabs.count() == 5
    finally:
        window.close()
        qt_app.processEvents()
