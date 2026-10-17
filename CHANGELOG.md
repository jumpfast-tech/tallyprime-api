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

### Notes
- XML is the default wire format and works on all TallyPrime releases.
- `format="json"` is reserved for TallyPrime 7.0+ native JSON and currently
  raises `TallyFormatError` until the schema is verified against a live instance.
