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

# `company` targets a specific loaded company (SVCURRENTCOMPANY) on every request
with TallyClient(host="localhost", port=9000, company="ABC Ltd") as client:
    # Create a master with a typed model — returns an ImportResult with Tally's counters
    result = client.ledgers.create(Ledger(name="Cash", parent="Cash-in-Hand"))
    assert result.ok and result.created == 1

    # Create a voucher (amount sign convention: negative = debit, positive = credit)
    client.vouchers.sales.create(
        Voucher(
            date="20250401",
            entries=[
                LedgerEntry("ABC Ltd", "-100.00", is_deemed_positive=True, is_party_ledger=True),
                LedgerEntry("Sales", "100.00"),
            ],
        )
    )

    # Pull data — exports return an ExportResult you can traverse
    ledgers = client.ledgers.pull_all()
    for row in ledgers.find_all("LEDGER"):
        print(row["@NAME"], row.get("PARENT"))

    tb = client.reports.trial_balance.pull("20250401", "20250430")
    tb.raw  # the original XML, always available
    tb.to_dict()  # the whole response as nested dicts/lists

    # List the companies loaded in the running instance
    companies = client.companies.list().texts("COMPANYNAME")
```

Writes return an `ImportResult`; pulls return an `ExportResult` you traverse
with `find_all`/`first`/`texts`/`to_dict`. Every `create`/`alter` also accepts a
plain dict of raw Tally tags instead of a model. See the
[API reference](#api-reference) below for the full surface.

By default the client talks to `http://localhost:9000`, which is where
TallyPrime exposes its gateway when "Enable ODBC/HTTP" is turned on.

## API reference

All operations hang off `TallyClient` resource namespaces. `create`/`alter`
accept a typed model or a raw-tag dict; `pull*` operations return an
[`ExportResult`](#reading-data), the rest return an
[`ImportResult`](#writing-data).

### Accounting masters

| Call | Description |
|---|---|
| `client.ledgers.create(data)` | Create a ledger |
| `client.ledgers.alter(name, data)` | Alter the ledger named `name` |
| `client.ledgers.delete(name)` | Delete the ledger named `name` |
| `client.ledgers.pull(name)` | Pull a single ledger |
| `client.ledgers.pull_all()` | Pull all ledgers |
| `client.ledgers.pull_by_group(group)` | Pull ledgers under `group` |
| `client.groups.create(data)` | Create an accounting group |
| `client.groups.alter(name, data)` | Alter the group named `name` |
| `client.groups.delete(name)` | Delete the group named `name` |
| `client.groups.pull(name)` | Pull a single group |
| `client.groups.pull_all()` | Pull all groups |
| `client.groups.pull_by_group(parent)` | Pull groups nested under `parent` |

### Inventory masters

| Call | Description |
|---|---|
| `client.stock_items.create(data)` | Create a stock item |
| `client.stock_items.alter(name, data)` | Alter the stock item named `name` |
| `client.stock_items.delete(name)` | Delete the stock item named `name` |
| `client.stock_items.pull(name)` | Pull a single stock item |
| `client.stock_items.pull_all()` | Pull all stock items |
| `client.stock_items.pull_by_group(group)` | Pull stock items under a stock group |
| `client.stock_groups.create(data)` | Create a stock group |
| `client.stock_groups.alter(name, data)` | Alter the stock group named `name` |
| `client.stock_groups.delete(name)` | Delete the stock group named `name` |
| `client.stock_groups.pull(name)` | Pull a single stock group |
| `client.stock_groups.pull_all()` | Pull all stock groups |
| `client.stock_groups.pull_zero_balance()` | Pull stock groups with a zero balance |
| `client.units.create_simple(data)` | Create a simple (base) unit |
| `client.units.create_compound(data)` | Create a compound unit |
| `client.units.alter(name, data)` | Alter the unit named `name` |
| `client.units.delete(name)` | Delete the unit named `name` |
| `client.units.pull(name)` | Pull a single unit |
| `client.units.pull_all()` | Pull all units |

### Vouchers

Available on each voucher type: `client.vouchers.payment`,
`client.vouchers.receipt`, `client.vouchers.sales`, `client.vouchers.purchase`.

| Call | Description |
|---|---|
| `client.vouchers.<type>.create(data)` | Create a voucher of that type |
| `client.vouchers.<type>.alter(voucher_id, data)` | Alter a voucher by id |
| `client.vouchers.<type>.delete(voucher_id)` | Delete a voucher by id |
| `client.vouchers.<type>.pull(from_date, to_date)` | Pull vouchers in a date range |

> Voucher `alter`/`delete` identify the target via a `REMOTEID` attribute; this
> path is inferred and unverified against a live instance (see
> [`docs/api-wire-formats.md`](docs/api-wire-formats.md)).

### Reports

| Call | Description |
|---|---|
| `client.reports.trial_balance.pull(from_date, to_date, *, format="detailed", group=None)` | Trial Balance (`format`: `"detailed"` / `"plain"` / `"ledger_wise"`) |
| `client.reports.sales_register.pull(from_date, to_date)` | Sales Register |

### Companies

| Call | Description |
|---|---|
| `client.companies.list()` | List companies loaded in the running instance |
| `client.companies.pull_all()` | Alias of `list()` |

Dates use Tally's `YYYYMMDD` or `DD-Mon-YYYY` forms. Target a specific company
with `TallyClient(company="ABC Ltd")` or `client.company = "ABC Ltd"`.

### Payload models

Importable from `tallyprime`; pass to `create`/`alter` (or use raw dicts):

- **Masters:** `Ledger`, `Group`, `StockItem`, `StockGroup`, `Unit`
- **Vouchers:** `Voucher`, `LedgerEntry`, `InventoryEntry`, `BatchAllocation`,
  `BillAllocation`, `CostCategoryAllocation`, `CostCentreAllocation`

Every model has an `extra={...}` escape hatch for raw Tally tags not modelled
explicitly.

### Writing data

`create` / `alter` / `delete` return an `ImportResult` with Tally's counters
(`created`, `altered`, `deleted`, `errors`, …) and an `.ok` flag. A rejected
import raises `TallyImportError` carrying every `<LINEERROR>` message.

### Reading data

`pull*` operations and reports return an `ExportResult`:

- `result.find_all(tag)` — every matching element (any depth) as a dict
- `result.first(tag)` — the first match or `None`
- `result.texts(tag)` — the text of every match
- `result.to_dict()` — the whole response as nested dicts/lists
- `result.raw` — the original XML

Use `parse_amount("1,29,377.00")` to turn Tally's Indian-grouped, `Dr`/`Cr`
amount strings into signed floats.

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

### Concurrency

The client is **synchronous by design** — there is no async client. Every call
is a single blocking HTTP round-trip, so if you need to run many in parallel,
put a thread pool over the client (the connection pool is thread-safe):

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(client.ledgers.create, ledgers))
```

If your application is itself async (FastAPI, aiohttp, …), call the client from
a worker thread so you don't block the event loop — e.g.
`await anyio.to_thread.run_sync(client.ledgers.create, ledger)` or
`loop.run_in_executor(...)`. Keeping the library sync means there's one code
path to reason about, and consumers bridge to async on their own terms.

## License

[MIT](LICENSE)

## Contact

Created by JumpFast Technologies. Email: [info@jumpfast.tech](mailto:info@jumpfast.tech)
