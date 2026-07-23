"""Deterministic, non-biological ROI accumulation demonstration."""

from __future__ import annotations

import numpy as np

from .image_loader import LoadedImages


def create_synthetic_demo() -> LoadedImages:
    """Return three tiny RGB frames with positive then negative red signal."""
    frames = []
    rectangles = ((12, 12, 28, 28), (8, 8, 44, 36), (18, 14, 30, 26))
    for index, (x1, y1, x2, y2) in enumerate(rectangles, start=1):
        frame = np.zeros((48, 64, 3), dtype=np.uint8)
        frame[:, :, 1] = 12
        frame[y1:y2, x1:x2, 0] = 180
        frame.setflags(write=False)
        frames.append(frame)
    return LoadedImages(
        frames_rgb=tuple(frames),
        labels=("demo_small", "demo_large", "demo_reduced"),
        source_identifiers=(
            "synthetic://roi/demo_small",
            "synthetic://roi/demo_large",
            "synthetic://roi/demo_reduced",
        ),
        width=64,
        height=48,
        synthetic=True,
    )

