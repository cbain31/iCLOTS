"""Immutable requests and results for Phase 3B file-output services."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from iclotspython.presentation.models import ROIAccumulationResult


class PlotFormat(str, Enum):
    """Supported rendered plot formats."""

    PNG = "png"


class ExportFormat(str, Enum):
    """Supported tabular export formats."""

    CSV = "csv"
    EXCEL = "xlsx"


class OverwritePolicy(str, Enum):
    """Explicit target-collision behavior."""

    FAIL_IF_EXISTS = "fail_if_exists"
    REPLACE = "replace"


class FailurePolicy(str, Enum):
    """Behavior after one item in a multi-file export fails."""

    STOP = "stop"
    CONTINUE = "continue"


class OutputFileStatus(str, Enum):
    """Outcome for one requested target."""

    CREATED = "created"
    REPLACED = "replaced"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"


class ManifestStatus(str, Enum):
    """Aggregate output-request outcome."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class IssueSeverity(str, Enum):
    """Structured output issue severity."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class OutputIssue:
    """Warning or failure associated with an output request or file."""

    severity: IssueSeverity
    code: str
    message: str
    detail: str
    path: str | None = None
    format: str | None = None
    remediation: str | None = None


@dataclass(frozen=True)
class OutputFileRecord:
    """Manifest record for one requested file."""

    kind: str
    format: str
    path: str
    suggested_filename: str
    status: OutputFileStatus
    size_bytes: int | None = None
    sha256: str | None = None
    issues: tuple[OutputIssue, ...] = ()


@dataclass(frozen=True)
class OutputManifest:
    """In-memory manifest describing every requested output target."""

    workflow_id: str
    destination_directory: str
    status: ManifestStatus
    files: tuple[OutputFileRecord, ...]
    issues: tuple[OutputIssue, ...] = ()

    @property
    def generated_files(self) -> tuple[OutputFileRecord, ...]:
        """Return successfully created or explicitly replaced files."""
        return tuple(
            record
            for record in self.files
            if record.status
            in {OutputFileStatus.CREATED, OutputFileStatus.REPLACED}
        )


@dataclass(frozen=True)
class PlotRequest:
    """Request to render one ROI result to a plot image."""

    result: ROIAccumulationResult
    destination_directory: str | Path
    filename: str | None = None
    format: PlotFormat = PlotFormat.PNG
    overwrite: OverwritePolicy = OverwritePolicy.FAIL_IF_EXISTS
    create_destination: bool = False
    dpi: int = 150
    width_inches: float = 8.0
    height_inches: float = 4.0
    title: str | None = None


@dataclass(frozen=True)
class ExportRequest:
    """Request to export one ROI result to one or more tabular formats."""

    result: ROIAccumulationResult
    destination_directory: str | Path
    formats: tuple[ExportFormat, ...] = (ExportFormat.CSV,)
    stem: str | None = None
    overwrite: OverwritePolicy = OverwritePolicy.FAIL_IF_EXISTS
    create_destination: bool = False
    failure_policy: FailurePolicy = FailurePolicy.STOP

