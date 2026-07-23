# Phase 3 roadmap

The phases below remain separate validation gates. Completing an earlier phase
does not authorize implementation of a later phase.

## Phase 3A — Application and presentation contracts

Define headless request, result, validation, warning, error, progress,
cancellation, provenance, table, plot-data, and export-neutral contracts.
Demonstrate the boundary with in-memory ROI accumulation.

Status: implemented for ROI accumulation.

## Phase 3B — Plotting and export services

Add headless consumers of presentation results for plotting and export.
Define explicit output requests, destination policy, overwrite behavior,
format-specific errors, and parity tests. Scientific calculations remain in
the core; Phase 3A services remain file-neutral.

Status: implemented for ROI PNG, CSV, and XLSX outputs with structured
manifests.

## Phase 3C — PySide6 application shell

Establish the desktop application shell, navigation, shared styling,
application-state boundaries, background-work policy, and structured
error/progress presentation. Do not migrate workflow calculations into Qt.

The approved Phase 3C implementation also includes the first functional ROI
accumulation screen so the shell can be validated against the established
Phase 3A and 3B boundaries rather than against placeholders alone.

Status: implemented for the single-window shell and ROI accumulation. Other
workflow navigation entries are visible but disabled.

## Phase 3D — First workflow review and hardening

Review the ROI screen with collaborators, validate presentation and export
parity against representative legacy outcomes, improve accessibility and
workflow usability, and resolve approved feedback before adding more screens.
No new scientific formulas belong in this phase.

## Phase 3E — Incremental workflow migration

Add application services and screens incrementally for device accumulation,
microchannel accumulation, velocity, and tracking. Each migration requires
core parity, request validation, presentation contracts, progress/error
handling, and legacy-output comparison.
