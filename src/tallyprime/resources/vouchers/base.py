# SPDX-License-Identifier: MIT
"""Shared implementation for voucher-type resources."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tallyprime.resources._base import Resource

if TYPE_CHECKING:
    from tallyprime.client import TallyClient


class VoucherTypeResource(Resource):
    """Operations for a single voucher type (sales, purchase, etc.).

    Args:
        client: The owning :class:`~tallyprime.client.TallyClient`.
        voucher_type: The TallyPrime voucher type name, e.g. ``"Sales"``.
    """

    def __init__(self, client: TallyClient, voucher_type: str) -> None:
        super().__init__(client)
        self.voucher_type = voucher_type

    def create(self, data: Mapping[str, Any]) -> Any:
        """Create a new voucher of this type."""
        return self._request("voucher.create", {"type": self.voucher_type, **data})

    def alter(self, voucher_id: str, data: Mapping[str, Any]) -> Any:
        """Alter an existing voucher identified by ``voucher_id``."""
        return self._request(
            "voucher.alter",
            {"type": self.voucher_type, "id": voucher_id, **data},
        )

    def delete(self, voucher_id: str) -> Any:
        """Delete the voucher identified by ``voucher_id``."""
        return self._request("voucher.delete", {"type": self.voucher_type, "id": voucher_id})

    def pull(self, from_date: str, to_date: str) -> Any:
        """Pull vouchers of this type for the period ``from_date``..``to_date``.

        Dates are accepted in TallyPrime's ``YYYYMMDD`` form.
        """
        return self._request(
            "voucher.pull",
            {"type": self.voucher_type, "from": from_date, "to": to_date},
        )
