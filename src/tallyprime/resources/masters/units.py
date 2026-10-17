# SPDX-License-Identifier: MIT
"""Unit of measure master operations."""

from __future__ import annotations

from typing import Any

from tallyprime.payloads import PayloadLike, as_payload
from tallyprime.resources._base import Resource


class UnitsResource(Resource):
    """Create, modify, delete and read units of measure."""

    def create_simple(self, data: PayloadLike) -> Any:
        """Create a simple (base) unit from a :class:`~tallyprime.payloads.Unit` or dict."""
        return self._request("unit.create_simple", as_payload(data))

    def create_compound(self, data: PayloadLike) -> Any:
        """Create a compound unit from a :class:`~tallyprime.payloads.Unit` or dict."""
        return self._request("unit.create_compound", as_payload(data))

    def alter(self, name: str, data: PayloadLike) -> Any:
        """Alter an existing unit identified by ``name``."""
        return self._request("unit.alter", {"name": name, **as_payload(data)})

    def delete(self, name: str) -> Any:
        """Delete the unit identified by ``name``."""
        return self._request("unit.delete", {"name": name})

    def pull(self, name: str) -> Any:
        """Pull a single unit by ``name``."""
        return self._request("unit.pull", {"name": name})

    def pull_all(self) -> Any:
        """Pull all units."""
        return self._request("unit.pull_all")
