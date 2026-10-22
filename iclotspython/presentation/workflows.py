"""Immutable multi-table results for migrated scientific workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import PlotSeries, TableData


@dataclass(frozen=True)
class NamedTable:
    name: str
    data: TableData


@dataclass(frozen=True)
class PlotPanel:
    title: str
    x_label: str
    y_label: str
    series: tuple[PlotSeries, ...]


@dataclass(frozen=True)
class WorkflowResult:
    workflow_id: str
    tables: tuple[NamedTable, ...]
    plots: tuple[PlotPanel, ...]
    parameters: tuple[tuple[str, Any], ...]
    provenance: tuple[tuple[str, Any], ...]
    warnings: tuple[str, ...]
    suggested_export_stem: str

    def table(self, name: str) -> TableData:
        return next(table.data for table in self.tables if table.name == name)
