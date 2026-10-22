"""Legacy static-adhesion measurements on explicit image arrays.

Scikit-image is imported only during segmentation. Legacy eccentricity naming
and the filopodia coordinate convention are retained deliberately.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class AdhesionCell:
    x: float
    y: float
    area_pixels: float
    area_micrometres_squared: float
    eccentricity: float
    texture: float
    functional_signal: int
    functional_intensity: float
    filopodia_count: int = 0
    filopodia_min: float = 0
    filopodia_mean: float = 0
    filopodia_max: float = 0
    filopodia_stdev: float = 0


def segment_legacy_cells(primary, functional, calibration, minarea, maxarea, threshold, functional_threshold,
                         *, filopodia=False, harris_k=0.2, threshold_rel=0.5, min_distance=5):
    from skimage import measure
    from skimage.feature import corner_harris, corner_peaks

    primary = np.asarray(primary)
    functional = np.asarray(functional)
    labeled = measure.label(primary > threshold)
    result = []
    for region in measure.regionprops(labeled):
        if not minarea < region.area < maxarea:
            continue
        coords = region.coords
        intensity = primary[coords[:, 0], coords[:, 1]]
        fn = functional[coords[:, 0], coords[:, 1]]
        signal = int(np.any(fn > functional_threshold))
        count, lengths = 0, np.zeros(1)
        if filopodia:
            convex = np.asarray(region.image_convex * 255).astype(np.uint8)
            padded = np.pad(convex, 10, mode="constant")
            peaks = corner_peaks(corner_harris(padded, k=harris_k), threshold_rel=threshold_rel, min_distance=min_distance)
            if peaks.any():
                count = len(peaks)
                center = (padded.shape[1] / 2, padded.shape[0] / 2)
                # Preserve legacy row/column ordering even for nonsquare cells.
                lengths = np.asarray([math.sqrt((center[0] - p[0]) ** 2 + (center[1] - p[1]) ** 2) * calibration for p in peaks])
        result.append(AdhesionCell(
            float(region.centroid[1]), float(region.centroid[0]), float(region.area), float(region.area * calibration * calibration),
            float(region.eccentricity), float(np.std(intensity)), signal, float(np.sum(fn)) if signal else 0,
            count, float(np.min(lengths)), float(np.mean(lengths)), float(np.max(lengths)), float(np.std(lengths)),
        ))
    return tuple(result)


def brightfield_area(radius_pixels, calibration):
    area = float(radius_pixels) * float(radius_pixels) * math.pi
    return area, area * calibration * calibration
