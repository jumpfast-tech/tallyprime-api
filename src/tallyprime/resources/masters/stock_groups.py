# SPDX-License-Identifier: MIT
"""Stock group master operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tallyprime.resources._base import Resource


class StockGroupsResource(Resource):
    """Create, modify, delete and read stock group masters."""

    def create(self, data: Mapping[str, Any]) -> Any:
        """Create a new stock group."""
        return self._request("stock_group.create", data)

    def alter(self, name: str, data: Mapping[str, Any]) -> Any:
        """Alter an existing stock group identified by ``name``."""
        return self._request("stock_group.alter", {"name": name, **data})

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
