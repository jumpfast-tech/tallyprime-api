# SPDX-License-Identifier: MIT
"""Accounting and inventory master resources."""

from tallyprime.resources.masters.groups import GroupsResource
from tallyprime.resources.masters.ledgers import LedgersResource
from tallyprime.resources.masters.stock_groups import StockGroupsResource
from tallyprime.resources.masters.stock_items import StockItemsResource
from tallyprime.resources.masters.units import UnitsResource

__all__ = [
    "GroupsResource",
    "LedgersResource",
    "StockGroupsResource",
    "StockItemsResource",
    "UnitsResource",
]
