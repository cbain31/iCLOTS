"""Small immutable result structures shared by scientific core modules."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class AccumulationSeries:
    """Observed values with the legacy artificial baseline and signed changes."""

    values: FloatArray
    changes: FloatArray


@dataclass(frozen=True)
class FrameSummary:
    """Per-frame velocity aggregates and the legacy time vector."""

    frames: IntArray
    time_seconds: FloatArray
    minimum: FloatArray
    mean: FloatArray
    maximum: FloatArray


@dataclass(frozen=True)
class ProfileResult:
    """Upper-edge profile coordinates with mean and sample standard deviation."""

    upper_edges: FloatArray
    mean: FloatArray
    standard_deviation: FloatArray
    membership: IntArray


@dataclass(frozen=True)
class MicrochannelMeasurement:
    """One frame/channel microchannel occupancy measurement."""

    frame: int
    channel: int
    row_start: int
    row_end: int
    column_occupancy_percent: FloatArray
    mean_occlusion_percent: float
    max_occlusion_percent: float
    area_pixels: float
    accumulation_pixels: float
    area_micrometres_squared: float
    accumulation_micrometres_squared: float


@dataclass(frozen=True)
class TrackMeasurement:
    """Legacy-compatible endpoint measurement for one accepted particle."""

    source_particle: int
    start_frame: float
    end_frame: float
    elapsed_seconds: float
    distance_pixels: float
    distance_micrometres: float
    velocity_micrometres_per_second: float
    area_pixels: float | None = None
    fluorescence: float | None = None
    area_micrometres_squared: float | None = None
    circularity: float | None = None

