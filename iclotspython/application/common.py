"""Shared application validation, progress and provenance helpers."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import math
import platform

from .errors import RequestValidationError, WorkflowCancelled
from .progress import ProgressEvent, ProgressStage


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int

    def slices(self, shape):
        values = (self.x, self.y, self.width, self.height)
        if any(isinstance(v, bool) or not isinstance(v, int) for v in values):
            invalid("roi", "ROI coordinates and dimensions must be integers.")
        if (self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0
                or self.x + self.width > shape[1] or self.y + self.height > shape[0]):
            invalid("roi", "ROI must be a nonempty rectangle inside the image.")
        return slice(self.y, self.y + self.height), slice(self.x, self.x + self.width)


def invalid(field, message):
    raise RequestValidationError(f"invalid_{field}", message, message, field=field)


def positive(value, field, *, allow_zero=False):
    try:
        number = float(value)
    except (TypeError, ValueError):
        invalid(field, f"{field} must be numeric.")
    if isinstance(value, bool) or not math.isfinite(number) or (
        number < 0 if allow_zero else number <= 0
    ):
        invalid(field, f"{field} must be finite and {'nonnegative' if allow_zero else 'positive'}.")
    return number


def integer(value, field, minimum=1):
    number = positive(value, field, allow_zero=minimum == 0)
    if number != int(number) or number < minimum:
        invalid(field, f"{field} must be an integer at least {minimum}.")
    return int(number)


def checkpoint(workflow, callback, cancelled, current, total, message):
    if cancelled and cancelled():
        raise WorkflowCancelled()
    if callback:
        callback(ProgressEvent(
            workflow_id=workflow, stage=ProgressStage.COMPLETE if current == total else ProgressStage.PROCESSING,
            current_step=current, total_steps=total, fraction_complete=current / total,
            message=message,
        ))


def environment_versions(*dependencies):
    versions = [("python", platform.python_version())]
    for name in ("numpy", *dependencies):
        try:
            versions.append((name, importlib.metadata.version(name)))
        except importlib.metadata.PackageNotFoundError:
            versions.append((name, "unavailable"))
    return tuple(versions)
