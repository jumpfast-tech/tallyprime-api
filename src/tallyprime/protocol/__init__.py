# SPDX-License-Identifier: MIT
"""Protocol layer: encode requests and decode responses per wire format.

Resources call :func:`encode_request` to turn an operation key + payload into a
request body, and :func:`decode_response` to parse the gateway's reply. Both
dispatch on the wire format (``"xml"`` or ``"json"``) and look the operation up
in the registry in :mod:`tallyprime.protocol.operations`.

The envelope dialect itself is documented on the encoder/decoder functions in
:mod:`tallyprime.protocol.xml_codec` and in ``docs/api-wire-formats.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tallyprime.protocol import json_codec, xml_codec
from tallyprime.protocol.operations import get_spec


def encode_request(operation: str, payload: Mapping[str, Any] | None, *, format: str) -> str:
    """Encode ``operation`` + ``payload`` into a request body for ``format``.

    Args:
        operation: A registered operation key, e.g. ``"ledger.create"``.
        payload: The operation's data/control mapping, or ``None``.
        format: ``"xml"`` (implemented) or ``"json"`` (raises until supported).

    Raises:
        TallyFormatError: If ``format`` is ``"json"`` (not yet implemented) or
            unrecognised.
    """
    spec = get_spec(operation)
    if format == "xml":
        return xml_codec.encode(spec, payload)
    return json_codec.encode(spec, payload)


def decode_response(operation: str, raw: str, *, format: str) -> Any:
    """Decode a raw response body for ``operation`` under ``format``.

    Imports return an :class:`~tallyprime.models.ImportResult`; exports return
    an :class:`~tallyprime.models.ExportResult`. See
    :func:`tallyprime.protocol.xml_codec.decode`.
    """
    spec = get_spec(operation)
    if format == "xml":
        return xml_codec.decode(spec, raw)
    return json_codec.decode(spec, raw)


__all__ = ["decode_response", "encode_request"]
