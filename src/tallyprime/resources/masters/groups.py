# SPDX-License-Identifier: MIT
"""Accounting group master operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tallyprime.resources._base import Resource


class GroupsResource(Resource):
    """Create, modify, delete and read accounting group masters."""

    def create(self, data: Mapping[str, Any]) -> Any:
        """Create a new group."""
        return self._request("group.create", data)

    def alter(self, name: str, data: Mapping[str, Any]) -> Any:
        """Alter an existing group identified by ``name``."""
        return self._request("group.alter", {"name": name, **data})

    def delete(self, name: str) -> Any:
        """Delete the group identified by ``name``."""
        return self._request("group.delete", {"name": name})

    def pull(self, name: str) -> Any:
        """Pull a single group by ``name``."""
        return self._request("group.pull", {"name": name})

    def pull_all(self) -> Any:
        """Pull all groups."""
        return self._request("group.pull_all")

    def pull_by_group(self, parent: str) -> Any:
        """Pull all groups nested under the ``parent`` group."""
        return self._request("group.pull_by_group", {"parent": parent})
