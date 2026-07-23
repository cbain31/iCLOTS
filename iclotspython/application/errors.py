"""Structured application-layer failures."""

from __future__ import annotations

from enum import Enum


class ErrorCategory(str, Enum):
    """Stable categories suitable for presentation-layer routing."""

    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_SHAPE = "unsupported_input_shape"
    SCIENTIFIC_CALCULATION = "scientific_calculation_failure"
    INTERNAL = "internal_application_failure"
    CANCELLED = "cancelled"


class ApplicationError(Exception):
    """Base exception carrying user- and developer-facing error information."""

    def __init__(
        self,
        *,
        category: ErrorCategory,
        code: str,
        user_message: str,
        detail: str,
        field: str | None = None,
        remediation: str | None = None,
    ) -> None:
        super().__init__(user_message)
        self.category = category
        self.code = code
        self.user_message = user_message
        self.detail = detail
        self.field = field
        self.remediation = remediation

    def as_record(self) -> dict[str, str | None]:
        """Return a serialization-neutral error representation."""
        return {
            "category": self.category.value,
            "code": self.code,
            "user_message": self.user_message,
            "detail": self.detail,
            "field": self.field,
            "remediation": self.remediation,
        }


class RequestValidationError(ApplicationError):
    """Invalid or incomplete caller input."""

    def __init__(
        self,
        code: str,
        user_message: str,
        detail: str,
        *,
        field: str | None = None,
        remediation: str | None = None,
    ) -> None:
        super().__init__(
            category=ErrorCategory.INVALID_INPUT,
            code=code,
            user_message=user_message,
            detail=detail,
            field=field,
            remediation=remediation,
        )


class UnsupportedInputShapeError(ApplicationError):
    """Array shape cannot be represented by the workflow contract."""

    def __init__(self, detail: str, *, field: str = "frames") -> None:
        super().__init__(
            category=ErrorCategory.UNSUPPORTED_SHAPE,
            code="unsupported_frame_shape",
            user_message="Frames must be equally sized three-channel arrays.",
            detail=detail,
            field=field,
            remediation="Supply arrays shaped (height, width, 3) using explicit RGB or BGR ordering.",
        )


class ScientificCalculationError(ApplicationError):
    """The scientific core could not calculate an otherwise valid request."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            category=ErrorCategory.SCIENTIFIC_CALCULATION,
            code="scientific_calculation_failed",
            user_message="The scientific calculation could not be completed.",
            detail=detail,
            remediation="Review the validated inputs and report the developer detail if the problem persists.",
        )


class InternalApplicationError(ApplicationError):
    """Unexpected application orchestration failure."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            category=ErrorCategory.INTERNAL,
            code="internal_application_failure",
            user_message="The workflow could not be completed.",
            detail=detail,
            remediation="Retry the workflow and report the developer detail if the problem persists.",
        )


class WorkflowCancelled(ApplicationError):
    """Caller-requested synchronous workflow cancellation."""

    def __init__(self, detail: str = "Cancellation was requested by the caller.") -> None:
        super().__init__(
            category=ErrorCategory.CANCELLED,
            code="workflow_cancelled",
            user_message="The analysis was cancelled.",
            detail=detail,
        )

