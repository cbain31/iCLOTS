"""Discovery and integrity helpers for optional ignored test datasets."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
from typing import Iterable


ENVIRONMENT_VARIABLE = "ICLOTS_TEST_DATA_DIR"
ROI_DATASET_DIRECTORY = "Multiscale_accumulation_surface"
ROI_SEQUENCE_DIRECTORY = "Healthy"
_ROI_FILENAME = re.compile(r"^1_T(?P<time>\d{4})_00001_Overlay\.tif$", re.IGNORECASE)


class LocalTestDataUnavailable(RuntimeError):
    """The opt-in dataset root or requested sequence is unavailable."""


def configured_test_data_root() -> Path:
    """Resolve the caller-configured dataset root without a repository fallback."""
    configured = os.environ.get(ENVIRONMENT_VARIABLE, "").strip()
    if not configured:
        raise LocalTestDataUnavailable(
            f"{ENVIRONMENT_VARIABLE} is not set; optional local-data tests were skipped."
        )
    root = Path(configured).expanduser()
    if not root.is_dir():
        raise LocalTestDataUnavailable(
            f"{ENVIRONMENT_VARIABLE} does not identify an available directory."
        )
    return root.resolve()


def roi_surface_sequence(root: Path) -> tuple[Path, ...]:
    """Return the five Healthy surface-accumulation frames in encoded time order."""
    sequence_directory = root / ROI_DATASET_DIRECTORY / ROI_SEQUENCE_DIRECTORY
    if not sequence_directory.is_dir():
        raise LocalTestDataUnavailable(
            "The configured test-data root does not contain the selected ROI dataset."
        )
    indexed = []
    for path in sequence_directory.iterdir():
        match = _ROI_FILENAME.match(path.name) if path.is_file() else None
        if match:
            indexed.append((int(match.group("time")), path))
    indexed.sort(key=lambda item: item[0])
    paths = tuple(path for _, path in indexed)
    if len(paths) != 5:
        raise LocalTestDataUnavailable(
            "The selected ROI dataset does not contain its expected five-frame sequence."
        )
    return paths


def content_snapshot(paths: Iterable[Path]) -> tuple[tuple[str, int, str], ...]:
    """Return filename, byte count, and SHA-256 without changing source files."""
    records = []
    for path in sorted(paths, key=lambda item: item.name.casefold()):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        records.append((path.name, path.stat().st_size, digest.hexdigest()))
    return tuple(records)


def directory_snapshot(directory: Path) -> tuple[tuple[str, int, str], ...]:
    """Snapshot every immediate source file, detecting additions and changes."""
    return content_snapshot(path for path in directory.iterdir() if path.is_file())
