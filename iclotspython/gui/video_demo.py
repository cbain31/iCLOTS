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


def tracking_video_demo(policy):
    """Artificial cells accepted by the existing tracking defaults.

    Thirty-two frames give foreground tracks enough travel for both the general
    distance cutoff and the deformability width bounds. All cells stay inside
    the image. Transient adhesion uses compact Gaussian spots whose detected
    masses lie inside its default minimum/maximum interval.
    """
    if policy not in {"general", "deformability", "transient_adhesion"}:
        raise ValueError(f"No validated synthetic tracking demo for {policy!r}")
    yy, xx = np.mgrid[:96, :128]
    frames = []
    for index in range(32):
        if policy == "transient_adhesion":
            gray = np.full((96, 128), 20.0)
            for y, x in ((18, 20), (44, 28), (70, 36)):
                gray += 200 * np.exp(-((xx - x - index * 2) ** 2 + (yy - y) ** 2) / (2 * 1.4 ** 2))
            gray = gray.astype(np.uint8)
        else:
            gray = np.full((96, 128), 20, dtype=np.uint8)
            for y, x in ((18, 16), (44, 24), (70, 32)):
                gray[y:y + 7, x + index * 2:x + index * 2 + 7] = 220
        rgb = np.repeat(gray[:, :, None], 3, axis=2)
        rgb.setflags(write=False)
        frames.append(rgb)
    return tuple(frames)
