# SPDX-License-Identifier: MIT
"""Typed payload models for building TallyPrime masters and vouchers.

These dataclasses are an ergonomic alternative to hand-writing the raw
``{"NAME": ..., "PARENT": ...}`` field dicts the resources accept. Each model
declares Pythonic attributes mapped to their TallyPrime XML tags and serialises
to the same dict shape via :meth:`TallyModel.to_payload`, so anywhere a resource
method takes a mapping you can pass a model instead::

    client.ledgers.create(Ledger(name="Cash", parent="Cash-in-Hand"))

Every model also carries an ``extra`` mapping: an escape hatch for the many
Tally fields not modelled explicitly. Keys in ``extra`` are raw Tally tags and
are merged verbatim into the payload::

    Ledger(name="ABC", parent="Sundry Debtors", extra={"PARTYGSTIN": "29ABC..."})

See :mod:`tallyprime.protocol.xml_codec` for how the resulting dicts are
rendered (nested ``.LIST`` blocks, ``bool`` → ``Yes``/``No``, ``@`` attributes).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Union


@dataclass
class TallyModel:
    """Base class for payload models.

    Subclasses are dataclasses whose fields carry a ``tag`` in their metadata
    (the TallyPrime XML tag). :meth:`to_payload` walks those fields and builds
    the field-tag dict the encoder expects, skipping ``None`` and empty lists.
    """

    def to_payload(self) -> dict[str, Any]:
        """Serialise this model to a TallyPrime field-tag mapping."""
        result: dict[str, Any] = {}
        for info in dataclasses.fields(self):
            value = getattr(self, info.name)
            if info.metadata.get("extra"):
                if value:
                    result.update(value)
                continue
            tag = info.metadata.get("tag")
            if tag is None or value is None:
                continue
            if isinstance(value, (list, tuple)) and len(value) == 0:
                continue
            result[str(tag)] = _convert(str(tag), value, info.metadata)
        return result


#: Anything a resource method will accept as payload data.
PayloadLike = Union[Mapping[str, Any], TallyModel]


def as_payload(data: PayloadLike) -> dict[str, Any]:
    """Normalise ``data`` (a model or a mapping) to a plain field-tag dict."""
    if isinstance(data, TallyModel):
        return data.to_payload()
    return dict(data)


def _convert(tag: str, value: Any, metadata: Mapping[str, Any]) -> Any:
    """Convert a single attribute value to its encoder representation."""
    if isinstance(value, TallyModel):
        return value.to_payload()
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        items = list(value)
        if items and isinstance(items[0], TallyModel):
            # A list of nested objects, e.g. voucher ledger entries. The encoder
            # repeats the element once per item.
            return [item.to_payload() for item in items]
        # A list of scalars becomes a Tally ".LIST" block: the wrapper carries a
        # TYPE attribute and repeats the singular inner tag (ADDRESS.LIST/ADDRESS).
        inner = tag[:-5] if tag.endswith(".LIST") else tag
        return {"@TYPE": metadata.get("list_type", "String"), inner: items}
    return value


# --------------------------------------------------------------------------- #
# Field helpers
# --------------------------------------------------------------------------- #
def _req(tag: str) -> Any:
    """A required field mapped to ``tag`` (no default)."""
    return field(metadata={"tag": tag})


def _opt(tag: str) -> Any:
    """An optional field mapped to ``tag`` (defaults to ``None``)."""
    return field(default=None, metadata={"tag": tag})


def _opt_list(tag: str, list_type: str = "String") -> Any:
    """An optional ``.LIST`` field of scalars (defaults to empty)."""
    return field(default_factory=list, metadata={"tag": tag, "list_type": list_type})


def _extra() -> Any:
    """The raw-tag escape-hatch field."""
    return field(default_factory=dict, metadata={"extra": True})


# --------------------------------------------------------------------------- #
# Accounting masters
# --------------------------------------------------------------------------- #
@dataclass
class Group(TallyModel):
    """An accounting group master."""

    name: str = _req("NAME")
    parent: str = _req("PARENT")
    extra: Mapping[str, Any] = _extra()


@dataclass
class Ledger(TallyModel):
    """An accounting ledger master.

    Amount-like fields (``opening_balance``) are passed through verbatim; format
    them as strings if you need a specific precision.
    """

    name: str = _req("NAME")
    parent: str = _req("PARENT")
    opening_balance: str | float | None = _opt("OPENINGBALANCE")
    mailing_names: list[str] = _opt_list("MAILINGNAME.LIST")
    addresses: list[str] = _opt_list("ADDRESS.LIST")
    pincode: str | None = _opt("PINCODE")
    country: str | None = _opt("COUNTRYNAME")
    state: str | None = _opt("LEDSTATENAME")
    email: str | None = _opt("EMAIL")
    phone: str | None = _opt("LEDGERPHONE")
    mobile: str | None = _opt("LEDGERMOBILE")
    gstin: str | None = _opt("PARTYGSTIN")
    is_bill_wise: bool | None = _opt("ISBILLWISEON")
    extra: Mapping[str, Any] = _extra()


# --------------------------------------------------------------------------- #
# Inventory masters
# --------------------------------------------------------------------------- #
@dataclass
class StockGroup(TallyModel):
    """An inventory stock group master."""

    name: str = _req("NAME")
    parent: str | None = _opt("PARENT")
    extra: Mapping[str, Any] = _extra()


@dataclass
class StockItem(TallyModel):
    """An inventory stock item master."""

    name: str = _req("NAME")
    parent: str | None = _opt("PARENT")
    base_units: str | None = _opt("BASEUNITS")
    opening_balance: str | float | None = _opt("OPENINGBALANCE")
    opening_rate: str | None = _opt("OPENINGRATE")
    opening_value: str | float | None = _opt("OPENINGVALUE")
    gst_applicable: str | None = _opt("GSTAPPLICABLE")
    extra: Mapping[str, Any] = _extra()


@dataclass
class Unit(TallyModel):
    """A unit of measure (simple or compound).

    For a simple unit set ``is_simple=True`` and (optionally) ``original_name``.
    For a compound unit set ``is_simple=False`` with ``base_units``,
    ``additional_units`` and ``conversion``; both referenced units must already
    exist.
    """

    name: str = _req("NAME")
    is_simple: bool | None = _opt("ISSIMPLEUNIT")
    original_name: str | None = _opt("ORIGINALNAME")
    decimal_places: int | None = _opt("DECIMALPLACES")
    base_units: str | None = _opt("BASEUNITS")
    additional_units: str | None = _opt("ADDITIONALUNITS")
    conversion: str | float | None = _opt("CONVERSION")
    extra: Mapping[str, Any] = _extra()


# --------------------------------------------------------------------------- #
# Vouchers
# --------------------------------------------------------------------------- #
@dataclass
class LedgerEntry(TallyModel):
    """One ledger line inside a voucher.

    ``amount`` follows Tally's sign convention: **negative = debit, positive =
    credit**. Mark the debit side with ``is_deemed_positive=True`` and the party
    ledger with ``is_party_ledger=True``.
    """

    ledger_name: str = _req("LEDGERNAME")
    amount: str | float = _req("AMOUNT")
    is_deemed_positive: bool | None = _opt("ISDEEMEDPOSITIVE")
    is_party_ledger: bool | None = _opt("ISPARTYLEDGER")
    extra: Mapping[str, Any] = _extra()


@dataclass
class BatchAllocation(TallyModel):
    """A batch/godown allocation inside an inventory entry.

    Used when a stock item is tracked by batch or stored across godowns. The
    quantity fields (``actual_qty``, ``billed_qty``) are passed through verbatim
    — Tally expects them with the unit, e.g. ``"10 Nos"``.
    """

    godown_name: str | None = _opt("GODOWNNAME")
    batch_name: str | None = _opt("BATCHNAME")
    amount: str | float | None = _opt("AMOUNT")
    actual_qty: str | None = _opt("ACTUALQTY")
    billed_qty: str | None = _opt("BILLEDQTY")
    extra: Mapping[str, Any] = _extra()


@dataclass
class InventoryEntry(TallyModel):
    """One stock line inside an inventory (invoice) voucher.

    Renders as an ``ALLINVENTORYENTRIES.LIST`` block. ``rate`` carries the unit,
    e.g. ``"100.00/Nos"``; ``amount`` follows the voucher sign convention
    (negative = debit, positive = credit).

    ``accounting_allocations`` are the ledger postings this stock line maps to
    (the sales/purchase ledger split), reusing :class:`LedgerEntry`.
    ``batch_allocations`` pin the line to batches/godowns. A plain item line can
    omit both.
    """

    stock_item_name: str = _req("STOCKITEMNAME")
    is_deemed_positive: bool | None = _opt("ISDEEMEDPOSITIVE")
    rate: str | None = _opt("RATE")
    amount: str | float | None = _opt("AMOUNT")
    actual_qty: str | None = _opt("ACTUALQTY")
    billed_qty: str | None = _opt("BILLEDQTY")
    batch_allocations: list[BatchAllocation] = field(
        default_factory=list, metadata={"tag": "BATCHALLOCATIONS.LIST"}
    )
    accounting_allocations: list[LedgerEntry] = field(
        default_factory=list, metadata={"tag": "ACCOUNTINGALLOCATIONS.LIST"}
    )
    extra: Mapping[str, Any] = _extra()


@dataclass
class Voucher(TallyModel):
    """A voucher (transaction).

    The voucher *type* comes from the resource namespace you call
    (``client.vouchers.sales`` → ``Sales``), so it is not set on the model.
    ``date`` accepts Tally's ``YYYYMMDD`` or ``DD-Mon-YYYY`` forms. Debit and
    credit totals must balance.

    Use ``entries`` for an accounting voucher. For an inventory invoice set
    ``is_invoice=True`` and populate ``inventory_entries`` (each
    :class:`InventoryEntry` carries its own accounting allocations); the party
    ledger still goes in ``entries``.
    """

    date: str = _req("DATE")
    entries: list[LedgerEntry] = field(default_factory=list, metadata={"tag": "LEDGERENTRIES.LIST"})
    inventory_entries: list[InventoryEntry] = field(
        default_factory=list, metadata={"tag": "ALLINVENTORYENTRIES.LIST"}
    )
    voucher_number: str | int | None = _opt("VOUCHERNUMBER")
    narration: str | None = _opt("NARRATION")
    reference: str | None = _opt("REFERENCE")
    is_invoice: bool | None = _opt("ISINVOICE")
    persisted_view: str | None = _opt("PERSISTEDVIEW")
    extra: Mapping[str, Any] = _extra()


__all__ = [
    "BatchAllocation",
    "Group",
    "InventoryEntry",
    "Ledger",
    "LedgerEntry",
    "PayloadLike",
    "StockGroup",
    "StockItem",
    "TallyModel",
    "Unit",
    "Voucher",
    "as_payload",
]
