"""Immutable input contracts for application workflow services."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from numpy.typing import ArrayLike


class ChannelConvention(str, Enum):
    """Explicit three-channel array ordering."""

    BGR = "BGR"
    RGB = "RGB"


class ColorChannel(str, Enum):
    """Named visible-light channels supported by accumulation workflows."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@dataclass(frozen=True)
class WorkflowMetadata:
    """Caller-supplied, non-personal workflow metadata."""

    source_identifiers: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()
    suggested_export_stem: str | None = None


@dataclass(frozen=True)
class ROIAccumulationRequest:
    """In-memory request for legacy-compatible ROI accumulation."""

    frames: Sequence[ArrayLike]
    selected_channels: Sequence[ColorChannel | str]
    thresholds: Mapping[ColorChannel | str, float]
    micrometres_per_pixel: float
    channel_convention: ChannelConvention | str | None
    frame_labels: Sequence[str] | None = None
    time_values: Sequence[float] | None = None
    metadata: WorkflowMetadata = field(default_factory=WorkflowMetadata)
