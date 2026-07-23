"""Destination, filename, checksum, and manifest helpers."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from .contracts import (
    ManifestStatus,
    OutputFileRecord,
    OutputFileStatus,
    OutputManifest,
)
from .errors import InvalidDestinationError, InvalidOutputRequestError


def prepare_destination(directory: str | Path, create: bool) -> Path:
    """Resolve and validate an explicitly supplied destination directory."""
    destination = Path(directory).resolve()
    if not destination.exists():
        if not create:
            raise InvalidDestinationError(
                f"Destination does not exist: {destination}."
            )
        try:
            destination.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            raise InvalidDestinationError(
                f"Could not create {destination}: {type(exc).__name__}: {exc}"
            ) from exc
    if not destination.is_dir():
        raise InvalidDestinationError(
            f"Destination is not a directory: {destination}."
        )
    if not os.access(destination, os.W_OK):
        raise InvalidDestinationError(
            f"Destination is not writable: {destination}."
        )
    return destination


def sanitize_stem(value: str, fallback: str) -> str:
    """Return a deterministic filesystem-neutral filename stem."""
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return normalized or fallback


def validate_filename(filename: str, suffix: str) -> str:
    """Require a leaf filename with the expected suffix."""
    if not filename or Path(filename).name != filename:
        raise InvalidOutputRequestError(
            "invalid_filename",
            f"Expected a leaf filename, received {filename!r}.",
            "filename",
        )
    if Path(filename).suffix.lower() != suffix.lower():
        raise InvalidOutputRequestError(
            "invalid_filename_suffix",
            f"Filename {filename!r} must end with {suffix}.",
            "filename",
        )
    return filename


def sha256_file(path: Path) -> str:
    """Calculate a file checksum without retaining file contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def success_record(
    *,
    kind: str,
    format_name: str,
    path: Path,
    suggested_filename: str,
    status: OutputFileStatus,
    issues=(),
) -> OutputFileRecord:
    """Build a completed-file manifest record."""
    return OutputFileRecord(
        kind=kind,
        format=format_name,
        path=str(path),
        suggested_filename=suggested_filename,
        status=status,
        size_bytes=path.stat().st_size,
        sha256=sha256_file(path),
        issues=tuple(issues),
    )


def build_manifest(
    workflow_id: str,
    destination: Path,
    records: list[OutputFileRecord],
) -> OutputManifest:
    """Aggregate per-file records into a deterministic manifest."""
    successes = sum(
        record.status in {OutputFileStatus.CREATED, OutputFileStatus.REPLACED}
        for record in records
    )
    if successes == len(records) and records:
        status = ManifestStatus.SUCCESS
    elif successes:
        status = ManifestStatus.PARTIAL
    else:
        status = ManifestStatus.FAILED
    issues = tuple(issue for record in records for issue in record.issues)
    return OutputManifest(
        workflow_id=workflow_id,
        destination_directory=str(destination),
        status=status,
        files=tuple(records),
        issues=issues,
    )

