# SPDX-License-Identifier: MIT
"""Stock item master operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tallyprime.resources._base import Resource


class StockItemsResource(Resource):
    """Create, modify, delete and read stock item masters."""

    def create(self, data: Mapping[str, Any]) -> Any:
        """Create a new stock item."""
        return self._request("stock_item.create", data)

    def alter(self, name: str, data: Mapping[str, Any]) -> Any:
        """Alter an existing stock item identified by ``name``."""
        return self._request("stock_item.alter", {"name": name, **data})

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
