# Product CSV Validator — Catalog Preflight

Read-only checks for product CSV files before a human or automation workflow attempts an import. All included data is synthetic. Developed with AI assistance.

## What it checks

- Exact duplicate identifiers, including the CSV record containing the first occurrence.
- Missing configured columns and empty required fields.
- Nonnegative price syntax using your explicitly chosen decimal separator.
- Surrounding whitespace, without changing source values.

The JSON report includes source SHA-256, counts and up to 500 issue details. Total counts remain complete when details are truncated. Report records count the header as 1; multiline CSV fields do not change this numbering. Identifiers retain leading zeros and are compared as exact, case-sensitive strings. `01` and ` 01 ` are different identifiers; the latter receives a whitespace warning.

## Input and output

See `examples/INPUT.json`. Limits: 5 MB of UTF-8 text, 10000 data records and 30 columns. CSV uses comma, semicolon or tab. Blank records, ragged records, duplicate/empty headers, NUL characters and oversized fields are rejected. Required fields and price columns are explicit; price fields become required if selected. Currency symbols, grouping separators, exponent notation and negative prices are not supported by this price rule.

Local use, with Python 3.8+ and no dependencies:

```sh
python3 catalog_preflight.py examples/INPUT.json
python3 -m unittest -v
```

One successful Actor run outputs one report to the default Apify dataset. Invalid input fails the run. On Apify, input and report data are stored by the platform; this is not an offline processing promise. The processing code does not fetch URLs, call an LLM, upload to other services or log source cell values. Local CLI operation reads input and prints JSON without network requests.

## Scope

Passing these checks does not certify compatibility with Shoptet, Allegro, Shopify or any other store. No tax validation, barcode registration lookup, automatic correction, upload to a shop or proof of factual product accuracy is included. Store-specific mapping and import tests must be completed before claiming such compatibility.

## Quick start

1. Paste product CSV into **CSV content**.
2. Select the field delimiter and enter the exact SKU, required-field and price-column names.
3. Select the decimal separator. For example, use semicolon-delimited CSV and comma decimals for `12,50`.
4. Run the Actor and open the default dataset. Download JSON to preserve the nested issue list.

### Example input

```json
{
  "csvText": "sku;name;price\n00123;Żółta lampa;12,50\n00123;Žlutá lampa;12.50\n00124;;19,90\n 00125 ;Modrá lampa;29,00\n",
  "delimiter": ";",
  "skuColumn": "sku",
  "requiredColumns": ["sku", "name"],
  "priceColumns": ["price"],
  "decimalSeparator": ","
}
```

This synthetic example produces one report with four data records, three errors and one warning. A completed audit can contain errors: inspect `passedConfiguredChecks` and `summary` rather than relying on the run's success status.

## Polish and Czech product catalogs

**Polski:** Kontrola pliku CSV przed importem: powtarzające się SKU, puste wymagane pola i format cen. Separator dziesiętny wybiera użytkownik. Narzędzie nie zmienia danych.

**Čeština:** Kontrola souboru CSV před importem: duplicitní SKU, chybějící povinná pole a formát cen. Desetinný oddělovač volí uživatel. Nástroj data nemění.

Unicode names and leading-zero SKUs are preserved. This is a general CSV check; platform-specific import rules are outside its scope.

## Support

Use this Actor's Issues tab for questions or reproducible problems. Share a small synthetic sample and the chosen settings; remove confidential data before posting publicly. Development uses AI assistance, with deterministic checks and automated tests.
