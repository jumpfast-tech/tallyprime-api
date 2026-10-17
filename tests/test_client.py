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


def test_default_format_is_json() -> None:
    with TallyClient() as client:
        assert client.format == "json"


def test_resource_namespaces_present() -> None:
    with TallyClient() as client:
        assert client.ledgers is not None
        assert client.groups is not None
        assert client.stock_items is not None
        assert client.stock_groups is not None
        assert client.units is not None
        assert client.vouchers.sales.voucher_type == "Sales"
        assert client.reports.trial_balance is not None


def test_resource_stub_raises_not_implemented() -> None:
    with TallyClient() as client, pytest.raises(NotImplementedError):
        client.ledgers.pull("Cash")


def test_send_returns_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Content-Type"].startswith("text/xml")
        return httpx.Response(200, text="<RESPONSE>OK</RESPONSE>")

    client = TallyClient()
    client._client = httpx.Client(base_url=client.base_url, transport=httpx.MockTransport(handler))
    try:
        assert client.send("<ENVELOPE/>", format="xml") == "<RESPONSE>OK</RESPONSE>"
    finally:
        client.close()


def test_send_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = TallyClient()
    client._client = httpx.Client(base_url=client.base_url, transport=httpx.MockTransport(handler))
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

    client = TallyClient()
    client._client = httpx.Client(base_url=client.base_url, transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(TallyConnectionError):
            client.send("<ENVELOPE/>")
    finally:
        client.close()
