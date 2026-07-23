"""Synchronous progress and cancellation contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ProgressStage(str, Enum):
    """Stable ROI workflow stages."""

    VALIDATING = "validating"
    PROCESSING = "processing"
    ASSEMBLING = "assembling"
    COMPLETE = "complete"


@dataclass(frozen=True)
class ProgressEvent:
    """One monotonic workflow progress notification."""

    workflow_id: str
    stage: ProgressStage
    current_step: int
    total_steps: int
    fraction_complete: float
    message: str
    current_frame_label: str | None = None


class ProgressCallback(Protocol):
    """Callable receiving progress events."""

    def __call__(self, event: ProgressEvent) -> None: ...


class CancellationCheck(Protocol):
    """Callable returning true when work should stop."""

    def __call__(self) -> bool: ...

