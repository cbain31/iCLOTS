"""Tracking orchestration and independent legacy-policy comparisons."""

from dataclasses import replace

import numpy as np
import pytest

from iclotspython.application.errors import RequestValidationError, ScientificCalculationError, WorkflowCancelled
from iclotspython.application.tracking import TrackingRequest, legacy_fluorescence_input, run_tracking
from iclotspython.application.video_input import VideoInput
from iclotspython.gui.video_demo import moving_video_demo

pytestmark = pytest.mark.unit


def test_legacy_fluorescence_division_reproduces_unresolved_defect():
    actual = legacy_fluorescence_input(np.array([[255, 0]], dtype=np.uint8), np.array([[0, 0]], dtype=np.uint8))
    assert np.isinf(actual[0, 0]) and np.isnan(actual[0, 1])


@pytest.mark.parametrize("policy,search,memory,stub", [("general", 60, 1, 3), ("deformability", 128 / 3, 1, 3), ("transient_adhesion", 12.8, 3, 10)])
def test_detection_linking_parameters_and_core_policies(monkeypatch, policy, search, memory, stub):
    pd = pytest.importorskip("pandas")
    tp = pytest.importorskip("trackpy")
    import cv2

    rows = [{"frame": frame, "particle": particle, "x": frame * 6 + particle * 10, "y": 12 + particle * 12,
             "mass": 1275.0, "size": 2.0, "ecc": 0.2} for frame in range(12) for particle in range(3)]
    features = pd.DataFrame(rows)
    calls = {}

    def batch(frames, diameter, **kwargs):
        calls["batch"] = (frames, diameter, kwargs)
        return features

    def link(frame, **kwargs):
        calls["link"] = kwargs
        return frame

    def filter_stubs(frame, minimum):
        calls["stub"] = minimum
        return frame

    monkeypatch.setattr(tp, "batch", batch)
    monkeypatch.setattr(tp, "link_df", link)
    monkeypatch.setattr(tp, "filter_stubs", filter_stubs)
    frames = moving_video_demo()
    result = run_tracking(TrackingRequest(VideoInput(frames_rgb=frames), policy, fps=10, micrometres_per_pixel=2))
    assert calls["batch"][1] == 15
    assert calls["batch"][2]["minmass"] == 1000
    assert calls["batch"][2]["invert"] is False
    assert calls["batch"][2]["processes"] == 1
    assert calls["link"] == dict(search_range=search, memory=memory, adaptive_stop=1, adaptive_step=0.95)
    assert calls["stub"] == stub
    measured = result.table("Velocity data").rows
    assert len(measured) == 2  # max particle ID deliberately excluded
    for row in measured:
        assert row[4] == 1.1
        assert row[5] == 132
        assert row[6] == pytest.approx(120)
        assert row[7] == 5
    # Independent legacy foreground loop.
    subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
    for rgb, actual in zip(frames, calls["batch"][0]):
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        expected = gray if policy == "transient_adhesion" else cv2.morphologyEx(subtractor.apply(gray), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        np.testing.assert_equal(actual, expected)


def test_real_trackpy_general_workflow():
    pytest.importorskip("trackpy")
    result = run_tracking(TrackingRequest(VideoInput(frames_rgb=moving_video_demo()), minimum_distance=6, minmass=100))
    assert result.table("Trackpy details").rows
    assert result.table("Velocity data").rows
    assert dict(result.parameters)["stub_length"] == 3


@pytest.mark.parametrize("field,value", [("diameter", 14), ("fps", 0), ("search_range", -1), ("minimum_distance", float("nan"))])
def test_tracking_validation(field, value):
    with pytest.raises(RequestValidationError):
        run_tracking(replace(TrackingRequest(VideoInput(frames_rgb=moving_video_demo())), **{field: value}))


def test_fluorescence_nonfinite_input_fails_with_explicit_scientific_issue():
    pytest.importorskip("trackpy")
    frames = (np.zeros((24, 24, 3), dtype=np.uint8),) * 3
    with pytest.raises(ScientificCalculationError, match="scientific calculation") as exc:
        run_tracking(TrackingRequest(VideoInput(frames_rgb=frames), policy="fluorescence"))
    assert "divides foreground" in exc.value.detail


def test_tracking_cancellation_prevents_detection():
    with pytest.raises(WorkflowCancelled):
        run_tracking(TrackingRequest(VideoInput(frames_rgb=moving_video_demo())), is_cancelled=lambda: True)
