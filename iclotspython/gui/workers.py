"""Qt worker boundary for the synchronous ROI application service."""

from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal, Slot

from iclotspython.application import ROIAccumulationRequest, run_roi_accumulation
from iclotspython.application.errors import ApplicationError, WorkflowCancelled


class AnalysisWorker(QObject):
    """Run the existing synchronous service without moving science into Qt."""

    progress = Signal(object)
    succeeded = Signal(object)
    failed = Signal(object)
    cancelled = Signal(object)
    finished = Signal()

    def __init__(self, request: ROIAccumulationRequest) -> None:
        super().__init__()
        self._request = request
        self._cancelled = threading.Event()

    def request_cancellation(self) -> None:
        """Thread-safe cancellation flag used by the application contract."""
        self._cancelled.set()

    @Slot()
    def run(self) -> None:
        """Call Phase 3A and translate its structured outcomes to Qt signals."""
        try:
            result = run_roi_accumulation(
                self._request,
                progress=self.progress.emit,
                is_cancelled=self._cancelled.is_set,
            )
        except WorkflowCancelled as exc:
            self.cancelled.emit(exc)
        except ApplicationError as exc:
            self.failed.emit(exc)
        except Exception as exc:
            self.failed.emit(exc)
        else:
            self.succeeded.emit(result)
        finally:
            self.finished.emit()

