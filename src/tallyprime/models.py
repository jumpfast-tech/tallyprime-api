# SPDX-License-Identifier: MIT
"""Typed result objects returned by the client."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ImportResult:
    """Outcome of an import (create / alter / delete) request.

    TallyPrime answers a successful import with a ``<RESPONSE>`` element holding
    a set of counters; a logical failure comes back wrapped in
    ``<ENVELOPE>`` with ``<STATUS>0</STATUS>`` and one or more ``<LINEERROR>``
    messages. **Tally returns HTTP 200 in both cases**, so success is determined
    from these counters, not the status code.

    Attributes:
        created: Number of objects created.
        altered: Number of objects altered.
        deleted: Number of objects deleted.
        cancelled: Number of vouchers cancelled.
        ignored: Number of objects ignored (e.g. duplicates).
        errors: Number of errored lines. ``0`` means success.
        combined: Value of the ``<COMBINED>`` counter.
        last_vch_id: ``<LASTVCHID>`` — id of the last voucher touched.
        last_m_id: ``<LASTMID>`` — id of the last master touched.
        line_errors: All ``<LINEERROR>`` messages, in document order.
        raw: The raw response body, for debugging or re-parsing.
    """

    created: int = 0
    altered: int = 0
    deleted: int = 0
    cancelled: int = 0
    ignored: int = 0
    errors: int = 0
    combined: int = 0
    last_vch_id: int = 0
    last_m_id: int = 0
    line_errors: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def ok(self) -> bool:
        """True when the import reported no errors."""
        return self.errors == 0 and not self.line_errors
