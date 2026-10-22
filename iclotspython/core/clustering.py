"""Existing KMeans policy on an explicit finite feature matrix."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ClusterResult:
    labels: tuple[int, ...]
    centers: tuple[tuple[float, ...], ...]
    silhouette: float
    inertia: float
    estimator_parameters: tuple
    scree: tuple[tuple[int, float], ...]


def cluster_legacy(features, clusters, checkpoint=None):
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    values = np.asarray(features, dtype=float)
    estimator = KMeans(n_clusters=clusters, random_state=100)
    labels = estimator.fit_predict(values)
    silhouette = float(silhouette_score(values, labels))
    scree = []
    for k in range(1, min(11, len(values)) + 1):
        if checkpoint:
            checkpoint(k)
        diagnostic = KMeans(n_clusters=k, max_iter=1000).fit(values)
        scree.append((k, float(diagnostic.inertia_)))
    return ClusterResult(tuple(map(int, labels)), tuple(tuple(map(float, row)) for row in estimator.cluster_centers_),
                         silhouette, float(estimator.inertia_), tuple(estimator.get_params().items()), tuple(scree))
