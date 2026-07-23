"""Read-only Qt table model for Phase 3A TableData."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from iclotspython.presentation.models import TableData


class ResultTableModel(QAbstractTableModel):
    """Expose immutable presentation rows to QTableView."""

    def __init__(self, table: TableData | None = None, parent=None) -> None:
        super().__init__(parent)
        self._table = table or TableData(columns=(), rows=())

    def set_table(self, table: TableData) -> None:
        self.beginResetModel()
        self._table = table
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._table.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._table.columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        value = self._table.rows[index.row()][index.column()]
        return f"{value:g}" if isinstance(value, float) else str(value)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._table.columns[section]
        return str(section + 1)

