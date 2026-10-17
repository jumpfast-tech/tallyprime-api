# SPDX-License-Identifier: MIT
import httpx
import pytest

from tallyprime import ExportResult, TallyClient, parse_amount

COLLECTION = """
<ENVELOPE>
  <COLLECTION>
    <LEDGER NAME="Cash"><PARENT>Cash-in-Hand</PARENT></LEDGER>
    <LEDGER NAME="Bank"><PARENT>Bank Accounts</PARENT></LEDGER>
  </COLLECTION>
</ENVELOPE>
"""


def test_find_all_returns_each_match() -> None:
    result = ExportResult.from_raw(COLLECTION)
    ledgers = result.find_all("LEDGER")
    assert len(ledgers) == 2
    assert ledgers[0]["@NAME"] == "Cash"
    assert ledgers[0]["PARENT"] == "Cash-in-Hand"
    assert ledgers[1]["@NAME"] == "Bank"


def test_first_and_texts() -> None:
    result = ExportResult.from_raw(COLLECTION)
    assert result.first("LEDGER")["@NAME"] == "Cash"  # type: ignore[index]
    assert result.texts("PARENT") == ["Cash-in-Hand", "Bank Accounts"]
    assert result.first("MISSING") is None


def test_to_dict_nesting_and_repeated_children() -> None:
    result = ExportResult.from_raw(COLLECTION)
    data = result.to_dict()
    assert isinstance(data, dict)
    collection = data["COLLECTION"]
    assert isinstance(collection, dict)
    # Two LEDGER children collapse to a list.
    assert isinstance(collection["LEDGER"], list)
    assert len(collection["LEDGER"]) == 2


def test_namespaced_tags_are_stripped() -> None:
    raw = '<ENVELOPE xmlns:UDF="TallyUDF"><UDF:FOO>bar</UDF:FOO></ENVELOPE>'
    result = ExportResult.from_raw(raw)
    assert result.texts("FOO") == ["bar"]


def test_from_raw_rejects_malformed_xml() -> None:
    from tallyprime import TallyResponseError

    with pytest.raises(TallyResponseError):
        ExportResult.from_raw("<ENVELOPE><UNCLOSED></ENVELOPE>")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1,29,377.00", 129377.00),
        ("1,000", 1000.0),
        ("500.50 Dr", -500.50),
        ("500.50 Cr", 500.50),
        ("(250.00)", -250.00),
        ("  42  ", 42.0),
    ],
)
def test_parse_amount(text: str, expected: float) -> None:
    assert parse_amount(text) == expected


def test_parse_amount_rejects_non_numeric() -> None:
    with pytest.raises(ValueError):
        parse_amount("  Dr ")


def test_pull_returns_export_result_end_to_end() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=COLLECTION)

    client = TallyClient()
    client._client = httpx.Client(
        base_url=client.base_url,
        transport=httpx.MockTransport(handler),
    )
    try:
        result = client.ledgers.pull_all()
    finally:
        client.close()

    assert isinstance(result, ExportResult)
    assert result.texts("PARENT") == ["Cash-in-Hand", "Bank Accounts"]
