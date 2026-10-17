# SPDX-License-Identifier: MIT
import httpx

from tallyprime import (
    BatchAllocation,
    BillAllocation,
    CostCategoryAllocation,
    CostCentreAllocation,
    InventoryEntry,
    Ledger,
    LedgerEntry,
    TallyClient,
    Unit,
    Voucher,
)
from tallyprime.payloads import as_payload
from tallyprime.protocol import encode_request


def test_ledger_to_payload_scalars() -> None:
    payload = Ledger(name="Cash", parent="Cash-in-Hand").to_payload()
    assert payload == {"NAME": "Cash", "PARENT": "Cash-in-Hand"}


def test_ledger_omits_none_and_empty_lists() -> None:
    payload = Ledger(name="Cash", parent="Cash-in-Hand", email=None).to_payload()
    assert "EMAIL" not in payload
    assert "ADDRESS.LIST" not in payload  # empty list dropped


def test_ledger_string_list_becomes_list_block() -> None:
    payload = Ledger(
        name="ABC", parent="Sundry Debtors", addresses=["Line 1", "Line 2"]
    ).to_payload()
    assert payload["ADDRESS.LIST"] == {
        "@TYPE": "String",
        "ADDRESS": ["Line 1", "Line 2"],
    }


def test_ledger_bool_field_retained_as_bool() -> None:
    # Booleans are converted to Yes/No at the XML layer, not here.
    payload = Ledger(name="X", parent="Y", is_bill_wise=True).to_payload()
    assert payload["ISBILLWISEON"] is True


def test_extra_merges_raw_tags() -> None:
    payload = Ledger(
        name="X", parent="Y", extra={"PARTYGSTIN": "29ABC", "NAME": "override"}
    ).to_payload()
    assert payload["PARTYGSTIN"] == "29ABC"
    # extra is merged last, so it can override a modelled tag
    assert payload["NAME"] == "override"


def test_unit_compound_payload() -> None:
    payload = Unit(
        name="Dozen", is_simple=False, base_units="Doz", additional_units="Pcs", conversion=12
    ).to_payload()
    assert payload == {
        "NAME": "Dozen",
        "ISSIMPLEUNIT": False,
        "BASEUNITS": "Doz",
        "ADDITIONALUNITS": "Pcs",
        "CONVERSION": 12,
    }


def test_voucher_entries_become_repeated_blocks() -> None:
    voucher = Voucher(
        date="20250401",
        entries=[
            LedgerEntry("ABC", "-100.00", is_deemed_positive=True, is_party_ledger=True),
            LedgerEntry("Sales", "100.00", is_deemed_positive=False),
        ],
    )
    payload = voucher.to_payload()
    assert payload["DATE"] == "20250401"
    assert payload["LEDGERENTRIES.LIST"] == [
        {
            "LEDGERNAME": "ABC",
            "AMOUNT": "-100.00",
            "ISDEEMEDPOSITIVE": True,
            "ISPARTYLEDGER": True,
        },
        {"LEDGERNAME": "Sales", "AMOUNT": "100.00", "ISDEEMEDPOSITIVE": False},
    ]


def test_inventory_entry_nested_allocations() -> None:
    entry = InventoryEntry(
        stock_item_name="Widget",
        rate="100.00/Nos",
        amount="1000.00",
        actual_qty="10 Nos",
        billed_qty="10 Nos",
        batch_allocations=[BatchAllocation(godown_name="Main", actual_qty="10 Nos")],
        accounting_allocations=[LedgerEntry("Sales", "1000.00")],
    )
    payload = entry.to_payload()
    assert payload["STOCKITEMNAME"] == "Widget"
    assert payload["BATCHALLOCATIONS.LIST"] == [{"GODOWNNAME": "Main", "ACTUALQTY": "10 Nos"}]
    assert payload["ACCOUNTINGALLOCATIONS.LIST"] == [{"LEDGERNAME": "Sales", "AMOUNT": "1000.00"}]


def test_inventory_invoice_encodes_to_xml() -> None:
    voucher = Voucher(
        date="20250401",
        is_invoice=True,
        entries=[LedgerEntry("ABC Ltd", "-1000.00", is_deemed_positive=True, is_party_ledger=True)],
        inventory_entries=[
            InventoryEntry(
                stock_item_name="Widget",
                amount="1000.00",
                accounting_allocations=[LedgerEntry("Sales", "1000.00")],
            )
        ],
    )
    body = encode_request("voucher.create", {"type": "Sales", **voucher.to_payload()}, format="xml")
    assert "<ISINVOICE>Yes</ISINVOICE>" in body
    assert "<ALLINVENTORYENTRIES.LIST>" in body
    assert "<STOCKITEMNAME>Widget</STOCKITEMNAME>" in body
    assert "<ACCOUNTINGALLOCATIONS.LIST><LEDGERNAME>Sales</LEDGERNAME>" in body


def test_ledger_entry_bill_allocations() -> None:
    entry = LedgerEntry(
        "ABC Ltd",
        "-1000.00",
        is_party_ledger=True,
        bill_allocations=[BillAllocation("INV-001", bill_type="New Ref", amount="-1000.00")],
    )
    payload = entry.to_payload()
    assert payload["BILLALLOCATIONS.LIST"] == [
        {"NAME": "INV-001", "BILLTYPE": "New Ref", "AMOUNT": "-1000.00"}
    ]


def test_ledger_entry_cost_allocations_nested() -> None:
    entry = LedgerEntry(
        "Marketing Exp",
        "-1000.00",
        is_deemed_positive=True,
        cost_allocations=[
            CostCategoryAllocation(
                category="Primary Cost Category",
                cost_centres=[
                    CostCentreAllocation("Delhi", "-600.00"),
                    CostCentreAllocation("Mumbai", "-400.00"),
                ],
            )
        ],
    )
    payload = entry.to_payload()
    cat = payload["CATEGORYALLOCATIONS.LIST"]
    assert cat == [
        {
            "CATEGORY": "Primary Cost Category",
            "COSTCENTREALLOCATIONS.LIST": [
                {"NAME": "Delhi", "AMOUNT": "-600.00"},
                {"NAME": "Mumbai", "AMOUNT": "-400.00"},
            ],
        }
    ]


def test_cost_allocations_encode_to_xml() -> None:
    voucher = Voucher(
        date="20250401",
        entries=[
            LedgerEntry(
                "Marketing Exp",
                "-1000.00",
                is_deemed_positive=True,
                cost_allocations=[
                    CostCategoryAllocation(
                        category="Primary Cost Category",
                        cost_centres=[CostCentreAllocation("Delhi", "-1000.00")],
                    )
                ],
            )
        ],
    )
    body = encode_request(
        "voucher.create", {"type": "Payment", **voucher.to_payload()}, format="xml"
    )
    assert "<CATEGORYALLOCATIONS.LIST><CATEGORY>Primary Cost Category</CATEGORY>" in body
    assert "<COSTCENTREALLOCATIONS.LIST><NAME>Delhi</NAME>" in body


def test_as_payload_accepts_mapping_and_model() -> None:
    assert as_payload({"NAME": "X"}) == {"NAME": "X"}
    assert as_payload(Ledger(name="X", parent="Y"))["NAME"] == "X"


def test_resource_accepts_model_end_to_end() -> None:
    sent: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["body"] = request.content.decode()
        return httpx.Response(
            200, text="<RESPONSE><CREATED>1</CREATED><ERRORS>0</ERRORS></RESPONSE>"
        )

    client = TallyClient()
    client._client = httpx.Client(
        base_url=client.base_url,
        transport=httpx.MockTransport(handler),
    )
    try:
        result = client.ledgers.create(
            Ledger(name="ABC", parent="Sundry Debtors", addresses=["Line 1"])
        )
    finally:
        client.close()

    assert result.created == 1
    assert '<LEDGER Action="Create">' in sent["body"]
    assert "<NAME>ABC</NAME>" in sent["body"]
    assert '<ADDRESS.LIST TYPE="String"><ADDRESS>Line 1</ADDRESS></ADDRESS.LIST>' in sent["body"]
