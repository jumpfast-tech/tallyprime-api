# SPDX-License-Identifier: MIT
"""The operation registry mapping resource calls to TallyPrime request shapes.

Every resource method hands :func:`tallyprime.resources._base.Resource._request`
a stable operation key (e.g. ``"ledger.create"``). This module maps that key to
an :class:`OperationSpec` describing *how* to build the TallyPrime envelope for
it, independent of the wire format. The XML and JSON encoders both consume these
specs.

Categories
----------
``master_import``
    Create/alter/delete an accounting or inventory master. Encoded as an
    ``Import Data`` request against the ``All Masters`` report, with the master
    object (``<LEDGER>``, ``<GROUP>`` ...) carrying an ``Action`` attribute.
``voucher_import``
    Create/alter/delete/cancel a voucher. Encoded as an ``Import``/``Data``
    request with ``<ID>Vouchers</ID>`` and a ``<VOUCHER>`` object.
``report_export``
    Pull a named report (Trial Balance, Sales Register). Encoded as an
    ``Export``/``Data`` request with ``<STATICVARIABLES>`` carrying the export
    format and optional ``SVFROMDATE``/``SVTODATE``.
``collection_export``
    Pull many masters of one type. Encoded as an ``Export``/``Collection``
    request with a ``<TDL>`` collection definition.
``object_export``
    Pull a single master by name. Encoded as an ``Export``/``Object`` request
    with ``<SUBTYPE>`` and ``<ID TYPE="Name">``.

See ``docs/api-wire-formats.md`` for the full envelope reference these specs
were derived from.
"""

from __future__ import annotations

from dataclasses import dataclass

MASTER_IMPORT = "master_import"
VOUCHER_IMPORT = "voucher_import"
REPORT_EXPORT = "report_export"
COLLECTION_EXPORT = "collection_export"
OBJECT_EXPORT = "object_export"

IMPORT_CATEGORIES = frozenset({MASTER_IMPORT, VOUCHER_IMPORT})


@dataclass(frozen=True)
class OperationSpec:
    """Describes how one operation maps onto a TallyPrime request envelope.

    Attributes:
        category: One of the ``*_import`` / ``*_export`` category constants.
        element: XML object element for imports, e.g. ``"LEDGER"``, ``"VOUCHER"``.
        action: ``Create`` / ``Alter`` / ``Delete`` / ``Cancel`` for imports.
        subtype: Tally object subtype for an object export, e.g. ``"Ledger"``.
        collection_type: Tally object type for a collection export, e.g.
            ``"Ledger"`` (the TDL ``<TYPE>`` of the collection).
        report_id: Report name for a report export, e.g. ``"Trial Balance"``.
    """

    category: str
    element: str | None = None
    action: str | None = None
    subtype: str | None = None
    collection_type: str | None = None
    report_id: str | None = None


def _master(element: str, tally_type: str) -> dict[str, OperationSpec]:
    """Build the standard create/alter/delete/pull specs for a master element.

    Args:
        element: The import XML element, e.g. ``"STOCKITEM"``.
        tally_type: The Tally object type name used in export subtypes and
            collections, e.g. ``"Stock Item"``.
    """
    return {
        "create": OperationSpec(MASTER_IMPORT, element=element, action="Create"),
        "alter": OperationSpec(MASTER_IMPORT, element=element, action="Alter"),
        "delete": OperationSpec(MASTER_IMPORT, element=element, action="Delete"),
        "pull": OperationSpec(OBJECT_EXPORT, subtype=tally_type),
        "pull_all": OperationSpec(COLLECTION_EXPORT, collection_type=tally_type),
        "pull_by_group": OperationSpec(COLLECTION_EXPORT, collection_type=tally_type),
    }


OPERATIONS: dict[str, OperationSpec] = {}

# Accounting and inventory masters: (prefix, import element, Tally type name)
for _name, _element, _type in (
    ("ledger", "LEDGER", "Ledger"),
    ("group", "GROUP", "Group"),
    ("stock_item", "STOCKITEM", "Stock Item"),
    ("stock_group", "STOCKGROUP", "Stock Group"),
):
    for _verb, _spec in _master(_element, _type).items():
        OPERATIONS[f"{_name}.{_verb}"] = _spec
# stock_group has a bespoke pull-by-balance variant instead of pull_by_group
OPERATIONS["stock_group.pull_zero_balance"] = OperationSpec(
    COLLECTION_EXPORT, collection_type="StockGroup"
)

# Units — create is split into simple/compound, both encode identically
OPERATIONS.update(
    {
        "unit.create_simple": OperationSpec(MASTER_IMPORT, element="UNIT", action="Create"),
        "unit.create_compound": OperationSpec(MASTER_IMPORT, element="UNIT", action="Create"),
        "unit.alter": OperationSpec(MASTER_IMPORT, element="UNIT", action="Alter"),
        "unit.delete": OperationSpec(MASTER_IMPORT, element="UNIT", action="Delete"),
        "unit.pull": OperationSpec(OBJECT_EXPORT, subtype="Unit"),
        "unit.pull_all": OperationSpec(COLLECTION_EXPORT, collection_type="Unit"),
    }
)

# Vouchers
OPERATIONS.update(
    {
        "voucher.create": OperationSpec(VOUCHER_IMPORT, element="VOUCHER", action="Create"),
        "voucher.alter": OperationSpec(VOUCHER_IMPORT, element="VOUCHER", action="Alter"),
        "voucher.delete": OperationSpec(VOUCHER_IMPORT, element="VOUCHER", action="Delete"),
        "voucher.pull": OperationSpec(REPORT_EXPORT, report_id="Day Book"),
    }
)

# Reports
OPERATIONS.update(
    {
        "report.trial_balance": OperationSpec(REPORT_EXPORT, report_id="Trial Balance"),
        "report.sales_register": OperationSpec(REPORT_EXPORT, report_id="Sales Register"),
    }
)

# Companies
OPERATIONS["company.pull_all"] = OperationSpec(COLLECTION_EXPORT, collection_type="Company")


def get_spec(operation: str) -> OperationSpec:
    """Return the :class:`OperationSpec` for ``operation``.

    Raises:
        KeyError: If the operation key is not registered (a library bug).
    """
    return OPERATIONS[operation]
