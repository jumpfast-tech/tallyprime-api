# SPDX-License-Identifier: MIT
"""Typed result objects returned by the client."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union
from xml.etree import ElementTree as ET

from tallyprime.exceptions import TallyResponseError

#: A parsed XML node: a leaf's text, or a mapping of child/attribute names to
#: nested nodes. Attribute names are prefixed with ``@``; a repeated child tag
#: collapses to a list.
Node = Union[str, dict[str, Any], None]


@dataclass
class ImportResult:
    """Outcome of an import (create / alter / delete) request.

    TallyPrime answers a successful import with a ``<RESPONSE>`` element holding
    a set of counters; a logical failure comes back wrapped in
    ``<ENVELOPE>`` with ``<STATUS>0</STATUS>`` and one or more ``<LINEERROR>``
    messages. **Tally returns HTTP 200 in both cases**, so success is determined
    from these counters, not the status code.

    Attributes:
        created: Number of objects created.
        altered: Number of objects altered.
        deleted: Number of objects deleted.
        cancelled: Number of vouchers cancelled.
        ignored: Number of objects ignored (e.g. duplicates).
        errors: Number of errored lines. ``0`` means success.
        combined: Value of the ``<COMBINED>`` counter.
        last_vch_id: ``<LASTVCHID>`` — id of the last voucher touched.
        last_m_id: ``<LASTMID>`` — id of the last master touched.
        line_errors: All ``<LINEERROR>`` messages, in document order.
        raw: The raw response body, for debugging or re-parsing.
    """

    created: int = 0
    altered: int = 0
    deleted: int = 0
    cancelled: int = 0
    ignored: int = 0
    errors: int = 0
    combined: int = 0
    last_vch_id: int = 0
    last_m_id: int = 0
    line_errors: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def ok(self) -> bool:
        """True when the import reported no errors."""
        return self.errors == 0 and not self.line_errors


def _localname(tag: str) -> str:
    """Strip any ``{namespace}`` prefix from an element tag.

    TallyPrime responses can carry namespaced tags (e.g. ``{TallyUDF}FOO``);
    matching and keys use the local name so callers never deal with namespaces.
    """
    return tag.rsplit("}", 1)[-1]


def _element_to_node(element: ET.Element) -> Node:
    """Convert an element to a :data:`Node` (text leaf or nested mapping)."""
    result: dict[str, Any] = {}
    for name, value in element.attrib.items():
        result[f"@{_localname(name)}"] = value

    for child in element:
        key = _localname(child.tag)
        node = _element_to_node(child)
        if key in result:
            existing = result[key]
            if isinstance(existing, list):
                existing.append(node)
            else:
                result[key] = [existing, node]
        else:
            result[key] = node

    text = (element.text or "").strip()
    if not result:
        # A pure leaf: return its text (empty string if none).
        return text
    if text:
        result["#text"] = text
    return result


@dataclass
class ExportResult:
    """Parsed result of an export (``pull``) request.

    Export responses vary widely by report, so rather than force a rigid schema
    this wraps the parsed tree and offers traversal helpers that work regardless
    of nesting. The original XML is always available as :attr:`raw`.

    Example:
        >>> result = client.ledgers.pull_all()
        >>> [row["NAME"] for row in result.find_all("LEDGER")]
        ['Cash', 'Bank']
    """

    raw: str
    root: ET.Element

    @classmethod
    def from_raw(cls, raw: str) -> ExportResult:
        """Parse ``raw`` XML into an :class:`ExportResult`.

        Raises:
            TallyResponseError: If the body is not well-formed XML.
        """
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise TallyResponseError(
                f"Could not parse TallyPrime export as XML: {exc}", body=raw
            ) from exc
        return cls(raw=raw, root=root)

    def to_dict(self) -> Node:
        """Convert the whole response to a nested dict/text structure."""
        return _element_to_node(self.root)

    def find_all(self, tag: str) -> list[dict[str, Any]]:
        """Return every element named ``tag`` (any depth) as a mapping.

        Leaf-only matches (elements with no children or attributes) are skipped,
        since there is nothing structured to return for them; use :meth:`texts`
        for those.
        """
        out: list[dict[str, Any]] = []
        for element in self.root.iter():
            if _localname(element.tag) != tag:
                continue
            node = _element_to_node(element)
            if isinstance(node, dict):
                out.append(node)
        return out

    def first(self, tag: str) -> dict[str, Any] | None:
        """Return the first element named ``tag`` as a mapping, or ``None``."""
        matches = self.find_all(tag)
        return matches[0] if matches else None

    def texts(self, tag: str) -> list[str]:
        """Return the text of every element named ``tag`` (any depth)."""
        return [
            (element.text or "").strip()
            for element in self.root.iter()
            if _localname(element.tag) == tag
        ]


def parse_amount(value: str) -> float:
    """Parse a Tally amount string into a float.

    Tally formats numbers with Indian digit grouping by default
    (``"1,29,377.00"``) and may wrap debits in parentheses or append a ``Dr``/
    ``Cr`` suffix. This strips the grouping/suffixes and returns a signed float
    (``Dr``/parenthesised → negative).

    Raises:
        ValueError: If no numeric value can be extracted.
    """
    text = value.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    upper = text.upper()
    if upper.endswith("DR"):
        negative = True
        text = text[:-2]
    elif upper.endswith("CR"):
        text = text[:-2]
    cleaned = text.replace(",", "").strip()
    if not cleaned:
        raise ValueError(f"No numeric value in {value!r}")
    amount = float(cleaned)
    return -amount if negative else amount
