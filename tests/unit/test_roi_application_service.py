"""End-to-end ROI accumulation application-service tests."""

from __future__ import annotations

import builtins
import json
import os
from pathlib import Path

import numpy as np
import pytest

from iclotspython.application.contracts import (
    ChannelConvention,
    ColorChannel,
    ROIAccumulationRequest,
    WorkflowMetadata,
)
from iclotspython.application.errors import WorkflowCancelled
from iclotspython.application.progress import ProgressStage
from iclotspython.application.roi_accumulation import run_roi_accumulation
from iclotspython.core import accumulation as accumulation_core
from iclotspython.presentation.models import WarningCode
from tests.support.accumulation_reference import legacy_series_with_zero_baseline


pytestmark = pytest.mark.unit
ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "accumulation" / "fixtures.json"


def _bgr_frame(red, green=None, blue=None):
    red = np.asarray(red, dtype=np.uint8)
    green = np.zeros_like(red) if green is None else np.asarray(green, dtype=np.uint8)
    blue = np.zeros_like(red) if blue is None else np.asarray(blue, dtype=np.uint8)
    return np.dstack((blue, green, red))


def _request(frames, **changes):
    values = {
        "frames": tuple(frames),
        "selected_channels": (ColorChannel.RED,),
        "thresholds": {ColorChannel.RED: 50},
        "micrometres_per_pixel": 0.5,
        "channel_convention": ChannelConvention.BGR,
        "frame_labels": tuple(f"f{index + 1}" for index in range(len(frames))),
        "time_values": tuple(float(index + 1) for index in range(len(frames))),
    }
    values.update(changes)
    return ROIAccumulationRequest(**values)


def test_service_preserves_strict_threshold_calibration_and_positive_change():
    result = run_roi_accumulation(
        _request(
            [
                _bgr_frame([[50, 51], [0, 0]]),
                _bgr_frame([[51, 60], [0, 0]]),
            ]
        )
    )
    channel = result.channels[0]
    assert channel.signal_pixels == (0.0, 1.0, 2.0)
    assert channel.area_micrometres_squared == (0.0, 0.25, 0.5)
    assert channel.accumulation_pixels == (0.0, 1.0, 1.0)
    assert channel.accumulation_micrometres_squared == (0.0, 0.25, 0.25)


def test_service_preserves_signed_negative_accumulation():
    result = run_roi_accumulation(
        _request(
            [
                _bgr_frame([[60, 60], [0, 0]]),
                _bgr_frame([[0, 0], [0, 0]]),
            ]
        )
    )
    assert result.channels[0].accumulation_pixels == (0.0, 2.0, -2.0)


def test_selected_channels_are_processed_independently():
    frame = _bgr_frame(
        red=[[60, 0], [0, 0]],
        blue=[[60, 60], [0, 0]],
    )
    result = run_roi_accumulation(
        _request(
            [frame],
            selected_channels=(ColorChannel.RED, ColorChannel.BLUE),
            thresholds={ColorChannel.RED: 50, ColorChannel.BLUE: 50},
        )
    )
    assert [(series.channel, series.signal_pixels) for series in result.channels] == [
        ("red", (0.0, 1.0)),
        ("blue", (0.0, 2.0)),
    ]


def test_rgb_convention_is_explicitly_supported_without_inference():
    rgb = np.dstack(
        (
            np.asarray([[60]], dtype=np.uint8),
            np.asarray([[0]], dtype=np.uint8),
            np.asarray([[0]], dtype=np.uint8),
        )
    )
    result = run_roi_accumulation(
        _request([rgb], channel_convention=ChannelConvention.RGB)
    )
    assert result.channels[0].signal_pixels == (0.0, 1.0)
    assert result.provenance.channel_convention == "RGB"


def test_empty_signal_is_a_normal_result_with_structured_warnings():
    result = run_roi_accumulation(
        _request([_bgr_frame([[0]])], thresholds={ColorChannel.RED: 10})
    )
    assert result.channels[0].signal_pixels == (0.0, 0.0)
    codes = {warning.code for warning in result.warnings}
    assert WarningCode.CHANNEL_HAS_NO_SIGNAL in codes
    assert WarningCode.EMPTY_SIGNAL_ALL_FRAMES in codes
    assert WarningCode.ARTIFICIAL_BASELINE_INCLUDED in codes


def test_service_is_deterministic_and_does_not_retain_caller_array_aliases():
    frame = _bgr_frame([[60]])
    request = _request([frame])
    first = run_roi_accumulation(request)
    frame[:] = 0
    second = run_roi_accumulation(_request([_bgr_frame([[60]])]))
    assert first == second


def test_service_delegates_to_phase2_core(monkeypatch):
    calls = {"threshold": 0, "series": 0}
    original_threshold = accumulation_core.threshold_channel
    original_series = accumulation_core.legacy_series_with_zero_baseline

    def threshold_spy(*args, **kwargs):
        calls["threshold"] += 1
        return original_threshold(*args, **kwargs)

    def series_spy(*args, **kwargs):
        calls["series"] += 1
        return original_series(*args, **kwargs)

    monkeypatch.setattr(accumulation_core, "threshold_channel", threshold_spy)
    monkeypatch.setattr(
        accumulation_core, "legacy_series_with_zero_baseline", series_spy
    )
    run_roi_accumulation(_request([_bgr_frame([[60]]), _bgr_frame([[70]])]))
    assert calls == {"threshold": 2, "series": 1}


def test_service_matches_phase2_core_and_phase1_reference_fixture():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    masks = fixture["decreasing_masks"]
    frames = [
        _bgr_frame(np.asarray(mask, dtype=np.uint8) * 255)
        for mask in masks
    ]
    result = run_roi_accumulation(_request(frames))
    counts = [
        accumulation_core.count_signal_pixels(mask)
        for mask in masks
    ]
    core = accumulation_core.legacy_series_with_zero_baseline(counts)
    reference = legacy_series_with_zero_baseline(counts)
    assert result.channels[0].signal_pixels == tuple(core.values)
    assert result.channels[0].accumulation_pixels == tuple(core.changes)
    np.testing.assert_array_equal(core.values, reference["areas"])
    np.testing.assert_array_equal(core.changes, reference["changes"])


def test_progress_is_monotonic_and_has_processing_event_per_frame():
    events = []
    result = run_roi_accumulation(
        _request([_bgr_frame([[60]]), _bgr_frame([[70]])]),
        progress=events.append,
    )
    assert result.workflow_id == "roi_accumulation"
    assert events[0].stage is ProgressStage.VALIDATING
    assert events[-1].stage is ProgressStage.COMPLETE
    assert events[0].fraction_complete == 0
    assert events[-1].fraction_complete == 1
    assert all(
        second.fraction_complete >= first.fraction_complete
        for first, second in zip(events, events[1:])
    )
    processing = [
        event for event in events if event.stage is ProgressStage.PROCESSING
    ]
    assert [event.current_frame_label for event in processing] == ["f1", "f2"]


def test_progress_callback_is_optional():
    assert run_roi_accumulation(_request([_bgr_frame([[60]])])).channels


def test_cancellation_stops_processing_with_structured_error():
    calls = 0

    def cancelled():
        nonlocal calls
        calls += 1
        return calls >= 3

    with pytest.raises(WorkflowCancelled) as exc:
        run_roi_accumulation(
            _request([_bgr_frame([[60]]), _bgr_frame([[70]])]),
            is_cancelled=cancelled,
        )
    assert exc.value.code == "workflow_cancelled"
    assert exc.value.category.value == "cancelled"


def test_service_does_not_write_files_or_change_working_directory(monkeypatch):
    original_cwd = os.getcwd()

    def forbidden_open(*args, **kwargs):
        raise AssertionError("service attempted filesystem access")

    def forbidden_chdir(*args, **kwargs):
        raise AssertionError("service attempted to change directory")

    monkeypatch.setattr(builtins, "open", forbidden_open)
    monkeypatch.setattr(os, "chdir", forbidden_chdir)
    monkeypatch.setattr(Path, "write_text", forbidden_open)
    monkeypatch.setattr(Path, "write_bytes", forbidden_open)
    monkeypatch.setattr(Path, "mkdir", forbidden_open)
    run_roi_accumulation(_request([_bgr_frame([[60]])]))
    assert os.getcwd() == original_cwd
