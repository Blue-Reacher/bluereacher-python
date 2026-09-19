"""Errors raised by the Blue Reacher client."""

from __future__ import annotations

from typing import Any, Optional


class BlueReacherError(Exception):
    """Raised when the Blue Reacher API returns a non-2xx response."""

    def __init__(
        self,
        message: str,
        status: int,
        code: Optional[str] = None,
        help: Optional[str] = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.help = help
        self.body = body

    def __str__(self) -> str:  # pragma: no cover - trivial
        base = super().__str__()
        if self.code:
            return f"{base} (status={self.status}, code={self.code})"
        return f"{base} (status={self.status})"
