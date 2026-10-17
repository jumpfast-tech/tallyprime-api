# SPDX-License-Identifier: MIT
"""Ledger master operations."""

from __future__ import annotations

from typing import Any

from tallyprime.payloads import PayloadLike, as_payload
from tallyprime.resources._base import Resource


class LedgersResource(Resource):
    """Create, modify, delete and read ledger masters."""

    def create(self, data: PayloadLike) -> Any:
        """Create a new ledger from a :class:`~tallyprime.payloads.Ledger` or dict."""
        return self._request("ledger.create", as_payload(data))

    def alter(self, name: str, data: PayloadLike) -> Any:
        """Alter an existing ledger identified by ``name``."""
        return self._request("ledger.alter", {"name": name, **as_payload(data)})

    def delete(self, name: str) -> Any:
        """Delete the ledger identified by ``name``."""
        return self._request("ledger.delete", {"name": name})

    def pull(self, name: str) -> Any:
        """Pull a single ledger by ``name``."""
        return self._request("ledger.pull", {"name": name})

    def pull_all(self) -> Any:
        """Pull all ledgers."""
        return self._request("ledger.pull_all")

    def pull_by_group(self, group: str) -> Any:
        """Pull all ledgers belonging to ``group``."""
        return self._request("ledger.pull_by_group", {"group": group})
