# SPDX-License-Identifier: MIT
"""HTTP client for the TallyPrime XML gateway.

TallyPrime exposes an HTTP endpoint (default ``http://localhost:9000``) that
accepts XML envelopes and returns XML responses. This module provides a thin,
typed wrapper around that endpoint.
"""

from __future__ import annotations

from types import TracebackType

import httpx

from tallyprime.exceptions import TallyConnectionError, TallyResponseError

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9000
DEFAULT_TIMEOUT = 30.0


class TallyClient:
    """A client for communicating with a running TallyPrime instance.

    Args:
        host: Hostname where the TallyPrime gateway listens.
        port: Port where the TallyPrime gateway listens.
        timeout: Request timeout in seconds.

    Example:
        >>> with TallyClient() as client:
        ...     xml = client.send("<ENVELOPE>...</ENVELOPE>")
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    @property
    def base_url(self) -> str:
        """The base URL of the TallyPrime gateway."""
        return f"http://{self.host}:{self.port}"

    def send(self, xml: str) -> str:
        """Send a raw XML request envelope and return the raw XML response.

        Args:
            xml: A complete TallyPrime XML request envelope.

        Returns:
            The raw XML response body.

        Raises:
            TallyConnectionError: If the gateway cannot be reached.
            TallyResponseError: If the gateway returns a non-2xx status.
        """
        try:
            response = self._client.post(
                "/",
                content=xml.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8"},
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
