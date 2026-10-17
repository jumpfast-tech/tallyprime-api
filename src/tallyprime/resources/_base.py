# SPDX-License-Identifier: MIT
"""Shared base class for resource namespaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tallyprime.client import TallyClient


class Resource:
    """Base class for a group of related API operations.

    A resource holds a back-reference to its :class:`~tallyprime.client.TallyClient`
    and dispatches encoded requests through it. Concrete resources expose
    high-level methods (``create``, ``alter``, ``pull`` ...) that build a
    payload and hand it to :meth:`_request`.
    """

    def __init__(self, client: TallyClient) -> None:
        self._client = client

    def _request(self, operation: str, payload: Any = None) -> Any:
        """Encode ``payload`` for ``operation``, send it, and decode the reply.

        Wire encoding/decoding (JSON vs XML envelope construction) will live
        here once the protocol layer is implemented.
        """
        raise NotImplementedError(
            f"The TallyPrime protocol layer is not implemented yet. operation={operation!r}"
        )
