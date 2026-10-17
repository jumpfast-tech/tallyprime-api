# SPDX-License-Identifier: MIT
import pytest

from tallyprime.exceptions import TallyFormatError, TallyImportError
from tallyprime.models import ImportResult
from tallyprime.protocol import decode_response, encode_request


def test_encode_group_create() -> None:
    body = encode_request(
        "group.create", {"NAME": "North Debtors", "PARENT": "Sundry Debtors"}, format="xml"
    )
    assert body.startswith("<ENVELOPE>")
    assert '<GROUP Action="Create">' in body
    assert "<NAME>North Debtors</NAME>" in body
    assert "<PARENT>Sundry Debtors</PARENT>" in body


def test_encode_master_alter_uses_name_attribute() -> None:
    body = encode_request("ledger.alter", {"name": "Cash", "PARENT": "Bank Accounts"}, format="xml")
    assert '<LEDGER Action="Alter" NAME="Cash">' in body
    # The control key "name" must not leak into the field body.
    assert "<name>" not in body
    assert "<PARENT>Bank Accounts</PARENT>" in body


def test_encode_master_delete_is_self_closing() -> None:
    body = encode_request("stock_item.delete", {"name": "Widget"}, format="xml")
    assert '<STOCKITEM Action="Delete" NAME="Widget"/>' in body


def test_encode_nested_list_block() -> None:
    body = encode_request(
        "ledger.create",
        {
            "NAME": "ABC",
            "ADDRESS.LIST": {"@TYPE": "String", "ADDRESS": ["Line 1", "Line 2"]},
        },
        format="xml",
    )
    assert '<ADDRESS.LIST TYPE="String">' in body
    assert "<ADDRESS>Line 1</ADDRESS><ADDRESS>Line 2</ADDRESS>" in body


def test_encode_boolean_becomes_yes_no() -> None:
    body = encode_request("unit.create_simple", {"NAME": "Pcs", "ISSIMPLEUNIT": True}, format="xml")
    assert "<ISSIMPLEUNIT>Yes</ISSIMPLEUNIT>" in body


def test_encode_value_is_escaped() -> None:
    body = encode_request("group.create", {"NAME": "A & B <Co>"}, format="xml")
    assert "<NAME>A &amp; B &lt;Co&gt;</NAME>" in body


def test_encode_voucher_create() -> None:
    body = encode_request(
        "voucher.create",
        {
            "type": "Sales",
            "DATE": "20250401",
            "LEDGERENTRIES.LIST": [
                {"LEDGERNAME": "ABC", "ISDEEMEDPOSITIVE": True, "AMOUNT": "-100.00"},
                {"LEDGERNAME": "Sales", "ISDEEMEDPOSITIVE": False, "AMOUNT": "100.00"},
            ],
        },
        format="xml",
    )
    assert "<ID>Vouchers</ID>" in body
    assert '<VOUCHER Action="Create" VCHTYPE="Sales">' in body
    assert "<VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>" in body
    assert body.count("<LEDGERENTRIES.LIST>") == 2


def test_encode_trial_balance_export_with_dates() -> None:
    body = encode_request(
        "report.trial_balance", {"from": "20250401", "to": "20250430"}, format="xml"
    )
    assert "<TALLYREQUEST>Export</TALLYREQUEST>" in body
    assert "<ID>Trial Balance</ID>" in body
    assert '<SVFROMDATE TYPE="Date">20250401</SVFROMDATE>' in body
    assert '<SVTODATE TYPE="Date">20250430</SVTODATE>' in body


def test_encode_collection_export_pull_all() -> None:
    body = encode_request("ledger.pull_all", None, format="xml")
    assert "<TYPE>Collection</TYPE>" in body
    assert "<ID>List of Ledgers</ID>" in body
    assert "<TYPE>Ledger</TYPE>" in body


def test_encode_object_export_pull_single() -> None:
    body = encode_request("ledger.pull", {"name": "Cash"}, format="xml")
    assert "<TYPE>Object</TYPE>" in body
    assert "<SUBTYPE>Ledger</SUBTYPE>" in body
    assert '<ID TYPE="Name">Cash</ID>' in body


def test_decode_import_success() -> None:
    raw = "<RESPONSE><CREATED>2</CREATED><ALTERED>1</ALTERED><ERRORS>0</ERRORS></RESPONSE>"
    result = decode_response("ledger.create", raw, format="xml")
    assert isinstance(result, ImportResult)
    assert result.created == 2
    assert result.altered == 1
    assert result.ok


def test_decode_import_lineerror_raises() -> None:
    raw = (
        "<ENVELOPE><HEADER><STATUS>0</STATUS></HEADER><BODY><DATA>"
        "<LINEERROR>Ledger 'X' does not exist!</LINEERROR>"
        "<ERRORS>1</ERRORS></DATA></BODY></ENVELOPE>"
    )
    with pytest.raises(TallyImportError) as exc_info:
        decode_response("voucher.create", raw, format="xml")
    assert exc_info.value.line_errors == ["Ledger 'X' does not exist!"]
    assert isinstance(exc_info.value.result, ImportResult)


def test_decode_export_returns_raw() -> None:
    raw = "<ENVELOPE><ACCTSINFO><ACCOUNTNAME>Cash</ACCOUNTNAME></ACCTSINFO></ENVELOPE>"
    assert decode_response("report.trial_balance", raw, format="xml") == raw


def test_json_encode_raises_format_error() -> None:
    with pytest.raises(TallyFormatError, match="JSON"):
        encode_request("ledger.create", {"NAME": "Cash"}, format="json")
