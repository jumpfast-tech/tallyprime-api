# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial package scaffolding.
- `TallyClient` with resource namespaces: `ledgers`, `groups`, `stock_items`,
  `stock_groups`, `units`, `vouchers` (payment/receipt/sales/purchase), and
  `reports` (trial balance, sales register).
- XML protocol layer: encoder for master/voucher imports and report/collection/
  object exports, plus a response parser returning `ImportResult`.
- `ImportResult` result model and exceptions `TallyError`,
  `TallyConnectionError`, `TallyResponseError`, `TallyImportError`,
  `TallyFormatError`.
- `docs/api-wire-formats.md` reference for the TallyPrime XML/JSON dialect.
- Typed payload models (`Ledger`, `Group`, `StockItem`, `StockGroup`, `Unit`,
  `Voucher`, `LedgerEntry`, `InventoryEntry`, `BatchAllocation`) that resources
  accept in place of raw dicts, each with an `extra={}` escape hatch for
  unmodelled Tally fields. `Voucher.inventory_entries` supports inventory
  invoices with nested batch and accounting allocations.
- Export (`pull`) responses now return an `ExportResult` with traversal helpers
  (`find_all`, `first`, `texts`, `to_dict`) that are namespace-aware, plus the
  original XML on `.raw`. Added `parse_amount()` for Tally's Indian-grouped,
  `Dr`/`Cr`-suffixed number strings.
- Ledger entries support bill-wise and cost-centre breakdowns via
  `BillAllocation`, `CostCategoryAllocation` and `CostCentreAllocation`.
- Company support: `TallyClient(company=...)` (mutable) sets `SVCURRENTCOMPANY`
  on every request, and `client.companies.list()` enumerates loaded companies.

### Notes
- XML is the default wire format and works on all TallyPrime releases.
- `format="json"` is reserved for TallyPrime 7.0+ native JSON and currently
  raises `TallyFormatError` until the schema is verified against a live instance.
