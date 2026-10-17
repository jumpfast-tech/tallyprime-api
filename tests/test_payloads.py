# SPDX-License-Identifier: MIT
import httpx

from tallyprime import Ledger, LedgerEntry, TallyClient, Unit, Voucher
from tallyprime.payloads import as_payload


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
