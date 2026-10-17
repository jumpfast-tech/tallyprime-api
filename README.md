# tallyprime

[![CI](https://github.com/jumpfast-tech/tallyprime-api/actions/workflows/ci.yml/badge.svg)](https://github.com/jumpfast-tech/tallyprime-api/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tallyprime.svg)](https://pypi.org/project/tallyprime/)
[![Python versions](https://img.shields.io/pypi/pyversions/tallyprime.svg)](https://pypi.org/project/tallyprime/)

A Python client for the [TallyPrime](https://tallysolutions.com/) HTTP/XML
gateway.

## Installation

```bash
pip install tallyprime
```

## Usage

```python
from tallyprime import TallyClient

with TallyClient(host="localhost", port=9000) as client:
    # Create a master — returns an ImportResult with Tally's counters
    result = client.ledgers.create({"NAME": "Cash", "PARENT": "Cash-in-Hand"})
    assert result.ok and result.created == 1

    # Create a voucher (amount sign convention: negative = debit, positive = credit)
    client.vouchers.sales.create({
        "DATE": "20250401",
        "LEDGERENTRIES.LIST": [
            {"LEDGERNAME": "ABC Ltd", "ISDEEMEDPOSITIVE": True, "AMOUNT": "-100.00"},
            {"LEDGERNAME": "Sales", "ISDEEMEDPOSITIVE": False, "AMOUNT": "100.00"},
        ],
    })

    # Pull data — exports return the raw report XML for you to parse
    cash = client.ledgers.pull("Cash")
    tb = client.reports.trial_balance.pull("20250401", "20250430")
```

By default the client talks to `http://localhost:9000`, which is where
TallyPrime exposes its gateway when "Enable ODBC/HTTP" is turned on.

### Wire format: XML (default) vs JSON

The client speaks TallyPrime's **XML** dialect by default — it works on every
TallyPrime release. The payloads you pass are plain dicts of Tally field tags;
see the conventions (nested `.LIST` blocks, booleans → `Yes`/`No`, `@`-prefixed
keys → attributes) documented on `tallyprime.protocol.xml_codec`.

`TallyClient(format="json")` is reserved for TallyPrime 7.0+ native JSON but is
**not implemented yet** — selecting it raises `TallyFormatError`. See
[`docs/api-wire-formats.md`](docs/api-wire-formats.md) for the full protocol
reference and the list of fields still needing verification against a live
instance.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest          # run tests
ruff check .    # lint
ruff format .   # format
mypy            # type-check
```

## License

[MIT](LICENSE)
