# SPDX-License-Identifier: MIT
"""Exception hierarchy for the TallyPrime client."""

from __future__ import annotations


class TallyError(Exception):
    """Base class for all errors raised by this library."""


class TallyConnectionError(TallyError):
    """Raised when the TallyPrime gateway cannot be reached."""


class TallyResponseError(TallyError):
    """Raised when TallyPrime returns an error or unexpected response.

    Attributes:
        status_code: The HTTP status code returned by the gateway, if any.
        body: The raw response body, if available.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
