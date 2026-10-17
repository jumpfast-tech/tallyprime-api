# SPDX-License-Identifier: MIT
"""Report resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tallyprime.resources.reports.sales_register import SalesRegisterResource
from tallyprime.resources.reports.trial_balance import TrialBalanceResource

if TYPE_CHECKING:
    from tallyprime.client import TallyClient


class ReportsResource:
    """Entry point for report operations.

    Example:
        >>> client.reports.trial_balance.pull("20250401", "20250430")
    """

    def __init__(self, client: TallyClient) -> None:
        self.trial_balance = TrialBalanceResource(client)
        self.sales_register = SalesRegisterResource(client)


__all__ = [
    "ReportsResource",
    "SalesRegisterResource",
    "TrialBalanceResource",
]
