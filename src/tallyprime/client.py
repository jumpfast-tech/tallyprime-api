# SPDX-License-Identifier: MIT
"""HTTP client for the TallyPrime gateway.

TallyPrime exposes an HTTP endpoint (default ``http://localhost:9000``) that
accepts request envelopes and returns responses. Modern builds speak JSON;
all builds speak the classic XML dialect. This client defaults to JSON and
lets you opt in to XML per-client or per-request.
"""

from __future__ import annotations

from types import TracebackType
from typing import Literal

import httpx

from tallyprime.exceptions import TallyConnectionError, TallyResponseError
from tallyprime.resources.masters import (
    GroupsResource,
    LedgersResource,
    StockGroupsResource,
    StockItemsResource,
    UnitsResource,
)
from tallyprime.resources.reports import ReportsResource
from tallyprime.resources.vouchers import VouchersResource

Format = Literal["json", "xml"]

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9000
DEFAULT_TIMEOUT = 30.0
DEFAULT_FORMAT: Format = "xml"

_CONTENT_TYPES: dict[Format, str] = {
    "json": "application/json",
    "xml": "text/xml; charset=utf-8",
}


class TallyClient:
    """A client for communicating with a running TallyPrime instance.

    Args:
        host: Hostname where the TallyPrime gateway listens.
        port: Port where the TallyPrime gateway listens.
        format: Wire format to use. ``"xml"`` (default) works on every
            TallyPrime release. ``"json"`` is accepted for forward
            compatibility but currently raises
            :class:`~tallyprime.exceptions.TallyFormatError`: native JSON needs
            TallyPrime 7.0+ and its schema is not implemented yet.
        timeout: Request timeout in seconds.

    Example:
        >>> with TallyClient() as client:
        ...     ledger = client.ledgers.pull("Cash")

    Resource namespaces:
        ledgers, groups, stock_items, stock_groups, units, vouchers, reports
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        *,
        format: Format = DEFAULT_FORMAT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.host = host
        self.port = port
        self.format: Format = format
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

        # Resource namespaces
        self.ledgers = LedgersResource(self)
        self.groups = GroupsResource(self)
        self.stock_items = StockItemsResource(self)
        self.stock_groups = StockGroupsResource(self)
        self.units = UnitsResource(self)
        self.vouchers = VouchersResource(self)
        self.reports = ReportsResource(self)

    @property
    def base_url(self) -> str:
        """The base URL of the TallyPrime gateway."""
        return f"http://{self.host}:{self.port}"

    def send(self, body: str, *, format: Format | None = None) -> str:
        """Send a pre-encoded request body and return the raw response body.

        This is the low-level transport. Resource methods build their payloads
        and call this under the hood; call it directly only when you need to
        send a hand-written envelope.

        Args:
            body: A complete, already-encoded request envelope.
            format: Override the client's wire format for this request.

        Returns:
            The raw response body.

        Raises:
            TallyConnectionError: If the gateway cannot be reached.
            TallyResponseError: If the gateway returns a non-2xx status.
        """
        wire = format or self.format
        try:
            response = self._client.post(
                "/",
                content=body.encode("utf-8"),
                headers={"Content-Type": _CONTENT_TYPES[wire]},
            )
        except httpx.RequestError as exc:
            raise TallyConnectionError(
                f"Could not reach TallyPrime at {self.base_url}: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise TallyResponseError(
                f"TallyPrime returned HTTP {response.status_code}",
                status_code=response.status_code,
                body=response.text,
            )
        return response.text

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> TallyClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
