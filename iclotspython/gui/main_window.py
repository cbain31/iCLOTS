"""Modern single-window iCLOTS application shell."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import GUI_VERSION
from .roi_screen import ROIAccumulationScreen


class MainWindow(QMainWindow):
    """Restrained navigation shell containing the first modern workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("main_window")
        self.setWindowTitle("iCLOTS Modern")
        self.resize(1280, 820)

        container = QWidget()
        layout = QVBoxLayout(container)
        heading = QLabel(f"iCLOTS Modern  •  {GUI_VERSION}")
        heading.setObjectName("application_title")
        heading.setStyleSheet("font-size: 18px; font-weight: 600; padding: 6px;")
        layout.addWidget(heading)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        horizontal = QWidget()
        from PySide6.QtWidgets import QHBoxLayout

        horizontal_layout = QHBoxLayout(horizontal)
        self.navigation = QTreeWidget()
        self.navigation.setObjectName("workflow_navigation")
        self.navigation.setHeaderLabel("Modern workflows")
        self.navigation.setMaximumWidth(255)
        self.navigation.setMinimumWidth(220)
        horizontal_layout.addWidget(self.navigation)

        self.workspace = QStackedWidget()
        self.workspace.setObjectName("workflow_workspace")
        self.roi_screen = ROIAccumulationScreen()
        self.workspace.addWidget(self.roi_screen)
        horizontal_layout.addWidget(self.workspace, 1)
        body_layout.addWidget(horizontal)
        layout.addWidget(body, 1)
        self.setCentralWidget(container)

        self.navigation_items: dict[str, QTreeWidgetItem] = {}
        self._build_navigation()
        self.navigation.itemSelectionChanged.connect(self._navigation_changed)
        self.navigation_items["ROI Accumulation"].setSelected(True)

        self.statusBar().setObjectName("application_status_bar")
        self.statusBar().showMessage(
            "ROI Accumulation is the available modern workflow."
        )

    def _build_navigation(self) -> None:
        groups = {
            "Accumulation and occlusion": [
                ("ROI Accumulation", True),
                ("Device Accumulation — coming later", False),
                ("Microchannel Accumulation — coming later", False),
            ],
            "Velocity": [("Velocity Profiling — coming later", False)],
            "Cell tracking": [("Single-cell Tracking — coming later", False)],
            "Adhesion": [("Adhesion Analysis — coming later", False)],
            "Machine learning": [("Clustering — coming later", False)],
            "Utilities": [("Utilities — coming later", False)],
        }
        for group_name, entries in groups.items():
            group = QTreeWidgetItem([group_name])
            group.setFlags(group.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.navigation.addTopLevelItem(group)
            for name, enabled in entries:
                item = QTreeWidgetItem([name])
                item.setData(0, Qt.ItemDataRole.UserRole, name)
                item.setDisabled(not enabled)
                group.addChild(item)
                self.navigation_items[name] = item
            group.setExpanded(True)

    def _navigation_changed(self) -> None:
        selected = self.navigation.selectedItems()
        if selected and selected[0].data(0, Qt.ItemDataRole.UserRole) == "ROI Accumulation":
            self.workspace.setCurrentWidget(self.roi_screen)

    def closeEvent(self, event) -> None:
        self.roi_screen.shutdown()
        super().closeEvent(event)

