"""Deterministic synthetic moving features, never presented as specimen data."""

import numpy as np


def moving_video_demo():
    frames = []
    for index in range(12):
        gray = np.full((96, 128), 20, dtype=np.uint8)
        for y, x in ((18, 16), (44, 45), (70, 72)):
            gray[y:y + 7, x + index * 2:x + index * 2 + 7] = 220
        rgb = np.repeat(gray[:, :, None], 3, axis=2)
        rgb.setflags(write=False)
        frames.append(rgb)
    return tuple(frames)
