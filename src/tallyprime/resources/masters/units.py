# SPDX-License-Identifier: MIT
"""Unit of measure master operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tallyprime.resources._base import Resource


class UnitsResource(Resource):
    """Create, modify, delete and read units of measure."""

    def create_simple(self, data: Mapping[str, Any]) -> Any:
        """Create a simple (base) unit."""
        return self._request("unit.create_simple", data)

    def create_compound(self, data: Mapping[str, Any]) -> Any:
        """Create a compound unit composed of simple units."""
        return self._request("unit.create_compound", data)

    def alter(self, name: str, data: Mapping[str, Any]) -> Any:
        """Alter an existing unit identified by ``name``."""
        return self._request("unit.alter", {"name": name, **data})

    def delete(self, name: str) -> Any:
        """Delete the unit identified by ``name``."""
        return self._request("unit.delete", {"name": name})

    def pull(self, name: str) -> Any:
        """Pull a single unit by ``name``."""
        return self._request("unit.pull", {"name": name})

    def pull_all(self) -> Any:
        """Pull all units."""
        return self._request("unit.pull_all")
