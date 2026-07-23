"""Pure NumPy references for accumulation and occlusion specifications."""

from __future__ import annotations

import math
import re

import numpy as np


BGR_INDEX = {"blue": 0, "green": 1, "red": 2}


def threshold_channel(channel, threshold):
    """Match OpenCV THRESH_BINARY: only values strictly above threshold count."""
    return (np.asarray(channel) > threshold).astype(np.uint8)


def count_signal_pixels(mask):
    return int(np.count_nonzero(np.asarray(mask)))


def pixel_count_to_area(pixel_count, micrometres_per_pixel):
    if micrometres_per_pixel <= 0:
        raise ValueError("micrometres per pixel must be positive")
    return float(pixel_count) * float(micrometres_per_pixel) ** 2


def signed_sequential_changes(values):
    values = np.asarray(values, dtype=float)
    return np.diff(values)


def legacy_series_with_zero_baseline(values):
    observed = [float(value) for value in values]
    areas = [0.0] + observed
    changes = [0.0] + [areas[index + 1] - areas[index] for index in range(len(areas) - 1)]
    return {"areas": np.asarray(areas), "changes": np.asarray(changes)}


def intended_observed_series(values):
    observed = np.asarray(values, dtype=float)
    changes = np.empty(observed.shape, dtype=float)
    if observed.size:
        changes[0] = np.nan
        changes[1:] = np.diff(observed)
    return {"areas": observed, "changes": changes}


def legacy_percent_occlusion(signal_mask, device_mask):
    numerator = count_signal_pixels(signal_mask)
    denominator = count_signal_pixels(device_mask)
    if denominator == 0:
        return math.nan if numerator == 0 else math.inf
    return numerator / denominator * 100.0


def intended_percent_occlusion(signal_mask, device_mask):
    signal = np.asarray(signal_mask, dtype=bool)
    device = np.asarray(device_mask, dtype=bool)
    if signal.shape != device.shape:
        raise ValueError("signal and device masks must have the same shape")
    denominator = count_signal_pixels(device)
    if denominator == 0:
        return 0.0
    return count_signal_pixels(signal & device) / denominator * 100.0


def roi_area_summary(mask, micrometres_per_pixel):
    pixels = count_signal_pixels(mask)
    return {"pixels": pixels, "area_micrometres_squared": pixel_count_to_area(pixels, micrometres_per_pixel)}


def channel_masks_from_bgr(image, thresholds):
    image = np.asarray(image)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("expected a BGR image with three layers")
    return {
        color: threshold_channel(image[:, :, index], thresholds[color])
        for color, index in BGR_INDEX.items()
    }


def legacy_device_map(bgr_series, map_threshold=10):
    images = np.asarray(bgr_series)
    if images.ndim != 4 or images.shape[-1] != 3:
        raise ValueError("expected frames of BGR images")
    return np.any(images > map_threshold, axis=(0, 3)).astype(np.uint8)


def connected_components(mask):
    """Return four-connected components in deterministic row-major discovery order."""
    binary = np.asarray(mask, dtype=bool)
    visited = np.zeros(binary.shape, dtype=bool)
    components = []
    for row, col in np.ndindex(binary.shape):
        if not binary[row, col] or visited[row, col]:
            continue
        stack = [(row, col)]
        visited[row, col] = True
        component = []
        while stack:
            current_row, current_col = stack.pop()
            component.append((current_row, current_col))
            for next_row, next_col in (
                (current_row - 1, current_col),
                (current_row + 1, current_col),
                (current_row, current_col - 1),
                (current_row, current_col + 1),
            ):
                if (
                    0 <= next_row < binary.shape[0]
                    and 0 <= next_col < binary.shape[1]
                    and binary[next_row, next_col]
                    and not visited[next_row, next_col]
                ):
                    visited[next_row, next_col] = True
                    stack.append((next_row, next_col))
        components.append(sorted(component))
    return components


def legacy_microchannel_map(last_bgr_image, thresholds):
    masks = channel_masks_from_bgr(last_bgr_image, thresholds)
    union = np.any(np.stack(list(masks.values())), axis=0)
    width = union.shape[1]
    active_rows = np.sum(union, axis=1) * width > 1
    return np.repeat(active_rows[:, None], width, axis=1).astype(np.uint8)


def horizontal_row_regions(map_mask):
    active = np.any(np.asarray(map_mask, dtype=bool), axis=1)
    regions = []
    start = None
    for index, value in enumerate(active):
        if value and start is None:
            start = index
        if start is not None and (not value or index == len(active) - 1):
            end = index + 1 if value and index == len(active) - 1 else index
            regions.append((start, end))
            start = None
    return regions


def validate_complete_horizontal_geometry(map_mask):
    mask = np.asarray(map_mask, dtype=bool)
    row_counts = np.sum(mask, axis=1)
    if np.any((row_counts != 0) & (row_counts != mask.shape[1])):
        raise ValueError("horizontal channel rows must be complete")
    return horizontal_row_regions(mask)


def column_occupancy(signal_mask, row_start, row_end):
    band = np.asarray(signal_mask, dtype=float)[row_start:row_end, :]
    if band.shape[0] == 0:
        raise ValueError("channel region has zero height")
    return np.sum(band, axis=0) / band.shape[0] * 100.0


def microchannel_summaries(signal_mask, channel_map):
    summaries = []
    for label, (start, end) in enumerate(horizontal_row_regions(channel_map)):
        occupancy = column_occupancy(signal_mask, start, end)
        area = count_signal_pixels(np.asarray(signal_mask)[start:end, :])
        summaries.append(
            {
                "channel": label,
                "row_start": start,
                "row_end": end,
                "column_occupancy_percent": occupancy,
                "mean_occlusion_percent": float(np.mean(occupancy)),
                "max_occlusion_percent": float(np.max(occupancy)),
                "area_pixels": area,
            }
        )
    return summaries


def legacy_microchannel_series(signal_masks, channel_map):
    previous = np.zeros(len(horizontal_row_regions(channel_map)), dtype=float)
    frames = []
    for frame_index, signal in enumerate(signal_masks):
        summaries = microchannel_summaries(signal, channel_map)
        for summary in summaries:
            channel = summary["channel"]
            summary = dict(summary)
            summary["frame"] = frame_index
            summary["accumulation_pixels"] = summary["area_pixels"] - previous[channel]
            previous[channel] = summary["area_pixels"]
            frames.append(summary)
    return frames


def legacy_lexical_image_order(filenames):
    groups = []
    for extension in (".png", ".jpg", ".tif"):
        groups.extend(sorted(name for name in filenames if name.lower().endswith(extension)))
    return groups


def natural_numeric_order(filenames):
    def key(name):
        return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]

    return sorted(filenames, key=key)

