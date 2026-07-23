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

## Phase 3C — PySide6 application shell

Establish the desktop application shell, navigation, shared styling,
application-state boundaries, background-work policy, and structured
error/progress presentation. Do not migrate workflow calculations into Qt.

## Phase 3D — First modern workflow screen

Implement one PySide6 workflow screen against the Phase 3A ROI service and
Phase 3B plotting/export services. Validate usability and presentation parity
before adding more screens.

## Phase 3E — Incremental workflow migration

Add application services and screens incrementally for device accumulation,
microchannel accumulation, velocity, and tracking. Each migration requires
core parity, request validation, presentation contracts, progress/error
handling, and legacy-output comparison.

