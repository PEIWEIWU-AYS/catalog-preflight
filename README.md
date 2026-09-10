# Catalog Preflight | 商品 CSV 体检工具

Read-only product CSV validation: detect duplicate SKUs, missing fields and invalid price syntax before an import. 商品 CSV 只读检查：发现重复货号、缺失字段和价格格式问题。All examples are synthetic; developed with AI assistance.

**Keywords / 关键词:** CSV validation, product catalog, duplicate SKU, decimal comma, Apify Actor; CSV 校验、商品目录、货号去重检查、价格格式。

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

## Deployment

The `.actor` directory contains the Apify configuration, customer documentation and Docker recipe. The Python SDK integration uses Python 3.12 and `apify==4.0.2`. Running the local CLI requires no Apify account. Hosted deployment and pricing are managed separately in Apify Console.

## Contributing

Report a reproducible bug with a synthetic CSV and settings. Do not post customer data or secrets. Run `python3 -m unittest -v` for code changes. Scope proposals should include a clear input rule and expected report.

## Roadmap

Potential additions include user-supplied column aliases and additional explicit validation rules. These are not implemented features.

## Keywords

product CSV validator, ecommerce catalog audit, SKU duplicate detection, semicolon CSV, decimal comma validation, Polish Czech product catalogs, 商品数据校验, 重复货号检查

## Suggested GitHub Topics

`csv` `data-validation` `ecommerce` `apify-actor` `python` `sku` `data-quality` `catalog` `automation`

## License

MIT. See LICENSE.
