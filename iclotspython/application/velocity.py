"""Legacy-compatible KLT orchestration independent of Qt and Tk."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from iclotspython.core import velocity as core
from iclotspython.presentation.models import PlotSeries, TableData
from iclotspython.presentation.workflows import NamedTable, PlotPanel, WorkflowResult

from .common import Region, checkpoint, environment_versions, integer, positive
from .video_input import VideoInput, iter_video_rgb, source_id, source_name


@dataclass(frozen=True)
class VelocityRequest:
    video: VideoInput
    micrometres_per_pixel: float = 1.0
    fps: float = 1.0
    bins: int = 7
    corners: int = 500
    block_size: int = 5
    window_x: int = 50
    window_y: int = 20
    roi: Region | None = None


def run_velocity(request: VelocityRequest, progress=None, is_cancelled=None):
    workflow = "velocity_profile"
    checkpoint(workflow, progress, is_cancelled, 0, 1, "Validating velocity request")
    calibration = positive(request.micrometres_per_pixel, "micrometres_per_pixel")
    fps = positive(request.fps, "fps")
    bins = integer(request.bins, "bins")
    corners = integer(request.corners, "corners")
    block = integer(request.block_size, "block_size", 2)
    window = (integer(request.window_y, "window_y", 4) // 2, integer(request.window_x, "window_x", 4) // 2)
    import cv2

    feature_params = dict(maxCorners=corners, qualityLevel=0.01, minDistance=block / 2, blockSize=block)
    lk_params = dict(winSize=window, maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 1, 1))
    frame_ids, positions, velocities = [], [], []
    warnings = ["Legacy KLT: features detected on destination frame, interpreted as source points; swapped/halved search windows, destination y, unsigned 2D displacement, legacy linspace time and upper-edge bins retained."]
    iterator = iter_video_rgb(request.video, request.roi)
    decoded = 0
    try:
        first = next(iterator)
        height = first.shape[0]
        previous = cv2.cvtColor(first, cv2.COLOR_RGB2GRAY)
        decoded = 1
        for index, frame in enumerate(iterator):
            checkpoint(workflow, progress, is_cancelled, index, index + 2, f"Analyzing frame pair {index}")
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            p0 = cv2.goodFeaturesToTrack(gray, mask=None, **feature_params)
            if p0 is not None:
                p1, status, error = cv2.calcOpticalFlowPyrLK(previous, gray, p0, None, **lk_params)
                if p1 is not None and status is not None and p1.any():
                    f, p, v = core.accepted_point_measurements(index, p0[status == 1], p1[status == 1], fps, calibration)
                    frame_ids.extend(map(int, f))
                    positions.extend(map(float, p))
                    velocities.extend(map(float, v))
            previous = gray.copy()
            decoded += 1
    finally:
        iterator.close()
    checkpoint(workflow, progress, is_cancelled, decoded, decoded + 1, "Assembling velocity profile")
    summary = core.frame_summary(frame_ids, velocities, fps)
    profile = core.velocity_profile(positions, velocities, height, bins, calibration)
    tables = (
        NamedTable("All events", TableData(("Frame", "Channel pos. (pix)", "Velocity (µm/s)"), tuple(zip(frame_ids, positions, velocities)))),
        NamedTable("Frame data", TableData(("Frame", "Time (s)", "Min. velocity (µm/s)", "Mean velocity (µm/s)", "Max. velocity (µm/s)"), tuple(tuple(map(float, row)) for row in zip(summary.frames, summary.time_seconds, summary.minimum, summary.mean, summary.maximum)))),
        NamedTable("Profile data", TableData(("Bin coordinate (µm)", "Bin mean velocity (µm/s)", "Bin stdev. velocity (µm/s)"), tuple(tuple(map(float, row)) for row in zip(profile.upper_edges, profile.mean, profile.standard_deviation)))),
        NamedTable("Descriptive statistics", TableData(("n events tracked", "Mean velocity (µm/s)", "Stdev. velocity (µm/s)"), ((len(velocities), float(np.mean(velocities)) if velocities else float("nan"), float(np.std(velocities, ddof=1)) if len(velocities) > 1 else float("nan")),))),
    )
    if not velocities:
        warnings.append("No accepted optical-flow events. Empty tables and undefined profile statistics are retained; no synthetic zero velocities were inserted.")
    plots = (
        PlotPanel("Velocity profile", "Channel position (µm)", "Velocity (µm/s)", (
            PlotSeries("Mean", "", "velocity", tuple(map(float, profile.upper_edges)), tuple(map(float, profile.mean)), "µm", "µm/s"),)),
        PlotPanel("Velocity time course", "Time (s), legacy convention", "Velocity (µm/s)", tuple(
            PlotSeries(name, "", "velocity", tuple(map(float, summary.time_seconds)), tuple(map(float, values)), "s", "µm/s")
            for name, values in (("Min", summary.minimum), ("Mean", summary.mean), ("Max", summary.maximum)))),
    )
    parameters = (("fps", fps), ("micrometres_per_pixel", calibration), ("bins", bins), ("feature_parameters", feature_params), ("lk_parameters", lk_params), ("roi", request.roi))
    provenance = (("contract_version", "1.0"), ("scientific_policy", "legacy-compatible"), ("scientific_core", "iclotspython.core.velocity"),
                  ("source", source_id(request.video)), ("decoded_frames", decoded), ("environment", environment_versions("opencv-python")))
    checkpoint(workflow, progress, is_cancelled, 1, 1, "Analysis complete")
    return WorkflowResult(workflow, tables, plots, parameters, provenance, tuple(warnings), source_name(request.video))
