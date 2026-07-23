"""Pure legacy-compatible accumulation and occlusion calculations."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .models import AccumulationSeries, MicrochannelMeasurement


BGR_INDEX: Mapping[str, int] = {"blue": 0, "green": 1, "red": 2}


def threshold_channel(channel: ArrayLike, threshold: float) -> NDArray[np.uint8]:
    """Match OpenCV THRESH_BINARY using a strict greater-than cutoff."""
    return (np.asarray(channel) > threshold).astype(np.uint8)


def count_signal_pixels(mask: ArrayLike) -> int:
    """Count nonzero signal pixels."""
    return int(np.count_nonzero(np.asarray(mask)))


def calibrated_area(pixel_count: float, micrometres_per_pixel: float) -> float:
    """Convert a pixel count to square micrometres."""
    return float(pixel_count) * float(micrometres_per_pixel) ** 2


def signed_sequential_changes(values: Sequence[float]) -> NDArray[np.float64]:
    """Return signed changes between consecutive observations."""
    return np.diff(np.asarray(values, dtype=float))


def legacy_series_with_zero_baseline(values: Sequence[float]) -> AccumulationSeries:
    """Prepend the artificial zero and calculate signed sequential changes."""
    observed = np.asarray([0.0, *(float(value) for value in values)], dtype=float)
    changes = np.asarray([0.0, *signed_sequential_changes(observed)], dtype=float)
    return AccumulationSeries(values=observed, changes=changes)


def legacy_percent_occlusion(signal_mask: ArrayLike, device_mask: ArrayLike) -> float:
    """Use the unrestricted signal numerator and legacy non-finite zero division."""
    numerator = count_signal_pixels(signal_mask)
    denominator = count_signal_pixels(device_mask)
    if denominator == 0:
        return math.nan if numerator == 0 else math.inf
    return numerator / denominator * 100.0


def legacy_device_map(
    bgr_series: ArrayLike, map_threshold: float = 10
) -> NDArray[np.uint8]:
    """Construct the device map from signal in every frame and BGR layer."""
    images = np.asarray(bgr_series)
    if images.ndim != 4 or images.shape[-1] != 3:
        raise ValueError("expected frames of BGR images")
    return np.any(images > map_threshold, axis=(0, 3)).astype(np.uint8)


def channel_masks_from_bgr(
    image: ArrayLike, thresholds: Mapping[str, float]
) -> dict[str, NDArray[np.uint8]]:
    """Threshold each named color using the legacy BGR layer convention."""
    bgr = np.asarray(image)
    if bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError("expected a BGR image with three layers")
    return {
        color: threshold_channel(bgr[:, :, layer], thresholds[color])
        for color, layer in BGR_INDEX.items()
    }


def legacy_microchannel_map(
    last_bgr_image: ArrayLike, thresholds: Mapping[str, float]
) -> NDArray[np.uint8]:
    """Build full-width horizontal geometry from all layers of the final frame."""
    masks = channel_masks_from_bgr(last_bgr_image, thresholds)
    union = np.any(np.stack(tuple(masks.values())), axis=0)
    width = union.shape[1]
    active_rows = np.sum(union, axis=1) * width > 1
    return np.repeat(active_rows[:, None], width, axis=1).astype(np.uint8)


def horizontal_row_regions(map_mask: ArrayLike) -> tuple[tuple[int, int], ...]:
    """Return contiguous active row bands in top-to-bottom order."""
    active = np.any(np.asarray(map_mask, dtype=bool), axis=1)
    regions: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(active):
        if value and start is None:
            start = index
        if start is not None and (not value or index == len(active) - 1):
            end = index + 1 if value and index == len(active) - 1 else index
            regions.append((start, end))
            start = None
    return tuple(regions)


def column_occupancy(
    signal_mask: ArrayLike, row_start: int, row_end: int
) -> NDArray[np.float64]:
    """Calculate zero-based, ROI-relative per-column occupancy percentages."""
    band = np.asarray(signal_mask, dtype=float)[row_start:row_end, :]
    return np.sum(band, axis=0) / band.shape[0] * 100.0


def legacy_microchannel_series(
    signal_masks: Sequence[ArrayLike],
    channel_map: ArrayLike,
    micrometres_per_pixel: float,
) -> tuple[MicrochannelMeasurement, ...]:
    """Measure each horizontal channel with a per-channel zero baseline."""
    regions = horizontal_row_regions(channel_map)
    previous = np.zeros(len(regions), dtype=float)
    measurements: list[MicrochannelMeasurement] = []
    for frame, signal_mask in enumerate(signal_masks):
        signal = np.asarray(signal_mask)
        for channel, (row_start, row_end) in enumerate(regions):
            occupancy = column_occupancy(signal, row_start, row_end)
            area = float(np.sum(signal[row_start:row_end, :]))
            change = area - previous[channel]
            measurements.append(
                MicrochannelMeasurement(
                    frame=frame,
                    channel=channel,
                    row_start=row_start,
                    row_end=row_end,
                    column_occupancy_percent=occupancy,
                    mean_occlusion_percent=float(np.mean(occupancy)),
                    max_occlusion_percent=float(np.max(occupancy)),
                    area_pixels=area,
                    accumulation_pixels=change,
                    area_micrometres_squared=calibrated_area(
                        area, micrometres_per_pixel
                    ),
                    accumulation_micrometres_squared=calibrated_area(
                        change, micrometres_per_pixel
                    ),
                )
            )
            previous[channel] = area
    return tuple(measurements)
