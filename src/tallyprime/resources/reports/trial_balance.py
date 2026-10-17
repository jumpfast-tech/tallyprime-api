# SPDX-License-Identifier: MIT
"""Trial Balance report operations."""

from __future__ import annotations

from typing import Any, Literal

from tallyprime.resources._base import Resource

TrialBalanceFormat = Literal["detailed", "plain", "ledger_wise"]


class TrialBalanceResource(Resource):
    """Pull the Trial Balance report in its various formats."""

    def pull(
        self,
        from_date: str,
        to_date: str,
        *,
        format: TrialBalanceFormat = "detailed",
        group: str | None = None,
    ) -> Any:
        """Pull the Trial Balance for a period.

        Args:
            from_date: Period start in ``YYYYMMDD`` form.
            to_date: Period end in ``YYYYMMDD`` form.
            format: Report variant: ``"detailed"``, ``"plain"`` or
                ``"ledger_wise"``.
            group: Restrict the report to a single group when provided.
        """
        return self._request(
            "report.trial_balance",
            {"from": from_date, "to": to_date, "format": format, "group": group},
        )
