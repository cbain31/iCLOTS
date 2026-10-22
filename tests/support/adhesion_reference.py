"""Independent transcription of the legacy fluorescence/filopodia cell loop.

Uses the original regionprops_table and OpenCV operations rather than production
region objects. No files, GUI, plots, or legacy DataFrame.append are needed.
"""

import math

import numpy as np


def legacy_cells(primary, functional, *, calibration=1, minarea=0, maxarea=10000, threshold=50, functional_threshold=30, filopodia=False):
    import cv2
    from skimage import measure
    from skimage.feature import corner_harris, corner_peaks

    _, mask = cv2.threshold(primary, threshold, 255, cv2.THRESH_BINARY)
    _, fn_mask = cv2.threshold(functional, functional_threshold, 255, cv2.THRESH_BINARY)
    props = measure.regionprops_table(measure.label(mask), properties=("centroid", "area", "eccentricity", "coords", "convex_image"))
    rows = []
    for i, area in enumerate(props["area"]):
        if not minarea < area < maxarea:
            continue
        coords = np.asarray(props["coords"][i]).astype(int)
        texture = np.std(primary[coords[:, 0], coords[:, 1]])
        signal = int(np.any(fn_mask[coords[:, 0], coords[:, 1]] > 0))
        fn = np.sum(functional[coords[:, 0], coords[:, 1]]) if signal else 0
        count, lengths = 0, [0]
        if filopodia:
            convex = (props["convex_image"][i] * 255).astype(np.uint8)
            bordered = cv2.copyMakeBorder(convex, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=0)
            peaks = corner_peaks(corner_harris(bordered, k=0.2), threshold_rel=0.5, min_distance=5)
            if peaks.any():
                count = len(peaks)
                center = [bordered.shape[1] / 2, bordered.shape[0] / 2]
                lengths = [math.sqrt((center[0] - p[0]) ** 2 + (center[1] - p[1]) ** 2) * calibration for p in peaks]
        rows.append((props["centroid-1"][i], props["centroid-0"][i], area, area * calibration * calibration,
                     props["eccentricity"][i], texture, signal, fn, count, min(lengths), np.mean(lengths), max(lengths), np.std(lengths)))
    return rows
