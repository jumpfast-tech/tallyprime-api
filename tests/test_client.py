# SPDX-License-Identifier: MIT
import httpx
import pytest

import tallyprime
from tallyprime import TallyClient, TallyConnectionError, TallyResponseError


def test_version_exported() -> None:
    assert isinstance(tallyprime.__version__, str)
    assert tallyprime.__version__.count(".") >= 2


def test_base_url_defaults() -> None:
    with TallyClient() as client:
        assert client.base_url == "http://localhost:9000"


def test_base_url_custom() -> None:
    with TallyClient("tally.local", 9999) as client:
        assert client.base_url == "http://tally.local:9999"


def test_default_format_is_xml() -> None:
    with TallyClient() as client:
        assert client.format == "xml"


def test_resource_namespaces_present() -> None:
    with TallyClient() as client:
        assert client.ledgers is not None
        assert client.groups is not None
        assert client.stock_items is not None
        assert client.stock_groups is not None
        assert client.units is not None
        assert client.vouchers.sales.voucher_type == "Sales"
        assert client.reports.trial_balance is not None


def _mock_client(handler: "object") -> TallyClient:
    client = TallyClient()
    client._client = httpx.Client(
        base_url=client.base_url,
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
    )
    return client


def test_send_returns_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Content-Type"].startswith("text/xml")
        return httpx.Response(200, text="<RESPONSE>OK</RESPONSE>")

    client = _mock_client(handler)
    try:
        assert client.send("<ENVELOPE/>", format="xml") == "<RESPONSE>OK</RESPONSE>"
    finally:
        client.close()


def test_send_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = _mock_client(handler)
    try:
        with pytest.raises(TallyResponseError) as exc_info:
            client.send("<ENVELOPE/>")
    finally:
        client.close()
    assert exc_info.value.status_code == 500
    assert exc_info.value.body == "boom"


def test_send_raises_on_connection_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    client = _mock_client(handler)
    try:
        with pytest.raises(TallyConnectionError):
            client.send("<ENVELOPE/>")
    finally:
        client.close()


def test_client_company_flows_into_request() -> None:
    sent: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["body"] = request.content.decode()
        return httpx.Response(
            200, text="<RESPONSE><CREATED>1</CREATED><ERRORS>0</ERRORS></RESPONSE>"
        )

    client = TallyClient(company="ABC Ltd")
    client._client = httpx.Client(base_url=client.base_url, transport=httpx.MockTransport(handler))
    try:
        client.ledgers.create({"NAME": "Cash", "PARENT": "Cash-in-Hand"})
    finally:
        client.close()
    assert "<SVCURRENTCOMPANY>ABC Ltd</SVCURRENTCOMPANY>" in sent["body"]


def test_companies_list_returns_export_result() -> None:
    raw = (
        "<ENVELOPE><COLLECTION>"
        '<COMPANY NAME="ABC Ltd"><COMPANYNAME>ABC Ltd</COMPANYNAME></COMPANY>'
        '<COMPANY NAME="XYZ Ltd"><COMPANYNAME>XYZ Ltd</COMPANYNAME></COMPANY>'
        "</COLLECTION></ENVELOPE>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=raw)

    client = TallyClient()
    client._client = httpx.Client(base_url=client.base_url, transport=httpx.MockTransport(handler))
    try:
        result = client.companies.list()
    finally:
        client.close()
    assert result.texts("COMPANYNAME") == ["ABC Ltd", "XYZ Ltd"]


def test_ledger_create_roundtrip() -> None:
    sent: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["body"] = request.content.decode()
        return httpx.Response(
            200, text="<RESPONSE><CREATED>1</CREATED><ERRORS>0</ERRORS></RESPONSE>"
        )

    client = _mock_client(handler)
    try:
        result = client.ledgers.create({"NAME": "Cash", "PARENT": "Cash-in-Hand"})
    finally:
        client.close()

    assert result.created == 1
    assert result.ok
    assert '<LEDGER Action="Create">' in sent["body"]
    assert "<NAME>Cash</NAME>" in sent["body"]
    assert "<REPORTNAME>All Masters</REPORTNAME>" in sent["body"]
