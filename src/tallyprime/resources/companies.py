# SPDX-License-Identifier: MIT
"""Company operations."""

from __future__ import annotations

from typing import Any

from tallyprime.resources._base import Resource


class CompaniesResource(Resource):
    """Read the companies known to the running TallyPrime instance.

    TallyPrime does not "open" a company over the gateway; instead each request
    targets a company via the ``SVCURRENTCOMPANY`` static variable. Set the
    active company once on the client (``TallyClient(company="ABC Ltd")`` or
    ``client.company = "ABC Ltd"``) and every request carries it; omit it to use
    whichever company is already open in the running instance.
    """

    def list(self) -> Any:
        """List the companies loaded in the running instance.

        Returns an :class:`~tallyprime.models.ExportResult`; the company names
        are available via ``result.texts("COMPANYNAME")`` (or ``find_all``).
        """
        return self._request("company.pull_all")

    # Alias mirroring the master resources' naming.
    def pull_all(self) -> Any:
        """Alias for :meth:`list`."""
        return self._request("company.pull_all")
