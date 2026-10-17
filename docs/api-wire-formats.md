# TallyPrime API — Wire-Format Reference

Reference for implementing the protocol layer (`resources/_base.py::Resource._request`).
Endpoint: `POST http://localhost:9000` (port configurable in Tally under
F1 → Settings → Connectivity). `Content-Type: text/xml` for XML,
`application/json` for native JSON.

> **Confidence:** Sections 1–3, 5, 6 and the dates/company notes come from
> official TallyHelp pages (see [Sources](#sources)) and are high-confidence.
> Tally's integration XML schema is historically identical between Tally.ERP 9
> and TallyPrime, so ERP 9 examples apply directly. Items flagged **UNVERIFIED**
> need validation against a live instance before shipping.

---

## 0. XML vs JSON — which to implement first

**XML is the safe primary.** It works on every TallyPrime (and ERP 9) release.

**Native JSON is real but new:** available only from **TallyPrime 7.0+** (a recent
2026 release) per the official "Integrate with TallyPrime Using JSON" page. Many
deployed instances are still 6.x and are **XML-only**. The JSON *body* field
mapping is not fully documented publicly yet.

> **Implication for this package:** we expose `format="json"` as the default per
> product decision, but the **XML encoder is what we implement and test first**.
> JSON encoding stays stubbed until the 7.0 native schema is confirmed on a live
> instance. Document this clearly so `format="json"` doesn't silently mislead on
> older gateways.

---

## 1. Base Envelope Structure

Every request is an `<ENVELOPE>` with `<HEADER>` and `<BODY>`. There are **two
body dialects** — import and export — and getting them right is the crux.

### HEADER fields

| Tag | Values | Notes |
|---|---|---|
| `VERSION` | `1` | On most export/voucher requests; often omitted on master imports. |
| `TALLYREQUEST` | `Import` / `Import Data` / `Export` | Case-insensitive in practice. |
| `TYPE` | `Data` / `Object` / `Collection` / `Function` | Selects what `ID` refers to. |
| `ID` | Report/collection/object name | e.g. `All Masters`, `Vouchers`, `Trial Balance`, `List of Ledgers`. For `TYPE=Object` add `<SUBTYPE>` + `<ID TYPE="Name">`. |

### Import skeleton (masters)
```xml
<ENVELOPE>
 <HEADER>
  <TALLYREQUEST>Import Data</TALLYREQUEST>
 </HEADER>
 <BODY>
  <IMPORTDATA>
   <REQUESTDESC>
    <REPORTNAME>All Masters</REPORTNAME>
   </REQUESTDESC>
   <REQUESTDATA>
    <TALLYMESSAGE xmlns:UDF="TallyUDF">
     <!-- one or more master objects here -->
    </TALLYMESSAGE>
   </REQUESTDATA>
  </IMPORTDATA>
 </BODY>
</ENVELOPE>
```

### Import skeleton (vouchers — terser form, also accepted)
```xml
<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>Import</TALLYREQUEST>
  <TYPE>Data</TYPE>
  <ID>Vouchers</ID>
 </HEADER>
 <BODY>
  <DESC></DESC>
  <DATA>
   <TALLYMESSAGE>
    <!-- VOUCHER here -->
   </TALLYMESSAGE>
  </DATA>
 </BODY>
</ENVELOPE>
```

### Export skeleton
```xml
<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>Export</TALLYREQUEST>
  <TYPE>Data</TYPE>
  <ID>Trial Balance</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>
```

> **UNVERIFIED:** an `<EXPORTDATA><REQUESTDESC><REPORTNAME>` export form appears
> in one blog but not in first-party docs. Use the `<DESC><STATICVARIABLES>` form.

---

## 2. Master & Voucher Payloads

All master objects go inside `<TALLYMESSAGE>` of the master-import skeleton.

### Group
```xml
<GROUP Action="Create">
 <NAME>North Zone Debtors</NAME>
 <PARENT>Sundry Debtors</PARENT>
</GROUP>
```

### Ledger (minimal → full)
```xml
<LEDGER Action="Create">
 <NAME>Customer ABC</NAME>
 <PARENT>Sundry Debtors</PARENT>
</LEDGER>
```
```xml
<LEDGER Action="Create">
 <NAME>Customer ABC</NAME>
 <PARENT>Sundry Debtors</PARENT>
 <MAILINGNAME.LIST TYPE="String"><MAILINGNAME>Customer – Mailing name</MAILINGNAME></MAILINGNAME.LIST>
 <ADDRESS.LIST TYPE="String">
  <ADDRESS>Door No</ADDRESS><ADDRESS>Lane</ADDRESS><ADDRESS>Locality</ADDRESS>
 </ADDRESS.LIST>
 <PINCODE>560068</PINCODE>
 <COUNTRYNAME>India</COUNTRYNAME>
 <LEDSTATENAME>Karnataka</LEDSTATENAME>
 <EMAIL>A@abc.com</EMAIL>
 <LEDGERPHONE>0888888</LEDGERPHONE>
 <LEDGERMOBILE>99999999</LEDGERMOBILE>
</LEDGER>
```

### Stock Group / Stock Item
```xml
<STOCKGROUP Action="Create"><NAME>Electronics</NAME></STOCKGROUP>
```
```xml
<STOCKITEM Action="Create">
 <NAME>Red Colored Striped Shirt</NAME>
 <BASEUNITS>lts</BASEUNITS>
 <NAME.LIST TYPE="String"><NAME>Red Colored Striped Shirt</NAME></NAME.LIST>
</STOCKITEM>
```

### Unit — simple / compound
```xml
<UNIT Action="Create">
 <NAME>Pcs</NAME><ISSIMPLEUNIT>Yes</ISSIMPLEUNIT>
 <ORIGINALNAME>Pieces</ORIGINALNAME><DECIMALPLACES>2</DECIMALPLACES>
</UNIT>
```
```xml
<UNIT Action="Create">
 <NAME>Dozen of 12 Pieces</NAME><ISSIMPLEUNIT>No</ISSIMPLEUNIT>
 <DECIMALPLACES>2</DECIMALPLACES>
 <BASEUNITS>Doz</BASEUNITS><ADDITIONALUNITS>Pcs</ADDITIONALUNITS><CONVERSION>12</CONVERSION>
</UNIT>
```
Compound units: load-bearing fields are `ISSIMPLEUNIT=No`, `BASEUNITS`,
`ADDITIONALUNITS`, `CONVERSION`. Both referenced units must already exist.

### Sales Voucher (accounting mode) — goes in the voucher skeleton
```xml
<VOUCHER>
 <DATE>20160401</DATE>
 <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
 <VOUCHERNUMBER>1</VOUCHERNUMBER>
 <PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>
 <ISINVOICE>No</ISINVOICE>
 <LEDGERENTRIES.LIST>
  <LEDGERNAME>ABC Company Limited</LEDGERNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
  <AMOUNT>-215476.00</AMOUNT>
 </LEDGERENTRIES.LIST>
 <LEDGERENTRIES.LIST>
  <LEDGERNAME>Sales</LEDGERNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <AMOUNT>215476.00</AMOUNT>
 </LEDGERENTRIES.LIST>
</VOUCHER>
```

**Sign convention (critical):** `AMOUNT` **negative = debit**, **positive =
credit**; `ISDEEMEDPOSITIVE=Yes` marks the debit side. Dr total must equal Cr
total or Tally rejects with "Voucher totals do not match".

- Use `LEDGERENTRIES.LIST` for accounting/sales vouchers (official samples).
  `ALLLEDGERENTRIES.LIST` is the export-side name and is also accepted on import —
  **support both; prefer `LEDGERENTRIES.LIST`.**
- Inventory invoices add `ALLINVENTORYENTRIES.LIST` with nested
  `BATCHALLOCATIONS.LIST` and `ACCOUNTINGALLOCATIONS.LIST`.

### Payment Voucher — **UNVERIFIED** (structure inferred, no first-party sample)
```xml
<!-- verify field set (ISPAYMENT, bank allocation sub-lists) on live Tally -->
<VOUCHER>
 <DATE>20160401</DATE>
 <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
 <LEDGERENTRIES.LIST>
  <LEDGERNAME>Rent</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-5000.00</AMOUNT>
 </LEDGERENTRIES.LIST>
 <LEDGERENTRIES.LIST>
  <LEDGERNAME>HDFC Bank</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>5000.00</AMOUNT>
 </LEDGERENTRIES.LIST>
</VOUCHER>
```

---

## 3. ACTION Attribute & Object Identification

`Action` (a.k.a. `ACTION`, case-insensitive) sits on the **object element**
(`<LEDGER>`, `<VOUCHER>` …), not on `TALLYMESSAGE`. Values: `Create`, `Alter`,
`Delete`, `Cancel` (vouchers only).

**Masters — identified by name.** For alter/delete, old name in the `NAME`
attribute, new values as children:
```xml
<LEDGER NAME="Customer ABC" Action="Alter">
 <ADDRESS.LIST TYPE="String"><ADDRESS>123 Business Lane</ADDRESS></ADDRESS.LIST>
</LEDGER>
```
Rename = `NAME=` attribute (old) + `<NAME>` child (new) together.

**Vouchers — identified by date + tag lookup:**
```xml
<VOUCHER DATE="01-Apr-2016" TAGNAME="Voucher Number" TAGVALUE="1"
         Action="Alter" VCHTYPE="Sales">
 <NARRATION>Being Goods sold</NARRATION>
</VOUCHER>
<VOUCHER DATE="01-Apr-2016" TAGNAME="VoucherNumber" TAGVALUE="2"
         Action="Cancel" VCHTYPE="Sales"/>
```

**Idempotency:** pass a stable `REMOTEID` attribute and/or `<GUID>` child to make
re-sends update instead of duplicate. (Real mechanism; confirm exact GUID string
format from a live export — **UNVERIFIED** format.)

---

## 4. Export Requests (Reports & Collections)

### Trial Balance
```xml
<ENVELOPE>
 <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
  <TYPE>Data</TYPE><ID>Trial Balance</ID></HEADER>
 <BODY><DESC><STATICVARIABLES>
   <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
 </STATICVARIABLES></DESC></BODY>
</ENVELOPE>
```

### Date-ranged register (Day Book pattern; basis for Sales Register)
```xml
<ENVELOPE>
 <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
  <TYPE>Data</TYPE><ID>DayBook</ID></HEADER>
 <BODY><DESC><STATICVARIABLES>
   <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   <SVFROMDATE TYPE="Date">1-Apr-2016</SVFROMDATE>
   <SVTODATE   TYPE="Date">1-Apr-2016</SVTODATE>
 </STATICVARIABLES></DESC></BODY>
</ENVELOPE>
```
**Sales Register — UNVERIFIED:** bare `<ID>Sales Register</ID>` with
`SVFROMDATE`/`SVTODATE` is probable; the verified route is Day Book + a
`<TDL><TDLMESSAGE>` voucher-type filter (`$VoucherTypeName=Sales`).

### All Ledgers — Collection export
```xml
<ENVELOPE>
 <HEADER><VERSION>1</VERSION><TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE><ID>List of Ledgers</ID></HEADER>
 <BODY><DESC>
  <STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
  <TDL><TDLMESSAGE>
   <COLLECTION NAME="List of Ledgers" ISMODIFY="Yes">
    <NATIVEMETHOD>Name</NATIVEMETHOD>
    <NATIVEMETHOD>Parent</NATIVEMETHOD>
   </COLLECTION>
  </TDLMESSAGE></TDL>
 </DESC></BODY>
</ENVELOPE>
```

### Single Ledger — Object export with FETCH
```xml
<ENVELOPE>
 <HEADER><VERSION>1</VERSION><TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>OBJECT</TYPE><SUBTYPE>Ledger</SUBTYPE>
  <ID TYPE="Name">NameOfTheLedger</ID></HEADER>
 <BODY><DESC>
  <STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
  <FETCHLIST><FETCH>Name</FETCH><FETCH>Parent</FETCH></FETCHLIST>
 </DESC></BODY>
</ENVELOPE>
```

---

## 5. Response Format

### Success (import)
```xml
<RESPONSE>
 <CREATED>1</CREATED><ALTERED>0</ALTERED><DELETED>0</DELETED>
 <LASTVCHID>0</LASTVCHID><LASTMID>0</LASTMID><COMBINED>0</COMBINED>
 <IGNORED>0</IGNORED><ERRORS>0</ERRORS><CANCELLED>0</CANCELLED>
</RESPONSE>
```
Success = `ERRORS=0` with the relevant counter incremented. **Tally returns HTTP
200 even on logical failure — parse the counters, not just the status code.**

### Error (import) — wrapped in ENVELOPE with `STATUS=0`
```xml
<ENVELOPE>
 <HEADER><VERSION>1</VERSION><STATUS>0</STATUS></HEADER>
 <BODY><DATA>
   <LINEERROR>Voucher totals do not match! Dr: 20,394.00 Cr: 20,395.00 Diff: 1.00 Cr</LINEERROR>
   <CREATED>0</CREATED><ALTERED>0</ALTERED><DELETED>0</DELETED>
   <ERRORS>1</ERRORS><CANCELLED>0</CANCELLED><VCHNUMBER>1</VCHNUMBER>
 </DATA></BODY>
</ENVELOPE>
```
Request-level failure: `<BODY><DATA>DESC not found</DATA></BODY>`.

**Client parsing rules:**
- `STATUS` in HEADER: `1` ok, `0` failure.
- There can be **multiple `<LINEERROR>`** (one per rejected line) — collect all.
  Common: `Ledger 'X' does not exist!`, `Voucher totals do not match!`.
- Export responses are raw report XML (e.g. `<ACCTSINFO><ACCOUNTNAME>…</ACCOUNTNAME>
  <ACCOUNTVALUE>1,29,377.00</ACCOUNTVALUE></ACCTSINFO>`). Numbers use Indian digit
  grouping — **strip commas before parsing**.

---

## 6. Dates, Company, Static Variables

- **Date formats (both accepted):** `YYYYMMDD` (e.g. `20160401`) inside `<DATE>`;
  `DD-Mon-YYYY` (e.g. `1-Apr-2016`) where `TYPE="Date"` is present. Default to
  `YYYYMMDD` in element content.
- **Company:** `<SVCURRENTCOMPANY>ABC Company Ltd</SVCURRENTCOMPANY>` inside
  `<STATICVARIABLES>`. If omitted, Tally uses the open company. Set it explicitly
  on multi-company instances.
- **Core static variables:** `SVEXPORTFORMAT` (`$$SysName:XML` / `:HTML` / ASCII /
  SDF), `SVFROMDATE`, `SVTODATE`, `SVCURRENTCOMPANY`, `EXPLODEFLAG` (Yes/No),
  `IMPORTDUPS` (duplicate handling — exact values UNVERIFIED).

---

## 7. Native JSON (TallyPrime 7.0+)

Per the official JSON integration page, 7.0 ships native JSON as a default
feature — no TDL needed for native-schema data. HTTP metadata replaces XML header
tags:
```
content-type: application/json
version: 1
tallyrequest: Import
type: Data
id: All Masters
```
Response shape: `{ "status": "1/0", "cmp_info": {}, "tallymessage": [] }`.

**UNVERIFIED and blocking for a JSON encoder:**
- The native-JSON **body field mapping** (how `LEDGER`/`AMOUNT`/`.LIST` map to
  keys) is not fully public — pull it from the TallyHelp JSON page / a live 7.0
  instance before implementing.
- Whether port 9000 serves JSON directly is not stated on the JSON page.
- Pre-7.0 instances are XML-only.

---

## Open items to verify on a live instance

1. Payment voucher exact field set.
2. `ALLLEDGERENTRIES.LIST` vs `LEDGERENTRIES.LIST` (support both).
3. `Sales Register` bare report name vs Day Book + TDL filter.
4. `<EXPORTDATA>` body form (use `<DESC>` form meanwhile).
5. Native JSON body schema + port-9000 behavior.
6. `GUID`/`REMOTEID` exact string format.

## Sources

- Official Sample XML: https://help.tallysolutions.com/sample-xml/
- Case Study I – XML Request/Response Formats: https://help.tallysolutions.com/article/DeveloperReference/integration-capabilities/case_study_1.htm
- Understanding Tally XML Tags: https://help.tallysolutions.com/understanding-tally-xml-tags/
- Native JSON integration (7.0+): https://help.tallysolutions.com/tally-prime-integration-using-json-1/
- Integration Methods and Technologies: https://help.tallysolutions.com/integration-methods-and-technologies/
- Community API docs: https://github.com/NoumaanAhamed/tally-prime-api-docs
- LINEERROR handling in real integrations: https://github.com/lamemustafa/bridge/pull/695 , https://github.com/Forgesaroj/tally-xml-kit/issues/4
