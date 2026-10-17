# SPDX-License-Identifier: MIT
"""Stock group master operations."""

from __future__ import annotations

from typing import Any

from tallyprime.payloads import PayloadLike, as_payload
from tallyprime.resources._base import Resource


class StockGroupsResource(Resource):
    """Create, modify, delete and read stock group masters."""

    def create(self, data: PayloadLike) -> Any:
        """Create a stock group from a :class:`~tallyprime.payloads.StockGroup` or dict."""
        return self._request("stock_group.create", as_payload(data))

    def alter(self, name: str, data: PayloadLike) -> Any:
        """Alter an existing stock group identified by ``name``."""
        return self._request("stock_group.alter", {"name": name, **as_payload(data)})

    def delete(self, name: str) -> Any:
        """Delete the stock group identified by ``name``."""
        return self._request("stock_group.delete", {"name": name})

    def pull(self, name: str) -> Any:
        """Pull a single stock group by ``name``."""
        return self._request("stock_group.pull", {"name": name})

    def pull_all(self) -> Any:
        """Pull all stock groups."""
        return self._request("stock_group.pull_all")

    def pull_zero_balance(self) -> Any:
        """Pull stock groups that currently hold a zero balance."""
        return self._request("stock_group.pull_zero_balance")
