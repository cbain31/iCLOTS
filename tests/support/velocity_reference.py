"""Pure reference calculations matching documented legacy velocity conventions.

This module intentionally has no Tkinter, OpenCV, plotting, pandas, or filesystem
dependencies. It is test support, not a replacement KLT implementation.
"""

from __future__ import annotations

import numpy as np


def euclidean_displacement(old_xy, new_xy):
    """Return unsigned two-dimensional displacement in pixels."""
    old = np.asarray(old_xy, dtype=float)
    new = np.asarray(new_xy, dtype=float)
    return np.linalg.norm(new - old, axis=-1)


def axial_displacement(old_xy, new_xy):
    """Return unsigned x-axis displacement in pixels."""
    old = np.asarray(old_xy, dtype=float)
    new = np.asarray(new_xy, dtype=float)
    return np.abs(new[..., 0] - old[..., 0])


def displacement_to_velocity(displacement, fps, micrometres_per_pixel):
    """Convert pixels/frame to micrometres/second."""
    return np.asarray(displacement, dtype=float) * float(fps) * float(micrometres_per_pixel)


def frame_statistics(frames, velocities):
    """Return sorted frame IDs and per-frame minimum, mean, and maximum."""
    frame_values = np.asarray(frames)
    velocity_values = np.asarray(velocities, dtype=float)
    if frame_values.shape != velocity_values.shape:
        raise ValueError("frames and velocities must have the same shape")
    unique_frames = np.unique(frame_values)
    minimum = []
    mean = []
    maximum = []
    for frame in unique_frames:
        selected = velocity_values[frame_values == frame]
        minimum.append(np.min(selected))
        mean.append(np.mean(selected))
        maximum.append(np.max(selected))
    return {
        "frame": unique_frames,
        "minimum": np.asarray(minimum),
        "mean": np.asarray(mean),
        "maximum": np.asarray(maximum),
    }


def profile_edges(channel_height_pixels, bin_count):
    """Construct the legacy evenly spaced profile edges in pixels."""
    if channel_height_pixels <= 0 or bin_count <= 0:
        raise ValueError("channel height and bin count must be positive")
    return np.linspace(0.0, float(channel_height_pixels), int(bin_count) + 1)


def profile_bin_means(positions, velocities, edges):
    """Return upper-edge coordinates and means using legacy digitization."""
    position_values = np.asarray(positions, dtype=float)
    velocity_values = np.asarray(velocities, dtype=float)
    edge_values = np.asarray(edges, dtype=float)
    if position_values.shape != velocity_values.shape:
        raise ValueError("positions and velocities must have the same shape")
    membership = np.digitize(position_values, edge_values)
    means = np.asarray(
        [
            np.mean(velocity_values[membership == index])
            if np.any(membership == index)
            else np.nan
            for index in range(1, len(edge_values))
        ]
    )
    return edge_values[1:], means


def profile_metrics(positions, velocities):
    """Calculate the archived profile shape metrics using outermost wall bins."""
    x = np.asarray(positions, dtype=float)
    y = np.asarray(velocities, dtype=float)
    finite = np.isfinite(x) & np.isfinite(y)
    x = x[finite]
    y = y[finite]
    if x.size < 3:
        raise ValueError("at least three finite profile points are required")
    profile_max = np.max(y)
    profile_min = np.min(y)
    profile_mean = np.mean(y)
    wall_mean = np.mean(y[[0, -1]])
    coefficients = np.polyfit(x, y, 2)
    predicted = np.polyval(coefficients, x)
    constant_sse = np.sum((y - profile_mean) ** 2)
    quadratic_sse = np.sum((y - predicted) ** 2)
    quadratic_r2 = np.nan if constant_sse == 0 else 1.0 - quadratic_sse / constant_sse
    return {
        "wall_to_max_ratio": wall_mean / profile_max,
        "center_to_wall_contrast": 1.0 - wall_mean / profile_max,
        "normalized_range": (profile_max - profile_min) / profile_max,
        "profile_cv": np.std(y, ddof=1) / profile_mean,
        "quadratic_coefficient_raw": coefficients[0],
        "quadratic_coefficient_normalized": coefficients[0] / profile_max,
        "quadratic_r2": quadratic_r2,
    }
