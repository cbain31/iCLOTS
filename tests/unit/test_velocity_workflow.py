"""Real OpenCV orchestration compared with independently executed legacy loop."""

from dataclasses import replace

import numpy as np
import pytest

from iclotspython.application.common import Region
from iclotspython.application.errors import RequestValidationError, WorkflowCancelled
from iclotspython.application.velocity import VelocityRequest, run_velocity
from iclotspython.application.video_input import VideoInput, iter_video_rgb
from iclotspython.gui.video_demo import moving_video_demo
from tests.support import velocity_reference as reference

pytestmark = pytest.mark.unit


def legacy_events(frames, fps, calibration):
    import cv2

    previous = cv2.cvtColor(frames[0], cv2.COLOR_RGB2GRAY)
    rows = []
    for count, frame in enumerate(frames[1:]):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        p0 = cv2.goodFeaturesToTrack(gray, mask=None, maxCorners=500, qualityLevel=0.01, minDistance=2.5, blockSize=5)
        if p0 is not None:
            p1, status, _ = cv2.calcOpticalFlowPyrLK(previous, gray, p0, None, winSize=(10, 25), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 1, 1))
            if p1 is not None and p1.any():
                for old, new in zip(p0[status == 1], p1[status == 1]):
                    rows.append((count, float(new[1]), float(np.linalg.norm(new - old) * fps * calibration)))
        previous = gray.copy()
    return rows


def test_real_opencv_events_match_legacy_loop_and_core_summaries():
    frames = moving_video_demo()
    progress = []
    result = run_velocity(VelocityRequest(VideoInput(frames_rgb=frames), fps=10, micrometres_per_pixel=0.5), progress.append)
    expected = legacy_events(frames, 10, 0.5)
    assert len(expected) > 10
    np.testing.assert_allclose(result.table("All events").rows, expected, rtol=1e-6)
    np.testing.assert_allclose(result.table("Descriptive statistics").rows[0][1], np.mean([row[2] for row in expected]))
    assert result.table("Profile data").rows[-1][0] == 48
    assert progress[-1].fraction_complete == 1
    assert all(a.fraction_complete <= b.fraction_complete for a, b in zip(progress, progress[1:]))


def test_empty_detection_is_reported_without_invented_zero_statistics():
    frames = (np.zeros((16, 16, 3), dtype=np.uint8),) * 3
    result = run_velocity(VelocityRequest(VideoInput(frames_rgb=frames)))
    assert not result.table("All events").rows
    assert np.isnan(result.table("Profile data").rows[0][1])
    assert "No accepted" in result.warnings[-1]


@pytest.mark.parametrize("field,value", [("fps", 0), ("fps", float("nan")), ("bins", 1.5), ("block_size", 0), ("window_x", 1)])
def test_bad_parameters(field, value):
    with pytest.raises(RequestValidationError):
        run_velocity(replace(VelocityRequest(VideoInput(frames_rgb=moving_video_demo())), **{field: value}))


def test_input_errors_and_cancellation():
    with pytest.raises(RequestValidationError):
        list(iter_video_rgb(VideoInput(frames_rgb=[])))
    with pytest.raises(RequestValidationError):
        list(iter_video_rgb(VideoInput(frames_rgb=[np.zeros((2, 2))] * 2)))
    with pytest.raises(RequestValidationError):
        list(iter_video_rgb(VideoInput(path="missing.avi")))
    with pytest.raises(RequestValidationError):
        list(iter_video_rgb(VideoInput(frames_rgb=moving_video_demo()), Region(0, 0, 1000, 2)))
    with pytest.raises(WorkflowCancelled):
        run_velocity(VelocityRequest(VideoInput(frames_rgb=moving_video_demo())), is_cancelled=lambda: True)
