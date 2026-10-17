# SPDX-License-Identifier: MIT
"""Shared base class for resource namespaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tallyprime.protocol import decode_response, encode_request

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

        Dispatches through :mod:`tallyprime.protocol` using the owning client's
        wire format. Imports return an
        :class:`~tallyprime.models.ImportResult`; exports return an
        :class:`~tallyprime.models.ExportResult`.
        """
        fmt = self._client.format
        body = encode_request(operation, payload, format=fmt)
        raw = self._client.send(body, format=fmt)
        return decode_response(operation, raw, format=fmt)
