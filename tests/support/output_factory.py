"""Small deterministic Phase 3B test fixtures."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path

from iclotspython.presentation.models import (
    ChannelAccumulationSeries,
    Provenance,
    ROIAccumulationResult,
    WarningCode,
    WarningRecord,
)


ROOT = Path(__file__).parents[2]


def roi_result(stem: str = "sample ROI") -> ROIAccumulationResult:
    """Return a compact presentation result without running scientific code."""
    warning = WarningRecord(
        code=WarningCode.ARTIFICIAL_BASELINE_INCLUDED,
        message="An artificial zero baseline is included.",
        detail="Synthetic Phase 3B fixture.",
    )
    provenance = Provenance(
        workflow_name="roi_accumulation",
        workflow_contract_version="1.0",
        application_version="unversioned",
        scientific_core_module="iclotspython.core.accumulation",
        channel_convention="BGR",
        selected_channels=("red",),
        thresholds=(("red", 50.0),),
        micrometres_per_pixel=0.5,
        frame_count=2,
        time_convention="synthetic",
        artificial_baseline_convention="legacy zero prepended",
        source_identifiers=("frame-1", "frame-2"),
        metadata=(),
        warning_codes=(warning.code.value,),
    )
    return ROIAccumulationResult(
        workflow_id="roi_accumulation",
        contract_version="1.0",
        frame_labels=("baseline", "first", "second"),
        time_values=(0.0, 1.0, 2.0),
        channels=(
            ChannelAccumulationSeries(
                channel="red",
                threshold=50.0,
                signal_pixels=(0.0, 1.0, 2.0),
                area_micrometres_squared=(0.0, 0.25, 0.5),
                accumulation_pixels=(0.0, 1.0, 1.0),
                accumulation_micrometres_squared=(0.0, 0.25, 0.25),
            ),
        ),
        units=(
            ("signal_pixels", "pixels"),
            ("area", "µm²"),
            ("accumulation", "µm²/timepoint"),
        ),
        parameters=(
            ("micrometres_per_pixel", 0.5),
            ("frame_count", 2),
        ),
        warnings=(warning,),
        provenance=provenance,
        suggested_export_stem=stem,
    )


@contextmanager
def workspace_output_directory():
    """Yield an automatically cleaned directory inside the repository."""
    with tempfile.TemporaryDirectory(
        prefix=".phase3b-test-", dir=ROOT
    ) as directory:
        yield Path(directory)

