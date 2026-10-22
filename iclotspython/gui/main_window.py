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
from .workflow_screen import MultiscaleScreen
from .video_screen import VelocityScreen
from .tracking_screen import TrackingScreen


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
        self.screens = {"ROI Accumulation": self.roi_screen}
        for mode in ("device", "microchannel"):
            screen = MultiscaleScreen(mode)
            self.screens[screen.workflow_title] = screen
            self.workspace.addWidget(screen)
        velocity = VelocityScreen()
        self.screens[velocity.workflow_title] = velocity
        self.workspace.addWidget(velocity)
        for policy in ("general", "deformability", "transient_adhesion"):
            screen = TrackingScreen(policy)
            self.screens[screen.workflow_title] = screen
            self.workspace.addWidget(screen)
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
            "Choose a workflow; parameters and results are independent for each screen."
        )

    def _build_navigation(self) -> None:
        groups = {
            "Accumulation and occlusion": [
                ("ROI Accumulation", True),
                ("Device Accumulation", True),
                ("Microchannel Accumulation", True),
            ],
            "Velocity": [("Velocity Profiling", True)],
            "Cell tracking": [("Single-cell Tracking", True), ("Deformability", True), ("Fluorescence Tracking — scientific review pending", False)],
            "Adhesion": [("Transient Adhesion", True), ("Adhesion Analysis — coming later", False)],
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
        if selected:
            name = selected[0].data(0, Qt.ItemDataRole.UserRole)
            if name in self.screens:
                self.workspace.setCurrentWidget(self.screens[name])

    def closeEvent(self, event) -> None:
        stopped = [screen.shutdown() for screen in self.screens.values()]
        if not all(stopped):
            event.ignore()
            self.statusBar().showMessage("Cancelling analysis; close again after it stops.")
            return
        super().closeEvent(event)

