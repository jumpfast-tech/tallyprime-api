# SPDX-License-Identifier: MIT
"""XML encoder and response parser for the TallyPrime gateway.

This module turns :class:`~tallyprime.protocol.operations.OperationSpec` plus a
payload into a TallyPrime XML request envelope, and parses the gateway's XML
reply back into Python. It is the authoritative implementation of the dialect
documented in ``docs/api-wire-formats.md``.

Payload → XML conventions
-------------------------
Payloads are plain mappings of Tally field tags to values. The serializer maps
them recursively:

* ``{"NAME": "Cash"}``            → ``<NAME>Cash</NAME>``
* ``True`` / ``False``            → ``<TAG>Yes</TAG>`` / ``<TAG>No</TAG>``
* ``None``                        → the element is omitted
* a nested mapping                → a nested element
* a list                         → the element is repeated once per item
* a key beginning with ``"@"``    → an XML **attribute** of the enclosing element

So a Tally ``.LIST`` block is expressed as::

    {"ADDRESS.LIST": {"@TYPE": "String", "ADDRESS": ["Line 1", "Line 2"]}}

which renders::

    <ADDRESS.LIST TYPE="String"><ADDRESS>Line 1</ADDRESS><ADDRESS>Line 2</ADDRESS></ADDRESS.LIST>
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

from tallyprime.exceptions import TallyImportError, TallyResponseError
from tallyprime.models import ExportResult, ImportResult
from tallyprime.protocol.operations import (
    COLLECTION_EXPORT,
    IMPORT_CATEGORIES,
    MASTER_IMPORT,
    OBJECT_EXPORT,
    REPORT_EXPORT,
    VOUCHER_IMPORT,
    OperationSpec,
)

# Keys that carry request control information rather than Tally field data.
# Resource methods fold identifiers into the payload under these names; the
# encoder lifts them out before serialising the remaining fields.
_CONTROL_KEYS = frozenset(
    {"name", "group", "parent", "type", "id", "from", "to", "format", "company"}
)

_EXPORT_FORMAT = "$$SysName:XML"


# --------------------------------------------------------------------------- #
# Serialisation primitives
# --------------------------------------------------------------------------- #
def _scalar(value: Any) -> str:
    """Render a scalar payload value as Tally expects it."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _render(tag: str, value: Any) -> str:
    """Recursively render ``value`` as one or more ``<tag>`` elements."""
    if value is None:
        return ""
    if isinstance(value, Mapping):
        attrs: dict[str, Any] = {}
        inner: list[str] = []
        for key, sub in value.items():
            if key.startswith("@"):
                attrs[key[1:]] = sub
            else:
                inner.append(_render(key, sub))
        return _wrap(tag, "".join(inner), attrs)
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        return "".join(_render(tag, item) for item in value)
    return _wrap(tag, escape(_scalar(value)), {})


def _wrap(tag: str, inner: str, attrs: Mapping[str, Any]) -> str:
    """Wrap ``inner`` in ``<tag>`` with ``attrs``; self-close when empty."""
    attr_str = "".join(f" {name}={quoteattr(_scalar(val))}" for name, val in attrs.items())
    if inner == "":
        return f"<{tag}{attr_str}/>"
    return f"<{tag}{attr_str}>{inner}</{tag}>"


def _fields(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Drop control keys, keeping only Tally field tags from ``payload``."""
    if not payload:
        return {}
    return {k: v for k, v in payload.items() if k not in _CONTROL_KEYS}


# --------------------------------------------------------------------------- #
# Encoders per category
# --------------------------------------------------------------------------- #
def encode(
    spec: OperationSpec, payload: Mapping[str, Any] | None, company: str | None = None
) -> str:
    """Encode a request for ``spec`` into a TallyPrime XML envelope string.

    ``company`` sets ``SVCURRENTCOMPANY`` on the request so it targets a specific
    loaded company. A ``company`` key in ``payload`` takes precedence; when
    neither is given, TallyPrime uses the currently-open company.
    """
    effective_company = (payload or {}).get("company") or company
    if spec.category == MASTER_IMPORT:
        return _encode_master_import(spec, payload, effective_company)
    if spec.category == VOUCHER_IMPORT:
        return _encode_voucher_import(spec, payload, effective_company)
    if spec.category == REPORT_EXPORT:
        return _encode_report_export(spec, payload, effective_company)
    if spec.category == COLLECTION_EXPORT:
        return _encode_collection_export(spec, payload, effective_company)
    if spec.category == OBJECT_EXPORT:
        return _encode_object_export(spec, payload, effective_company)
    raise TallyResponseError(f"Unsupported operation category: {spec.category!r}")


def _company_svars(company: str | None) -> str:
    """Render a ``<STATICVARIABLES>`` block selecting ``company``, or ``""``."""
    if not company:
        return ""
    return f"<STATICVARIABLES>{_render('SVCURRENTCOMPANY', company)}</STATICVARIABLES>"


def _encode_master_import(
    spec: OperationSpec, payload: Mapping[str, Any] | None, company: str | None = None
) -> str:
    """Build an ``Import Data`` → ``All Masters`` envelope for a master object.

    ::

        <ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
         <BODY><IMPORTDATA>
          <REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>
          <REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
           <LEDGER Action="Create"><NAME>Cash</NAME>...</LEDGER>
          </TALLYMESSAGE></REQUESTDATA>
         </IMPORTDATA></BODY></ENVELOPE>

    For ``Alter``/``Delete`` the existing master is identified by a ``NAME``
    attribute on the object element.
    """
    assert spec.element and spec.action
    obj: dict[str, Any] = {"@Action": spec.action}
    if spec.action in ("Alter", "Delete"):
        name = (payload or {}).get("name")
        if name is None:
            raise TallyResponseError(f"{spec.action} requires a master name")
        obj["@NAME"] = name
    obj.update(_fields(payload))
    message = _render(spec.element, obj)
    return (
        "<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>"
        "<BODY><IMPORTDATA>"
        f"<REQUESTDESC><REPORTNAME>All Masters</REPORTNAME>{_company_svars(company)}</REQUESTDESC>"
        f'<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">{message}</TALLYMESSAGE></REQUESTDATA>'
        "</IMPORTDATA></BODY></ENVELOPE>"
    )


def _encode_voucher_import(
    spec: OperationSpec, payload: Mapping[str, Any] | None, company: str | None = None
) -> str:
    """Build an ``Import`` → ``Vouchers`` envelope for a voucher object.

    ::

        <ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Import</TALLYREQUEST>
          <TYPE>Data</TYPE><ID>Vouchers</ID></HEADER>
         <BODY><DESC></DESC><DATA><TALLYMESSAGE>
           <VOUCHER VCHTYPE="Sales" ACTION="Create">
             <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME> ... </VOUCHER>
         </TALLYMESSAGE></DATA></BODY></ENVELOPE>

    Amount sign convention: **negative = debit, positive = credit**, and the
    debit side is additionally marked ``<ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>``.
    Debit and credit totals must balance.

    .. note::
       Vouchers have no unique name, so ``Alter``/``Delete`` normally identify
       the target by ``DATE`` + ``TAGNAME``/``TAGVALUE``. This client instead
       passes the caller-supplied id through a ``REMOTEID`` attribute, which is
       the idempotent-key mechanism. **This alter/delete path is inferred and
       unverified against a live instance** — see ``docs/api-wire-formats.md``.
    """
    assert spec.element and spec.action
    data = payload or {}
    vtype = data.get("type")
    obj: dict[str, Any] = {"@Action": spec.action}
    if vtype is not None:
        obj["@VCHTYPE"] = vtype
    if spec.action == "Create" and vtype is not None:
        obj["VOUCHERTYPENAME"] = vtype
    if spec.action in ("Alter", "Delete"):
        voucher_id = data.get("id")
        if voucher_id is None:
            raise TallyResponseError(f"{spec.action} requires a voucher id")
        obj["@REMOTEID"] = voucher_id
    obj.update(_fields(payload))
    message = _render(spec.element, obj)
    return (
        "<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Import</TALLYREQUEST>"
        "<TYPE>Data</TYPE><ID>Vouchers</ID></HEADER>"
        f"<BODY><DESC>{_company_svars(company)}</DESC>"
        f"<DATA><TALLYMESSAGE>{message}</TALLYMESSAGE></DATA></BODY></ENVELOPE>"
    )


def _static_variables(payload: Mapping[str, Any] | None, company: str | None = None) -> str:
    """Render the ``<STATICVARIABLES>`` block common to every export.

    Always sets ``SVEXPORTFORMAT`` to XML. Adds ``SVFROMDATE``/``SVTODATE``
    (as ``TYPE="Date"``) when the payload carries ``from``/``to``, and
    ``SVCURRENTCOMPANY`` when a ``company`` is given. Dates are passed through
    verbatim; Tally accepts both ``YYYYMMDD`` and ``DD-Mon-YYYY``.
    """
    data = payload or {}
    parts = [_render("SVEXPORTFORMAT", _EXPORT_FORMAT)]
    if data.get("from") is not None:
        parts.append(_date_var("SVFROMDATE", data["from"]))
    if data.get("to") is not None:
        parts.append(_date_var("SVTODATE", data["to"]))
    if company:
        parts.append(_render("SVCURRENTCOMPANY", company))
    return f"<STATICVARIABLES>{''.join(parts)}</STATICVARIABLES>"


def _date_var(tag: str, value: Any) -> str:
    """Render a ``<TAG TYPE="Date">value</TAG>`` static variable."""
    return f'<{tag} TYPE="Date">{escape(_scalar(value))}</{tag}>'


def _encode_report_export(
    spec: OperationSpec, payload: Mapping[str, Any] | None, company: str | None = None
) -> str:
    """Build an ``Export`` → report envelope.

    ::

        <ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
          <TYPE>Data</TYPE><ID>Trial Balance</ID></HEADER>
         <BODY><DESC><STATICVARIABLES>
           <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
           <SVFROMDATE TYPE="Date">20250401</SVFROMDATE>
           <SVTODATE TYPE="Date">20250430</SVTODATE>
         </STATICVARIABLES></DESC></BODY></ENVELOPE>

    .. note::
       The Trial Balance ``format`` variant and ``group`` filter, and the bare
       ``Sales Register`` report name, are **unverified** — Tally may require a
       ``<TDL>`` report tweak for those. See ``docs/api-wire-formats.md``.
    """
    assert spec.report_id
    return (
        "<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>"
        f"<TYPE>Data</TYPE><ID>{escape(spec.report_id)}</ID></HEADER>"
        f"<BODY><DESC>{_static_variables(payload, company)}</DESC></BODY></ENVELOPE>"
    )


def _encode_collection_export(
    spec: OperationSpec, payload: Mapping[str, Any] | None, company: str | None = None
) -> str:
    """Build an ``Export`` → ``Collection`` envelope pulling many masters.

    ::

        <ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
          <TYPE>Collection</TYPE><ID>List of Ledgers</ID></HEADER>
         <BODY><DESC>
           <STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
           <TDL><TDLMESSAGE>
             <COLLECTION NAME="List of Ledgers" ISINITIALIZE="Yes">
               <TYPE>Ledger</TYPE>
               <NATIVEMETHOD>Name</NATIVEMETHOD><NATIVEMETHOD>Parent</NATIVEMETHOD>
             </COLLECTION>
           </TDLMESSAGE></TDL>
         </DESC></BODY></ENVELOPE>

    When the payload carries ``group``/``parent``, a ``<CHILDOF>`` filter is
    added to restrict the collection to that group. **That filter is inferred
    and unverified.**
    """
    assert spec.collection_type
    data = payload or {}
    name = f"List of {spec.collection_type}s"
    collection_body = [
        _render("TYPE", spec.collection_type),
        _render("NATIVEMETHOD", "Name"),
        _render("NATIVEMETHOD", "Parent"),
    ]
    parent = data.get("group") or data.get("parent")
    if parent is not None:
        collection_body.append(_render("CHILDOF", parent))
    collection = (
        f'<COLLECTION NAME={quoteattr(name)} ISINITIALIZE="Yes">'
        f"{''.join(collection_body)}</COLLECTION>"
    )
    return (
        "<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>"
        f"<TYPE>Collection</TYPE><ID>{escape(name)}</ID></HEADER>"
        "<BODY><DESC>"
        f"{_static_variables(None, company)}"
        f"<TDL><TDLMESSAGE>{collection}</TDLMESSAGE></TDL>"
        "</DESC></BODY></ENVELOPE>"
    )


def _encode_object_export(
    spec: OperationSpec, payload: Mapping[str, Any] | None, company: str | None = None
) -> str:
    """Build an ``Export`` → ``Object`` envelope pulling one master by name.

    ::

        <ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
          <TYPE>Object</TYPE><SUBTYPE>Ledger</SUBTYPE>
          <ID TYPE="Name">Cash</ID></HEADER>
         <BODY><DESC>
           <STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
           <FETCHLIST><FETCH>Name</FETCH><FETCH>Parent</FETCH></FETCHLIST>
         </DESC></BODY></ENVELOPE>
    """
    assert spec.subtype
    name = (payload or {}).get("name")
    if name is None:
        raise TallyResponseError("pull requires a master name")
    return (
        "<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>"
        f"<TYPE>Object</TYPE><SUBTYPE>{escape(spec.subtype)}</SUBTYPE>"
        f'<ID TYPE="Name">{escape(_scalar(name))}</ID></HEADER>'
        "<BODY><DESC>"
        f"{_static_variables(None, company)}"
        "<FETCHLIST><FETCH>Name</FETCH><FETCH>Parent</FETCH></FETCHLIST>"
        "</DESC></BODY></ENVELOPE>"
    )


# --------------------------------------------------------------------------- #
# Response decoding
# --------------------------------------------------------------------------- #
def decode(spec: OperationSpec, raw: str) -> Any:
    """Decode a raw XML response for ``spec``.

    Imports return an :class:`~tallyprime.models.ImportResult` (raising
    :class:`~tallyprime.exceptions.TallyImportError` on a reported failure).
    Exports return an :class:`~tallyprime.models.ExportResult` wrapping the
    parsed tree, with the original XML preserved on ``.raw``.
    """
    if spec.category in IMPORT_CATEGORIES:
        return _decode_import(raw)
    return ExportResult.from_raw(raw)


def _int(root: ET.Element, tag: str) -> int:
    """Return the integer text of the first ``tag`` element, or ``0``."""
    node = root.find(f".//{tag}")
    if node is None or node.text is None:
        return 0
    try:
        return int(node.text.strip())
    except ValueError:
        return 0


def _decode_import(raw: str) -> ImportResult:
    """Parse an import response into :class:`ImportResult`.

    Handles both the success shape (a ``<RESPONSE>`` with counters) and the
    failure shape (``<ENVELOPE>`` with ``<STATUS>0</STATUS>`` and one or more
    ``<LINEERROR>``). All ``<LINEERROR>`` messages are collected. A bare text
    error such as ``<DATA>DESC not found</DATA>`` is treated as a line error.
    """
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise TallyResponseError(
            f"Could not parse TallyPrime response as XML: {exc}", body=raw
        ) from exc

    line_errors = [
        node.text.strip() for node in root.iter("LINEERROR") if node.text and node.text.strip()
    ]
    # A <DATA> element holding only text (no child elements) is an error string.
    for data in root.iter("DATA"):
        if len(data) == 0 and data.text and data.text.strip():
            line_errors.append(data.text.strip())

    result = ImportResult(
        created=_int(root, "CREATED"),
        altered=_int(root, "ALTERED"),
        deleted=_int(root, "DELETED"),
        cancelled=_int(root, "CANCELLED"),
        ignored=_int(root, "IGNORED"),
        errors=_int(root, "ERRORS"),
        combined=_int(root, "COMBINED"),
        last_vch_id=_int(root, "LASTVCHID"),
        last_m_id=_int(root, "LASTMID"),
        line_errors=line_errors,
        raw=raw,
    )

    status_node = root.find(".//STATUS")
    status_failed = status_node is not None and (status_node.text or "").strip() == "0"
    if result.errors > 0 or line_errors or status_failed:
        detail = "; ".join(line_errors) if line_errors else "import rejected by TallyPrime"
        raise TallyImportError(detail, line_errors=line_errors, result=result, body=raw)
    return result


__all__ = ["decode", "encode"]
