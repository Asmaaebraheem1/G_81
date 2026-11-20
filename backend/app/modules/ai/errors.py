"""Typed AI failures. The API maps these to documented error codes."""

from __future__ import annotations

from typing import Any


class AiUnavailable(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 503,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}
