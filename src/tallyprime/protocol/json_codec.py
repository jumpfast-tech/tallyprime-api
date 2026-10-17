# SPDX-License-Identifier: MIT
"""JSON encoder/decoder for the TallyPrime gateway — not yet implemented.

TallyPrime gained a *native* JSON interface in **TallyPrime 7.0** (per the
official "Integrate with TallyPrime Using JSON" documentation). On 7.0+ the
gateway accepts JSON whose structure mirrors Tally's object schema, using HTTP
header metadata in place of the XML ``<HEADER>`` tags::

    content-type: application/json
    version: 1
    tallyrequest: Import
    type: Data
    id: All Masters

and replies with ``{"status": "1/0", "cmp_info": {}, "tallymessage": [...]}``.

Two things block a correct implementation today:

1. The native-JSON **body field mapping** (how ``LEDGER`` / ``AMOUNT`` / ``.LIST``
   blocks map onto JSON keys) is not fully published and needs confirming
   against a live 7.0+ instance.
2. Pre-7.0 instances — still the majority in the field — are XML-only.

Until that schema is verified, selecting ``format="json"`` raises a clear error
pointing users at ``format="xml"``. See ``docs/api-wire-formats.md`` (§7).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NoReturn

from tallyprime.exceptions import TallyFormatError
from tallyprime.protocol.operations import OperationSpec

_MESSAGE = (
    "The JSON wire format is not implemented yet. Native JSON requires "
    "TallyPrime 7.0+ and its body schema has not been verified against a live "
    "instance. Use TallyClient(format='xml') for now."
)


def encode(spec: OperationSpec, payload: Mapping[str, Any] | None) -> NoReturn:
    """Raise :class:`~tallyprime.exceptions.TallyFormatError` — JSON is unsupported."""
    raise TallyFormatError(_MESSAGE)


def decode(spec: OperationSpec, raw: str) -> NoReturn:
    """Raise :class:`~tallyprime.exceptions.TallyFormatError` — JSON is unsupported."""
    raise TallyFormatError(_MESSAGE)


__all__ = ["decode", "encode"]
