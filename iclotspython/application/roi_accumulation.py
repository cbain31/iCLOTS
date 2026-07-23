"""Synchronous headless ROI accumulation application service."""

from __future__ import annotations

import re

from iclotspython.core import accumulation as accumulation_core
from iclotspython.presentation.models import (
    ChannelAccumulationSeries,
    Provenance,
    ROIAccumulationResult,
    WarningCode,
    WarningRecord,
)

from .contracts import (
    ChannelConvention,
    ColorChannel,
    ROIAccumulationRequest,
)
from .errors import ScientificCalculationError, WorkflowCancelled
from .progress import (
    CancellationCheck,
    ProgressCallback,
    ProgressEvent,
    ProgressStage,
)
from .validation import validate_roi_accumulation_request


WORKFLOW_ID = "roi_accumulation"
CONTRACT_VERSION = "1.0"
APPLICATION_VERSION = "unversioned"

_CHANNEL_INDEX = {
    ChannelConvention.BGR: {
        ColorChannel.BLUE: 0,
        ColorChannel.GREEN: 1,
        ColorChannel.RED: 2,
    },
    ChannelConvention.RGB: {
        ColorChannel.RED: 0,
        ColorChannel.GREEN: 1,
        ColorChannel.BLUE: 2,
    },
}


def _emit(
    callback: ProgressCallback | None,
    stage: ProgressStage,
    current: int,
    total: int,
    message: str,
    frame_label: str | None = None,
) -> None:
    if callback is not None:
        callback(
            ProgressEvent(
                workflow_id=WORKFLOW_ID,
                stage=stage,
                current_step=current,
                total_steps=total,
                fraction_complete=current / total,
                message=message,
                current_frame_label=frame_label,
            )
        )


def _check_cancelled(is_cancelled: CancellationCheck | None) -> None:
    if is_cancelled is not None and is_cancelled():
        raise WorkflowCancelled()


def _export_stem(request: ROIAccumulationRequest) -> str:
    candidate = request.metadata.suggested_export_stem
    if not candidate and request.metadata.source_identifiers:
        candidate = request.metadata.source_identifiers[0]
    candidate = candidate or WORKFLOW_ID
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", candidate).strip("._-")
    return normalized or WORKFLOW_ID


def run_roi_accumulation(
    request: ROIAccumulationRequest,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> ROIAccumulationResult:
    """Validate, execute, and present legacy-compatible ROI accumulation."""
    estimated_operations = len(tuple(request.frames)) * len(
        tuple(request.selected_channels)
    )
    total_steps = max(estimated_operations + 3, 3)
    current_step = 0
    _emit(progress, ProgressStage.VALIDATING, current_step, total_steps, "Validating request")
    _check_cancelled(is_cancelled)

    outcome = validate_roi_accumulation_request(request)
    validated = outcome.request
    warnings = list(outcome.warnings)
    current_step = 1
    _emit(progress, ProgressStage.VALIDATING, current_step, total_steps, "Request validated")

    channel_results: list[ChannelAccumulationSeries] = []
    any_signal = False
    for channel in validated.selected_channels:
        threshold = validated.threshold_for(channel)
        layer = _CHANNEL_INDEX[validated.channel_convention][channel]
        observed_counts: list[float] = []
        for label, frame in zip(validated.frame_labels, validated.frames):
            _check_cancelled(is_cancelled)
            try:
                signal_mask = accumulation_core.threshold_channel(
                    frame[:, :, layer], threshold
                )
                observed_counts.append(
                    float(accumulation_core.count_signal_pixels(signal_mask))
                )
            except Exception as exc:
                raise ScientificCalculationError(
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            current_step += 1
            _emit(
                progress,
                ProgressStage.PROCESSING,
                current_step,
                total_steps,
                f"Processed {channel.value} channel for {label}",
                label,
            )

        try:
            pixel_series = accumulation_core.legacy_series_with_zero_baseline(
                observed_counts
            )
            area_values = tuple(
                accumulation_core.calibrated_area(
                    value, validated.micrometres_per_pixel
                )
                for value in pixel_series.values
            )
            accumulation_values = tuple(
                accumulation_core.calibrated_area(
                    value, validated.micrometres_per_pixel
                )
                for value in pixel_series.changes
            )
        except Exception as exc:
            raise ScientificCalculationError(
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if any(observed_counts):
            any_signal = True
        else:
            warnings.append(
                WarningRecord(
                    code=WarningCode.CHANNEL_HAS_NO_SIGNAL,
                    message=f"The selected {channel.value} channel contains no threshold-positive pixels.",
                    detail=f"No value was strictly greater than threshold {threshold}.",
                    field=f"thresholds.{channel.value}",
                    remediation="Confirm the selected channel, convention, and threshold.",
                )
            )
        channel_results.append(
            ChannelAccumulationSeries(
                channel=channel.value,
                threshold=threshold,
                signal_pixels=tuple(float(value) for value in pixel_series.values),
                area_micrometres_squared=area_values,
                accumulation_pixels=tuple(
                    float(value) for value in pixel_series.changes
                ),
                accumulation_micrometres_squared=accumulation_values,
            )
        )

    if not any_signal:
        warnings.append(
            WarningRecord(
                code=WarningCode.EMPTY_SIGNAL_ALL_FRAMES,
                message="No threshold-positive signal was found in any selected channel.",
                detail="The calculation completed normally with zero-valued series.",
                remediation="Confirm channel selection and thresholds if signal was expected.",
            )
        )
    warnings.append(
        WarningRecord(
            code=WarningCode.ARTIFICIAL_BASELINE_INCLUDED,
            message="An artificial zero baseline is included.",
            detail="The first result row is a compatibility baseline, not an observed frame.",
        )
    )

    _check_cancelled(is_cancelled)
    current_step = total_steps - 1
    _emit(
        progress,
        ProgressStage.ASSEMBLING,
        current_step,
        total_steps,
        "Assembling presentation result",
    )

    threshold_pairs = tuple(
        (channel.value, validated.threshold_for(channel))
        for channel in validated.selected_channels
    )
    warning_codes = tuple(warning.code.value for warning in warnings)
    provenance = Provenance(
        workflow_name=WORKFLOW_ID,
        workflow_contract_version=CONTRACT_VERSION,
        application_version=APPLICATION_VERSION,
        scientific_core_module="iclotspython.core.accumulation",
        channel_convention=validated.channel_convention.value,
        selected_channels=tuple(
            channel.value for channel in validated.selected_channels
        ),
        thresholds=threshold_pairs,
        micrometres_per_pixel=validated.micrometres_per_pixel,
        frame_count=len(validated.frames),
        time_convention="caller-supplied or sequential; compatibility baseline at 0",
        artificial_baseline_convention="legacy zero prepended before observed frames",
        source_identifiers=validated.metadata.source_identifiers,
        metadata=validated.metadata.attributes,
        warning_codes=warning_codes,
    )
    result = ROIAccumulationResult(
        workflow_id=WORKFLOW_ID,
        contract_version=CONTRACT_VERSION,
        frame_labels=("baseline", *validated.frame_labels),
        time_values=(0.0, *validated.time_values),
        channels=tuple(channel_results),
        units=(
            ("signal_pixels", "pixels"),
            ("area", "µm²"),
            ("accumulation_pixels", "pixels/timepoint"),
            ("accumulation", "µm²/timepoint"),
            ("time", "timepoint"),
        ),
        parameters=(
            ("channel_convention", validated.channel_convention.value),
            ("selected_channels", tuple(item[0] for item in threshold_pairs)),
            ("thresholds", threshold_pairs),
            ("micrometres_per_pixel", validated.micrometres_per_pixel),
            ("frame_count", len(validated.frames)),
        ),
        warnings=tuple(warnings),
        provenance=provenance,
        suggested_export_stem=_export_stem(request),
    )
    _emit(
        progress,
        ProgressStage.COMPLETE,
        total_steps,
        total_steps,
        "ROI accumulation complete",
    )
    return result
