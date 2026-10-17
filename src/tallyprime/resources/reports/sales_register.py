# SPDX-License-Identifier: MIT
"""Sales Register report operations."""

from __future__ import annotations

from typing import Any

from tallyprime.resources._base import Resource


class SalesRegisterResource(Resource):
    """Pull the Sales Register report."""

    def pull(self, from_date: str, to_date: str) -> Any:
        """Pull the Sales Register for the period ``from_date``..``to_date``.

        Dates are accepted in TallyPrime's ``YYYYMMDD`` form.
        """
        return self._request("report.sales_register", {"from": from_date, "to": to_date})
