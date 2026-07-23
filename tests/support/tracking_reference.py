"""Pandas-free reference/specification helpers for legacy tracking calculations.

Functions named ``legacy_*`` reproduce inspected selection or threshold behavior.
Functions named ``intended_*`` express Phase 1 specifications only. Nothing here
performs particle detection or TrackPy linking.
"""

from __future__ import annotations

import math
from collections import Counter


def _ordered(track):
    rows = list(track)
    if not rows:
        raise IndexError("cannot measure an empty track")
    return sorted(rows, key=lambda row: float(row["frame"]))


def euclidean_endpoint_displacement(track):
    rows = _ordered(track)
    return math.hypot(
        float(rows[-1]["x"]) - float(rows[0]["x"]),
        float(rows[-1]["y"]) - float(rows[0]["y"]),
    )


def signed_x_endpoint_displacement(track):
    rows = _ordered(track)
    return float(rows[-1]["x"]) - float(rows[0]["x"])


def absolute_x_endpoint_displacement(track):
    return abs(signed_x_endpoint_displacement(track))


def elapsed_time(track, fps):
    if fps <= 0:
        raise ValueError("FPS must be positive")
    rows = _ordered(track)
    return (float(rows[-1]["frame"]) - float(rows[0]["frame"])) / float(fps)


def calibrated_distance(distance_pixels, micrometres_per_pixel):
    if micrometres_per_pixel <= 0:
        raise ValueError("micrometres per pixel must be positive")
    return float(distance_pixels) * float(micrometres_per_pixel)


def legacy_velocity(distance_micrometres, elapsed_seconds):
    """Reproduce NumPy-like non-finite zero-duration division semantics."""
    if elapsed_seconds == 0:
        if distance_micrometres == 0:
            return math.nan
        return math.copysign(math.inf, distance_micrometres)
    return float(distance_micrometres) / float(elapsed_seconds)


def intended_velocity(distance_micrometres, elapsed_seconds):
    if elapsed_seconds <= 0:
        raise ValueError("elapsed time must be positive")
    return float(distance_micrometres) / float(elapsed_seconds)


def filter_tracks_by_observation_count(rows, minimum_observations):
    if minimum_observations <= 0:
        raise ValueError("minimum observations must be positive")
    rows = list(rows)
    counts = Counter(int(row["particle"]) for row in rows)
    retained = {particle for particle, count in counts.items() if count >= minimum_observations}
    return [row for row in rows if int(row["particle"]) in retained]


def legacy_particle_ids(filtered_rows):
    rows = list(filtered_rows)
    if not rows:
        raise IndexError("legacy code indexes the last row of an empty filtered table")
    return list(range(int(rows[-1]["particle"])))


def intended_particle_ids(filtered_rows):
    return sorted({int(row["particle"]) for row in filtered_rows})


def legacy_general_distance_included(distance_pixels, gui_minimum_pixels):
    return float(distance_pixels) > float(gui_minimum_pixels) / 3.0


def intended_general_distance_included(distance_pixels, gui_minimum_pixels):
    return float(distance_pixels) >= float(gui_minimum_pixels)


def legacy_deformability_distance_included(signed_distance_pixels, roi_width_pixels):
    distance = float(signed_distance_pixels)
    width = float(roi_width_pixels)
    return distance < width and distance > width / 3.0


def legacy_adhesion_distance_included(signed_distance_pixels, roi_width_pixels):
    return float(signed_distance_pixels) < float(roi_width_pixels)


def track_rows(rows, particle_id):
    selected = [row for row in rows if int(row["particle"]) == int(particle_id)]
    if not selected:
        raise IndexError(f"particle {particle_id} has no rows")
    return selected


def measure_track(track, fps, micrometres_per_pixel, displacement="euclidean", zero_duration="raise"):
    modes = {
        "euclidean": euclidean_endpoint_displacement,
        "signed_x": signed_x_endpoint_displacement,
        "absolute_x": absolute_x_endpoint_displacement,
    }
    if displacement not in modes:
        raise ValueError(f"unsupported displacement mode: {displacement}")
    rows = _ordered(track)
    distance_pixels = modes[displacement](rows)
    duration = elapsed_time(rows, fps)
    distance_um = calibrated_distance(distance_pixels, micrometres_per_pixel)
    if zero_duration == "legacy":
        velocity = legacy_velocity(distance_um, duration)
    elif zero_duration == "raise":
        velocity = intended_velocity(distance_um, duration)
    else:
        raise ValueError(f"unsupported zero-duration mode: {zero_duration}")
    return {
        "particle": int(rows[0]["particle"]),
        "start_frame": float(rows[0]["frame"]),
        "end_frame": float(rows[-1]["frame"]),
        "distance_pixels": distance_pixels,
        "distance_micrometres": distance_um,
        "elapsed_seconds": duration,
        "velocity_micrometres_per_second": velocity,
    }


def measure_tracks(particle_ids, measurement_rows, fps, micrometres_per_pixel, displacement="euclidean"):
    return [
        measure_track(
            track_rows(measurement_rows, particle),
            fps,
            micrometres_per_pixel,
            displacement=displacement,
        )
        for particle in particle_ids
    ]


def legacy_area_mass(track):
    rows = _ordered(track)
    return sum(float(row["mass"]) for row in rows) / len(rows) / 255.0


def fluorescence_area_and_intensity(track):
    rows = _ordered(track)
    mean_size = sum(float(row["size"]) for row in rows) / len(rows)
    mean_mass = sum(float(row["mass"]) for row in rows) / len(rows)
    return {"area_pixels": math.pi * mean_size**2, "fluorescence": mean_mass}


def adhesion_area_and_eccentricity(track, micrometres_per_pixel):
    rows = _ordered(track)
    area_pixels = legacy_area_mass(rows)
    mean_ecc = sum(float(row["ecc"]) for row in rows) / len(rows)
    return {
        "area_micrometres_squared": area_pixels * float(micrometres_per_pixel) ** 2,
        "mean_eccentricity_labeled_circularity": mean_ecc,
    }

