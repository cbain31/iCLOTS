"""Headless workflow orchestration and application-facing contracts."""

from .contracts import (
    ChannelConvention,
    ColorChannel,
    ROIAccumulationRequest,
    WorkflowMetadata,
)
from .roi_accumulation import run_roi_accumulation

__all__ = [
    "ChannelConvention",
    "ColorChannel",
    "ROIAccumulationRequest",
    "WorkflowMetadata",
    "run_roi_accumulation",
]

