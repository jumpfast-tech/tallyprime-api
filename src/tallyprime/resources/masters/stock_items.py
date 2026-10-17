# SPDX-License-Identifier: MIT
"""Stock item master operations."""

from __future__ import annotations

from typing import Any

from tallyprime.payloads import PayloadLike, as_payload
from tallyprime.resources._base import Resource


class StockItemsResource(Resource):
    """Create, modify, delete and read stock item masters."""

    def create(self, data: PayloadLike) -> Any:
        """Create a stock item from a :class:`~tallyprime.payloads.StockItem` or dict."""
        return self._request("stock_item.create", as_payload(data))

    def alter(self, name: str, data: PayloadLike) -> Any:
        """Alter an existing stock item identified by ``name``."""
        return self._request("stock_item.alter", {"name": name, **as_payload(data)})

    def delete(self, name: str) -> Any:
        """Delete the stock item identified by ``name``."""
        return self._request("stock_item.delete", {"name": name})

    def pull(self, name: str) -> Any:
        """Pull a single stock item by ``name``."""
        return self._request("stock_item.pull", {"name": name})

    def pull_all(self) -> Any:
        """Pull all stock items."""
        return self._request("stock_item.pull_all")

    def pull_by_group(self, group: str) -> Any:
        """Pull all stock items belonging to the ``group`` stock group."""
        return self._request("stock_item.pull_by_group", {"group": group})
