"""Pure legacy-compatible measurements for already linked particle tracks."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from enum import Enum

from .models import TrackMeasurement


TrackRow = Mapping[str, float | int]


class LegacyTrackingPolicy(str, Enum):
    """Named legacy measurement and selection policies."""

    GENERAL = "general"
    FLUORESCENCE = "fluorescence"
    DEFORMABILITY = "deformability"
    TRANSIENT_ADHESION = "transient_adhesion"


def _ordered(track: Iterable[TrackRow]) -> list[TrackRow]:
    rows = list(track)
    if not rows:
        raise IndexError("cannot measure an empty track")
    return sorted(rows, key=lambda row: float(row["frame"]))


def legacy_particle_ids(filtered_rows: Sequence[TrackRow]) -> tuple[int, ...]:
    """Reproduce range(last filtered particle), including the skipped maximum ID."""
    if not filtered_rows:
        raise IndexError("legacy code indexes the last row of an empty filtered table")
    return tuple(range(int(filtered_rows[-1]["particle"])))


def track_rows(rows: Sequence[TrackRow], particle_id: int) -> list[TrackRow]:
    """Select one particle from linked, intentionally unfiltered rows."""
    selected = [
        row for row in rows if int(row["particle"]) == int(particle_id)
    ]
    if not selected:
        raise IndexError(f"particle {particle_id} has no rows")
    return selected


def elapsed_time(track: Iterable[TrackRow], fps: float) -> float:
    """Calculate elapsed seconds from endpoint frame indices."""
    rows = _ordered(track)
    return (float(rows[-1]["frame"]) - float(rows[0]["frame"])) / float(fps)


def legacy_velocity(distance_micrometres: float, duration: float) -> float:
    """Preserve NumPy-like non-finite behavior for zero-duration tracks."""
    if duration == 0:
        if distance_micrometres == 0:
            return math.nan
        return math.copysign(math.inf, distance_micrometres)
    return float(distance_micrometres) / float(duration)


def _mean(rows: Sequence[TrackRow], name: str) -> float:
    return sum(float(row[name]) for row in rows) / len(rows)


def _distance_pixels(rows: Sequence[TrackRow], policy: LegacyTrackingPolicy) -> float:
    delta_x = float(rows[-1]["x"]) - float(rows[0]["x"])
    if policy in {
        LegacyTrackingPolicy.DEFORMABILITY,
        LegacyTrackingPolicy.TRANSIENT_ADHESION,
    }:
        return delta_x
    delta_y = float(rows[-1]["y"]) - float(rows[0]["y"])
    return math.hypot(delta_x, delta_y)


def _included(
    distance_pixels: float,
    policy: LegacyTrackingPolicy,
    threshold_pixels: float,
) -> bool:
    if policy in {
        LegacyTrackingPolicy.GENERAL,
        LegacyTrackingPolicy.FLUORESCENCE,
    }:
        return distance_pixels > float(threshold_pixels) / 3.0
    if policy is LegacyTrackingPolicy.DEFORMABILITY:
        return (
            distance_pixels < float(threshold_pixels)
            and distance_pixels > float(threshold_pixels) / 3.0
        )
    return distance_pixels < float(threshold_pixels)


def measure_legacy_tracks(
    filtered_rows: Sequence[TrackRow],
    linked_rows: Sequence[TrackRow],
    fps: float,
    micrometres_per_pixel: float,
    policy: LegacyTrackingPolicy,
    threshold_pixels: float,
) -> tuple[TrackMeasurement, ...]:
    """Measure legacy-selected IDs using intentionally unfiltered linked rows."""
    results: list[TrackMeasurement] = []
    for particle in legacy_particle_ids(filtered_rows):
        rows = _ordered(track_rows(linked_rows, particle))
        distance_pixels = _distance_pixels(rows, policy)
        if not _included(distance_pixels, policy, threshold_pixels):
            continue
        duration = elapsed_time(rows, fps)
        distance_um = distance_pixels * float(micrometres_per_pixel)
        area_pixels: float | None = None
        fluorescence: float | None = None
        area_um2: float | None = None
        circularity: float | None = None
        if policy in {
            LegacyTrackingPolicy.GENERAL,
            LegacyTrackingPolicy.DEFORMABILITY,
        }:
            area_pixels = _mean(rows, "mass") / 255.0
        elif policy is LegacyTrackingPolicy.FLUORESCENCE:
            area_pixels = math.pi * _mean(rows, "size") ** 2
            fluorescence = _mean(rows, "mass")
        else:
            area_pixels = _mean(rows, "mass") / 255.0
            area_um2 = area_pixels * float(micrometres_per_pixel) ** 2
            circularity = _mean(rows, "ecc")
        results.append(
            TrackMeasurement(
                source_particle=particle,
                start_frame=float(rows[0]["frame"]),
                end_frame=float(rows[-1]["frame"]),
                elapsed_seconds=duration,
                distance_pixels=distance_pixels,
                distance_micrometres=distance_um,
                velocity_micrometres_per_second=legacy_velocity(
                    distance_um, duration
                ),
                area_pixels=area_pixels,
                fluorescence=fluorescence,
                area_micrometres_squared=area_um2,
                circularity=circularity,
            )
        )
    return tuple(results)

