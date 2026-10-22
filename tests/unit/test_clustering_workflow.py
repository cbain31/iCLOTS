"""Seeded final-clustering parity, exclusions, workbook validation and reports."""

from dataclasses import replace

import numpy as np
import pytest

from iclotspython.application.clustering import ClusteringRequest, load_clustering_workbooks, run_clustering
from iclotspython.application.errors import RequestValidationError, WorkflowCancelled
from iclotspython.presentation.models import TableData

pytestmark = pytest.mark.unit


def request():
    rows = tuple(("a" if i < 6 else "b", float(i % 3) + (10 if i >= 6 else 0), float(i % 2) + (12 if i >= 6 else 0)) for i in range(12))
    return ClusteringRequest(TableData(("Sample", "Area", "Texture"), rows), ("Area", "Texture"))


def test_final_labels_match_checked_in_kmeans_constructor():
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    data = request()
    matrix = np.asarray([r[1:] for r in data.data.rows])
    expected = KMeans(n_clusters=2, random_state=100).fit_predict(matrix)
    result = run_clustering(data)
    assert [r[-1] for r in result.table("Labeled data").rows] == list(expected)
    assert result.table("Silhouette").rows[0][0] == pytest.approx(silhouette_score(matrix, expected))
    assert dict(result.parameters)["normalization"] == "none"
    assert result.table("Scree diagnostic").rows[0][0] == 1
    assert dict(dict(result.parameters)["estimator"])["random_state"] == 100


def test_selected_feature_exclusions_keep_sample_row_alignment():
    original = request()
    rows = list(original.data.rows)
    rows[2] = ("excluded", None, 0)
    result = run_clustering(replace(original, data=replace(original.data, rows=tuple(rows))))
    assert result.table("Excluded rows").rows == ((2, "Missing selected feature (legacy dropna)"),)
    assert 2 not in [r[0] for r in result.table("Labeled data").rows]
    assert all(r[1] != "excluded" for r in result.table("Labeled data").rows)
    assert sum(r[-1] for r in result.table("Counts").rows) == 11


@pytest.mark.parametrize("features,clusters", [((), 2), (("Area",), 2), (("Area", "bad"), 2), (("Area", "Texture"), 12)])
def test_invalid_feature_requests(features, clusters):
    with pytest.raises(RequestValidationError):
        run_clustering(replace(request(), features=features, clusters=clusters))


def test_workbook_single_sheet_policy(tmp_path):
    from openpyxl import Workbook

    path = tmp_path / "sample.xlsx"
    workbook = Workbook()
    workbook.active.append(("Area", "Texture"))
    workbook.active.append((1, 2))
    workbook.save(path)
    data = load_clustering_workbooks((str(path),))
    assert data.columns == ("Area", "Texture", "Sample")
    assert data.rows == ((1, 2, "sample"),)
    workbook.create_sheet("extra")
    workbook.save(path)
    workbook.close()
    with pytest.raises(RequestValidationError, match="exactly one worksheet"):
        load_clustering_workbooks((str(path),))


def test_cancelled_clustering_does_not_fit():
    with pytest.raises(WorkflowCancelled):
        run_clustering(request(), is_cancelled=lambda: True)
