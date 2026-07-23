"""Headless ROI plot rendering from Phase 3A presentation results."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from iclotspython.presentation.tables import roi_plot_series

from .contracts import (
    IssueSeverity,
    OutputFileRecord,
    OutputFileStatus,
    OutputIssue,
    OutputManifest,
    OverwritePolicy,
    PlotFormat,
    PlotRequest,
)
from .errors import InvalidOutputRequestError
from .paths import (
    build_manifest,
    prepare_destination,
    sanitize_stem,
    success_record,
    validate_filename,
)


_COLORS = {"red": "red", "green": "green", "blue": "blue"}


def suggest_plot_filename(
    result, format: PlotFormat = PlotFormat.PNG
) -> str:
    """Return the deterministic default plot filename."""
    stem = sanitize_stem(result.suggested_export_stem, result.workflow_id)
    return f"{stem}_roi_plot.{format.value}"


def _failed_record(
    path: Path, suggested: str, format_name: str, issue: OutputIssue
) -> OutputFileRecord:
    return OutputFileRecord(
        kind="plot",
        format=format_name,
        path=str(path),
        suggested_filename=suggested,
        status=OutputFileStatus.FAILED,
        issues=(issue,),
    )


def _render_figure(request: PlotRequest, handle) -> None:
    """Render using matplotlib's non-interactive object API."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(
        figsize=(request.width_inches, request.height_inches),
        dpi=request.dpi,
    )
    FigureCanvasAgg(figure)
    area_axis, accumulation_axis = figure.subplots(1, 2)
    for series in roi_plot_series(request.result):
        axis = area_axis if series.quantity == "area" else accumulation_axis
        axis.plot(
            series.x,
            series.y,
            color=_COLORS.get(series.channel, "black"),
            marker="o",
            label=series.channel,
        )
    area_axis.set_title("ROI area")
    area_axis.set_xlabel("Timepoint")
    area_axis.set_ylabel("Area (µm²)")
    accumulation_axis.set_title("ROI accumulation")
    accumulation_axis.set_xlabel("Timepoint")
    accumulation_axis.set_ylabel("Accumulation (µm²/timepoint)")
    if request.result.channels:
        area_axis.legend()
        accumulation_axis.legend()
    figure.suptitle(request.title or "ROI accumulation")
    figure.tight_layout()
    figure.savefig(handle, format=request.format.value, dpi=request.dpi)


def render_roi_plot(request: PlotRequest) -> OutputManifest:
    """Render one ROI result and return an in-memory output manifest."""
    if not isinstance(request.format, PlotFormat):
        raise InvalidOutputRequestError(
            "unsupported_plot_format",
            f"Unsupported plot format: {request.format!r}.",
            "format",
        )
    if not isinstance(request.overwrite, OverwritePolicy):
        raise InvalidOutputRequestError(
            "invalid_overwrite_policy",
            f"Unsupported overwrite policy: {request.overwrite!r}.",
            "overwrite",
        )
    if request.dpi <= 0 or request.width_inches <= 0 or request.height_inches <= 0:
        raise InvalidOutputRequestError(
            "invalid_plot_dimensions",
            "DPI, width, and height must all be positive.",
            "dpi",
        )
    destination = prepare_destination(
        request.destination_directory, request.create_destination
    )
    suggested = suggest_plot_filename(request.result, request.format)
    filename = (
        validate_filename(request.filename, f".{request.format.value}")
        if request.filename is not None
        else suggested
    )
    target = destination / filename
    existed = target.exists()
    if existed and request.overwrite is OverwritePolicy.FAIL_IF_EXISTS:
        issue = OutputIssue(
            severity=IssueSeverity.ERROR,
            code="target_exists",
            message="The plot target already exists.",
            detail="No file was changed because overwrite permission was not granted.",
            path=str(target),
            format=request.format.value,
            remediation="Choose another filename or explicitly request replacement.",
        )
        return build_manifest(
            request.result.workflow_id,
            destination,
            [_failed_record(target, suggested, request.format.value, issue)],
        )

    temporary: Path | None = None
    created_target = False
    try:
        if request.overwrite is OverwritePolicy.REPLACE:
            descriptor, temp_name = tempfile.mkstemp(
                dir=destination, prefix=f".{filename}.", suffix=".tmp"
            )
            os.close(descriptor)
            temporary = Path(temp_name)
            with temporary.open("wb") as handle:
                _render_figure(request, handle)
            os.replace(temporary, target)
        else:
            handle = target.open("xb")
            created_target = True
            with handle:
                _render_figure(request, handle)
    except Exception as exc:
        cleanup = temporary if temporary is not None else target
        if cleanup.exists() and (temporary is not None or created_target):
            cleanup.unlink()
        code = "target_exists" if isinstance(exc, FileExistsError) else "plot_render_failed"
        message = (
            "The plot target already exists."
            if code == "target_exists"
            else "The plot image could not be created."
        )
        issue = OutputIssue(
            severity=IssueSeverity.ERROR,
            code=code,
            message=message,
            detail=f"{type(exc).__name__}: {exc}",
            path=str(target),
            format=request.format.value,
        )
        return build_manifest(
            request.result.workflow_id,
            destination,
            [_failed_record(target, suggested, request.format.value, issue)],
        )

    issues = ()
    status = OutputFileStatus.CREATED
    if existed:
        status = OutputFileStatus.REPLACED
        issues = (
            OutputIssue(
                severity=IssueSeverity.WARNING,
                code="target_replaced",
                message="An existing plot file was replaced.",
                detail="Replacement occurred under the explicit overwrite policy.",
                path=str(target),
                format=request.format.value,
            ),
        )
    record = success_record(
        kind="plot",
        format_name=request.format.value,
        path=target,
        suggested_filename=suggested,
        status=status,
        issues=issues,
    )
    return build_manifest(request.result.workflow_id, destination, [record])
