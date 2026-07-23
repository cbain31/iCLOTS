"""Structured request-level failures for output services."""

from __future__ import annotations


class OutputServiceError(Exception):
    """Failure that prevents any output target from being attempted."""

    def __init__(
        self,
        *,
        code: str,
        user_message: str,
        detail: str,
        field: str | None = None,
        remediation: str | None = None,
    ) -> None:
        super().__init__(user_message)
        self.code = code
        self.user_message = user_message
        self.detail = detail
        self.field = field
        self.remediation = remediation

    def as_record(self) -> dict[str, str | None]:
        """Return a serialization-neutral error record."""
        return {
            "code": self.code,
            "user_message": self.user_message,
            "detail": self.detail,
            "field": self.field,
            "remediation": self.remediation,
        }


class InvalidDestinationError(OutputServiceError):
    """Destination directory is unavailable or invalid."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            code="invalid_destination",
            user_message="The output destination is not available.",
            detail=detail,
            field="destination_directory",
            remediation="Choose an existing writable directory or request explicit directory creation.",
        )


class InvalidOutputRequestError(OutputServiceError):
    """An output option or filename is invalid."""

    def __init__(self, code: str, detail: str, field: str) -> None:
        super().__init__(
            code=code,
            user_message="The output request is invalid.",
            detail=detail,
            field=field,
            remediation="Review the requested format, filename, and output policy.",
        )

