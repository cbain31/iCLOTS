"""Validation and normalization for application workflow requests."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from iclotspython.presentation.models import WarningCode, WarningRecord

from .contracts import (
    ChannelConvention,
    ColorChannel,
    ROIAccumulationRequest,
    WorkflowMetadata,
)
from .errors import RequestValidationError, UnsupportedInputShapeError


@dataclass(frozen=True)
class ValidatedROIAccumulationRequest:
    """Normalized immutable request used by the ROI service."""

    frames: tuple[NDArray[np.generic], ...]
    selected_channels: tuple[ColorChannel, ...]
    thresholds: tuple[tuple[ColorChannel, float], ...]
    micrometres_per_pixel: float
    channel_convention: ChannelConvention
    frame_labels: tuple[str, ...]
    time_values: tuple[float, ...]
    metadata: WorkflowMetadata

    def threshold_for(self, channel: ColorChannel) -> float:
        """Return the validated threshold for a selected channel."""
        return dict(self.thresholds)[channel]


@dataclass(frozen=True)
class ValidationOutcome:
    """Validated request plus non-fatal normalization warnings."""

    request: ValidatedROIAccumulationRequest
    warnings: tuple[WarningRecord, ...]


def _channel(value: ColorChannel | str) -> ColorChannel:
    try:
        return value if isinstance(value, ColorChannel) else ColorChannel(str(value).lower())
    except ValueError as exc:
        raise RequestValidationError(
            "unsupported_selected_channel",
            "A selected channel is not supported.",
            f"Unsupported channel value: {value!r}.",
            field="selected_channels",
            remediation="Select one or more of red, green, or blue.",
        ) from exc


def _convention(value: ChannelConvention | str | None) -> ChannelConvention:
    if isinstance(value, ChannelConvention):
        return value
    try:
        return ChannelConvention(str(value).upper())
    except ValueError as exc:
        raise RequestValidationError(
            "ambiguous_channel_convention",
            "The channel ordering must be specified explicitly.",
            f"Expected RGB or BGR, received {value!r}.",
            field="channel_convention",
            remediation="Set channel_convention to ChannelConvention.RGB or ChannelConvention.BGR.",
        ) from exc


def _threshold_mapping(
    request: ROIAccumulationRequest,
) -> dict[ColorChannel, float]:
    normalized: dict[ColorChannel, float] = {}
    for key, value in request.thresholds.items():
        normalized[_channel(key)] = value
    return normalized


def validate_roi_accumulation_request(
    request: ROIAccumulationRequest,
) -> ValidationOutcome:
    """Validate and defensively copy an ROI accumulation request."""
    raw_frames = tuple(request.frames)
    if not raw_frames:
        raise RequestValidationError(
            "no_frames",
            "At least one frame is required.",
            "The request contained no frame arrays.",
            field="frames",
            remediation="Supply one or more in-memory three-channel arrays.",
        )

    convention = _convention(request.channel_convention)
    selected = tuple(_channel(channel) for channel in request.selected_channels)
    if not selected:
        raise RequestValidationError(
            "no_selected_channels",
            "Select at least one channel.",
            "The selected_channels sequence was empty.",
            field="selected_channels",
        )
    if len(set(selected)) != len(selected):
        raise RequestValidationError(
            "duplicate_selected_channel",
            "Each selected channel may appear only once.",
            f"Selected channels were {selected!r}.",
            field="selected_channels",
        )

    frames: list[NDArray[np.generic]] = []
    expected_shape: tuple[int, ...] | None = None
    for index, raw_frame in enumerate(raw_frames):
        frame = np.asarray(raw_frame)
        if frame.ndim != 3 or frame.shape[-1] != 3:
            raise UnsupportedInputShapeError(
                f"Frame {index} has shape {frame.shape}; expected (height, width, 3)."
            )
        if expected_shape is None:
            expected_shape = frame.shape
        elif frame.shape != expected_shape:
            raise UnsupportedInputShapeError(
                f"Frame {index} has shape {frame.shape}; expected {expected_shape}."
            )
        if not (
            np.issubdtype(frame.dtype, np.integer)
            or np.issubdtype(frame.dtype, np.floating)
        ):
            raise RequestValidationError(
                "unsupported_frame_dtype",
                "Frame values must use a numeric integer or floating dtype.",
                f"Frame {index} uses dtype {frame.dtype}.",
                field="frames",
            )
        if not np.all(np.isfinite(frame)):
            raise RequestValidationError(
                "non_finite_frame_values",
                "Frame arrays must contain only finite values.",
                f"Frame {index} contains NaN or infinite values.",
                field="frames",
            )
        normalized = np.array(frame, copy=True)
        normalized.setflags(write=False)
        frames.append(normalized)

    calibration = float(request.micrometres_per_pixel)
    if not np.isfinite(calibration) or calibration <= 0:
        raise RequestValidationError(
            "invalid_calibration",
            "Micrometres per pixel must be finite and positive.",
            f"Received {request.micrometres_per_pixel!r}.",
            field="micrometres_per_pixel",
            remediation="Enter a finite calibration greater than zero.",
        )

    provided_thresholds = _threshold_mapping(request)
    thresholds: list[tuple[ColorChannel, float]] = []
    warnings: list[WarningRecord] = []
    for channel in selected:
        if channel not in provided_thresholds:
            raise RequestValidationError(
                "missing_selected_channel_threshold",
                f"A threshold is required for the selected {channel.value} channel.",
                f"No threshold was supplied for {channel.value}.",
                field="thresholds",
            )
        threshold = float(provided_thresholds[channel])
        if not np.isfinite(threshold):
            raise RequestValidationError(
                "invalid_threshold",
                "Thresholds must be finite numeric values.",
                f"The {channel.value} threshold was {provided_thresholds[channel]!r}.",
                field=f"thresholds.{channel.value}",
            )
        for index, frame in enumerate(frames):
            if np.issubdtype(frame.dtype, np.integer):
                bounds = np.iinfo(frame.dtype)
                if threshold < bounds.min or threshold > bounds.max:
                    raise RequestValidationError(
                        "threshold_outside_dtype_range",
                        "A threshold is outside the frame dtype range.",
                        f"{channel.value} threshold {threshold} is outside "
                        f"[{bounds.min}, {bounds.max}] for frame {index} ({frame.dtype}).",
                        field=f"thresholds.{channel.value}",
                    )
        observed_min = min(float(np.min(frame)) for frame in frames)
        observed_max = max(float(np.max(frame)) for frame in frames)
        if threshold < observed_min or threshold > observed_max:
            warnings.append(
                WarningRecord(
                    code=WarningCode.DTYPE_RANGE_MISMATCH,
                    message=f"The {channel.value} threshold is outside the observed data range.",
                    detail=f"Threshold {threshold}; observed range [{observed_min}, {observed_max}].",
                    field=f"thresholds.{channel.value}",
                    remediation="Confirm the array scale and threshold units.",
                )
            )
        thresholds.append((channel, threshold))

    frame_count = len(frames)
    if request.frame_labels is None:
        labels = tuple(f"frame_{index + 1:04d}" for index in range(frame_count))
        warnings.append(
            WarningRecord(
                code=WarningCode.FRAME_LABELS_AUTOGENERATED,
                message="Frame labels were generated automatically.",
                detail="Sequential frame_0001-style labels were used.",
                field="frame_labels",
            )
        )
    else:
        labels = tuple(str(label) for label in request.frame_labels)
        if len(labels) != frame_count:
            raise RequestValidationError(
                "incorrect_frame_label_count",
                "The frame-label count must match the frame count.",
                f"Received {len(labels)} labels for {frame_count} frames.",
                field="frame_labels",
            )

    if request.time_values is None:
        time_values = tuple(float(index + 1) for index in range(frame_count))
        warnings.append(
            WarningRecord(
                code=WarningCode.TIME_VALUES_AUTOGENERATED,
                message="Time values were generated automatically.",
                detail="Sequential timepoints 1..N were used; baseline remains timepoint 0.",
                field="time_values",
            )
        )
    else:
        time_values = tuple(float(value) for value in request.time_values)
        if len(time_values) != frame_count:
            raise RequestValidationError(
                "incorrect_time_value_count",
                "The time-value count must match the frame count.",
                f"Received {len(time_values)} values for {frame_count} frames.",
                field="time_values",
            )
        if not np.all(np.isfinite(time_values)):
            raise RequestValidationError(
                "non_finite_time_values",
                "Time values must be finite.",
                f"Received time values {time_values!r}.",
                field="time_values",
            )
        if any(second <= first for first, second in zip(time_values, time_values[1:])):
            warnings.append(
                WarningRecord(
                    code=WarningCode.NON_MONOTONIC_TIME,
                    message="Supplied time values are not strictly increasing.",
                    detail=f"Received {time_values!r}; values were preserved as supplied.",
                    field="time_values",
                    remediation="Confirm acquisition order before interpreting the plot.",
                )
            )

    source_identifiers = request.metadata.source_identifiers
    if source_identifiers and len(source_identifiers) != frame_count:
        raise RequestValidationError(
            "incorrect_source_identifier_count",
            "Source-identifier count must match the frame count when supplied.",
            f"Received {len(source_identifiers)} identifiers for {frame_count} frames.",
            field="metadata.source_identifiers",
        )

    validated = ValidatedROIAccumulationRequest(
        frames=tuple(frames),
        selected_channels=selected,
        thresholds=tuple(thresholds),
        micrometres_per_pixel=calibration,
        channel_convention=convention,
        frame_labels=labels,
        time_values=time_values,
        metadata=request.metadata,
    )
    return ValidationOutcome(request=validated, warnings=tuple(warnings))

