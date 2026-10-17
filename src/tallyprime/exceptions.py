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


class TallyImportError(TallyResponseError):
    """Raised when an import request is rejected by TallyPrime.

    The gateway returns HTTP 200 even for logical failures, reporting the
    problem through ``<STATUS>0</STATUS>`` and ``<LINEERROR>`` messages such as
    ``"Ledger 'X' does not exist!"`` or ``"Voucher totals do not match!"``.
    There may be more than one ``<LINEERROR>`` — all are collected here.

    Attributes:
        line_errors: Every ``<LINEERROR>`` message returned.
        result: The parsed :class:`~tallyprime.models.ImportResult`, if one was
            built before the failure was detected.
    """

    def __init__(
        self,
        message: str,
        *,
        line_errors: list[str] | None = None,
        result: object | None = None,
        body: str | None = None,
    ) -> None:
        super().__init__(message, status_code=200, body=body)
        self.line_errors = line_errors or []
        self.result = result


class TallyFormatError(TallyError):
    """Raised when a requested wire format cannot be used.

    Most commonly raised when ``format="json"`` is selected: native JSON is only
    available on TallyPrime 7.0+ and its body schema is not yet implemented here.
    Use ``format="xml"`` instead.
    """
