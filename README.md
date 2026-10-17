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
from tallyprime import TallyClient, Ledger, Voucher, LedgerEntry

with TallyClient(host="localhost", port=9000) as client:
    # Create a master with a typed model — returns an ImportResult with Tally's counters
    result = client.ledgers.create(Ledger(name="Cash", parent="Cash-in-Hand"))
    assert result.ok and result.created == 1

    # Create a voucher (amount sign convention: negative = debit, positive = credit)
    client.vouchers.sales.create(Voucher(
        date="20250401",
        entries=[
            LedgerEntry("ABC Ltd", "-100.00", is_deemed_positive=True, is_party_ledger=True),
            LedgerEntry("Sales", "100.00"),
        ],
    ))

    # Pull data — exports return the raw report XML for you to parse
    cash = client.ledgers.pull("Cash")
    tb = client.reports.trial_balance.pull("20250401", "20250430")
```

Every `create`/`alter` also accepts a plain dict of raw Tally tags if you'd
rather not use the models — `client.ledgers.create({"NAME": "Cash", "PARENT":
"Cash-in-Hand"})`. Models carry an `extra={...}` escape hatch for any Tally
field not modelled explicitly.

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
