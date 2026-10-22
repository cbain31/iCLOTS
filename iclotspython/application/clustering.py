"""Workbook input and feature-specific missing-row policy for legacy clustering."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from iclotspython.core.clustering import cluster_legacy
from iclotspython.presentation.models import PlotSeries, TableData
from iclotspython.presentation.workflows import NamedTable, PlotPanel, WorkflowResult

from .common import checkpoint, environment_versions, integer, invalid
from .errors import ScientificCalculationError


@dataclass(frozen=True)
class ClusteringRequest:
    data: TableData
    features: tuple[str, ...]
    clusters: int = 2
    source_identifiers: tuple[str, ...] = ()


def load_clustering_workbooks(paths):
    """Read one-sheet XLSX inputs and retain workbook-derived sample labels."""
    import pandas as pd

    if not paths:
        invalid("workbooks", "Choose one or more single-sheet XLSX workbooks.")
    frames = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.suffix.lower() != ".xlsx" or not path.is_file():
            invalid("workbooks", "Clustering inputs must be existing XLSX files.")
        try:
            with pd.ExcelFile(path, engine="openpyxl") as workbook:
                if len(workbook.sheet_names) != 1:
                    invalid("workbooks", f"{path.name} must contain exactly one worksheet.")
                frame = pd.read_excel(workbook)
        except (OSError, ValueError) as exc:
            invalid("workbooks", f"Could not read {path.name}: {exc}")
        if frame.columns.duplicated().any():
            invalid("columns", "Workbook columns must have unique names.")
        frame["Sample"] = path.name.split(".")[0]  # original sample convention
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    return TableData(tuple(map(str, combined.columns)), tuple(tuple(v.item() if isinstance(v, np.generic) else v for v in row) for row in combined.itertuples(index=False, name=None)))


def numeric_features(table):
    """Offer numeric columns without changing or excluding input rows."""
    candidates = []
    for col, name in enumerate(table.columns):
        values = [row[col] for row in table.rows if row[col] is not None]
        if name != "Sample" and values and all(isinstance(v, (int, float, np.number)) and not isinstance(v, bool) for v in values):
            candidates.append(name)
    return tuple(candidates)


def run_clustering(request: ClusteringRequest, progress=None, is_cancelled=None):
    workflow = "clustering"
    checkpoint(workflow, progress, is_cancelled, 0, 13, "Validating selected features")
    columns = request.data.columns
    if len(set(columns)) != len(columns) or "Sample" not in columns:
        invalid("columns", "Clustering requires unique columns and a Sample column.")
    if len(request.features) < 2 or len(set(request.features)) != len(request.features):
        invalid("features", "Choose at least two different numerical features.")
    if any(len(row) != len(columns) for row in request.data.rows):
        invalid("rows", "Every input row must match the column count.")
    if any(feature not in numeric_features(request.data) for feature in request.features):
        invalid("features", "Selected features must be numerical columns in the input table.")
    indices = [columns.index(f) for f in request.features]
    matrix, retained, excluded = [], [], []
    for row_index, row in enumerate(request.data.rows):
        selected = np.asarray([float(row[i]) if row[i] is not None else np.nan for i in indices])
        if np.any(np.isnan(selected)):
            excluded.append((row_index, "Missing selected feature (legacy dropna)"))
            continue
        if not np.all(np.isfinite(selected)):
            invalid("features", "Infinite feature values are unsupported; no normalization was applied.")
        retained.append(row_index)
        matrix.append(selected)
    clusters = integer(request.clusters, "clusters", 2)
    if len(matrix) <= clusters:
        invalid("clusters", "Cluster count must be at least two and less than the number of complete selected-feature rows.")

    def check(k):
        checkpoint(workflow, progress, is_cancelled, k + 1, 13, f"Scree diagnostic: {k} clusters")

    try:
        result = cluster_legacy(matrix, clusters, check)
    except ValueError as exc:
        raise ScientificCalculationError(f"KMeans/silhouette could not be evaluated: {exc}") from exc
    values = np.asarray(matrix)
    sample_col = columns.index("Sample")
    rows = tuple((source_row, request.data.rows[source_row][sample_col], *map(float, value), label)
                 for source_row, value, label in zip(retained, values, result.labels))
    tables = [NamedTable("Labeled data", TableData(("Source row", "Sample", *request.features, "Label"), rows)),
              NamedTable("Excluded rows", TableData(("Source row", "Reason"), tuple(excluded))),
              NamedTable("Silhouette", TableData(("Silhouette coefficient",), ((result.silhouette,),))),
              NamedTable("Scree diagnostic", TableData(("Number of clusters", "SSE"), result.scree))]
    labels = np.asarray(result.labels)
    for title, operation in (("Min. by cluster", np.min), ("Mean by cluster", np.mean), ("Max. by cluster", np.max)):
        tables.append(NamedTable(title, TableData(("Label", *request.features), tuple((label, *map(float, operation(values[labels == label], axis=0))) for label in sorted(set(result.labels))))))
    tables.append(NamedTable("Stdev. by cluster", TableData(("Label", *request.features), tuple((label, *(map(float, np.std(values[labels == label], axis=0, ddof=1)) if np.sum(labels == label) > 1 else (float("nan"),) * values.shape[1])) for label in sorted(set(result.labels))))))
    counts = {}
    for row in rows:
        key = (row[1], row[-1])
        counts[key] = counts.get(key, 0) + 1
    tables.append(NamedTable("Counts", TableData(("Sample", "Label", "size"), tuple((*key, value) for key, value in sorted(counts.items(), key=lambda item: str(item[0]))))))
    with np.errstate(divide="ignore", invalid="ignore"):
        correlation = np.corrcoef(values, rowvar=False)
    tables.append(NamedTable("Feature correlation", TableData(("Feature", *request.features), tuple((name, *map(float, row)) for name, row in zip(request.features, correlation)))))
    plots = (PlotPanel("Scree diagnostic (unseeded legacy)", "Number of clusters", "SSE", (PlotSeries("SSE", "", "SSE", tuple(float(k) for k, _ in result.scree), tuple(v for _, v in result.scree), "clusters", "SSE"),)),
             PlotPanel("Selected feature groups", request.features[0], request.features[1], tuple(PlotSeries(f"Cluster {label}", "", "features", tuple(map(float, values[labels == label, 0])), tuple(map(float, values[labels == label, 1])), "input units", "input units") for label in sorted(set(result.labels)))))
    warnings = ("Features use original units without scaling; rows missing any selected feature are excluded and listed explicitly.",
                "Final KMeans retains random_state=100. Other estimator defaults depend on scikit-learn and are recorded; exact historical default parity is unestablished.",
                "Legacy scree diagnostic is unseeded and may vary across runs. It uses up to 11 clusters, bounded by available rows; final clustering is separately seeded.")
    checkpoint(workflow, progress, is_cancelled, 13, 13, "Analysis complete")
    return WorkflowResult(workflow, tuple(tables), plots, (("features", request.features), ("estimator", result.estimator_parameters), ("normalization", "none"), ("excluded_rows", len(excluded))),
        (("contract_version", "1.0"), ("scientific_policy", "legacy-compatible with recorded library defaults"), ("sources", request.source_identifiers),
         ("environment", environment_versions("scikit-learn", "pandas", "openpyxl"))), warnings, "clustering")
