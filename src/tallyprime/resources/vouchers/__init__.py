# SPDX-License-Identifier: MIT
"""Voucher (transaction) resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tallyprime.resources.vouchers.base import VoucherTypeResource

if TYPE_CHECKING:
    from tallyprime.client import TallyClient


class VouchersResource:
    """Entry point for voucher operations, grouped by voucher type.

    Example:
        >>> client.vouchers.sales.pull("20250401", "20250430")
    """

    def __init__(self, client: TallyClient) -> None:
        self.payment = VoucherTypeResource(client, "Payment")
        self.receipt = VoucherTypeResource(client, "Receipt")
        self.sales = VoucherTypeResource(client, "Sales")
        self.purchase = VoucherTypeResource(client, "Purchase")


__all__ = ["VoucherTypeResource", "VouchersResource"]
