"""Pure numerical calculations for legacy KLT velocity results."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .models import FrameSummary, ProfileResult


def euclidean_displacement(
    source_xy: ArrayLike, destination_xy: ArrayLike
) -> NDArray[np.float64]:
    """Return unsigned two-dimensional point displacement in pixels."""
    source = np.asarray(source_xy, dtype=float)
    destination = np.asarray(destination_xy, dtype=float)
    return np.linalg.norm(destination - source, axis=-1)


def displacement_to_velocity(
    displacement_pixels: ArrayLike,
    fps: float,
    micrometres_per_pixel: float,
) -> NDArray[np.float64]:
    """Scale pixels per frame to micrometres per second."""
    return (
        np.asarray(displacement_pixels, dtype=float)
        * float(fps)
        * float(micrometres_per_pixel)
    )


def accepted_point_measurements(
    frame: int,
    source_xy: ArrayLike,
    destination_xy: ArrayLike,
    fps: float,
    micrometres_per_pixel: float,
) -> tuple[NDArray[np.int64], NDArray[np.float64], NDArray[np.float64]]:
    """Build frame, destination-y, and velocity arrays for accepted KLT pairs."""
    source = np.asarray(source_xy, dtype=float)
    destination = np.asarray(destination_xy, dtype=float)
    if source.shape != destination.shape:
        raise ValueError("source and destination coordinates must have the same shape")
    displacement = euclidean_displacement(source, destination)
    velocity = displacement_to_velocity(
        displacement, fps, micrometres_per_pixel
    )
    frames = np.full(displacement.shape, int(frame), dtype=np.int64)
    return frames, destination[..., 1].astype(float), velocity


def frame_summary(frames: ArrayLike, velocities: ArrayLike, fps: float) -> FrameSummary:
    """Aggregate frame velocities and reproduce the legacy linspace time vector."""
    frame_values = np.asarray(frames, dtype=np.int64)
    velocity_values = np.asarray(velocities, dtype=float)
    if frame_values.shape != velocity_values.shape:
        raise ValueError("frames and velocities must have the same shape")
    unique_frames = np.unique(frame_values)
    minimum = np.asarray(
        [np.min(velocity_values[frame_values == frame]) for frame in unique_frames]
    )
    mean = np.asarray(
        [np.mean(velocity_values[frame_values == frame]) for frame in unique_frames]
    )
    maximum = np.asarray(
        [np.max(velocity_values[frame_values == frame]) for frame in unique_frames]
    )
    time_seconds = (
        np.linspace(0, len(unique_frames), len(unique_frames)) / float(fps)
    )
    return FrameSummary(
        frames=unique_frames,
        time_seconds=time_seconds,
        minimum=minimum,
        mean=mean,
        maximum=maximum,
    )


def profile_edges(channel_height_pixels: float, bin_count: int) -> NDArray[np.float64]:
    """Construct the legacy evenly spaced profile edges in pixels."""
    return np.linspace(0.0, float(channel_height_pixels), int(bin_count) + 1)


def velocity_profile(
    positions_pixels: ArrayLike,
    velocities: ArrayLike,
    channel_height_pixels: float,
    bin_count: int,
    micrometres_per_pixel: float,
) -> ProfileResult:
    """Digitize by legacy rules and return upper-edge mean/sample-SD values."""
    positions = np.asarray(positions_pixels, dtype=float)
    velocity_values = np.asarray(velocities, dtype=float)
    if positions.shape != velocity_values.shape:
        raise ValueError("positions and velocities must have the same shape")
    edges = profile_edges(channel_height_pixels, bin_count)
    membership = np.digitize(positions, edges)
    means = []
    standard_deviations = []
    for index in range(1, len(edges)):
        selected = velocity_values[membership == index]
        means.append(float(np.mean(selected)) if selected.size else np.nan)
        standard_deviations.append(
            float(np.std(selected, ddof=1)) if selected.size > 1 else np.nan
        )
    return ProfileResult(
        upper_edges=(edges[1:] * float(micrometres_per_pixel)).astype(float),
        mean=np.asarray(means),
        standard_deviation=np.asarray(standard_deviations),
        membership=membership.astype(np.int64),
    )

