"""Read-only, deterministic checks for customer-supplied product CSV files."""

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re

MAX_BYTES = 5_000_000
MAX_ROWS = 10_000
MAX_COLUMNS = 30
MAX_ISSUES = 500


class InputError(ValueError):
    pass


def audit_catalog(payload):
    if not isinstance(payload, dict):
        raise InputError('Input must be a JSON object.')
    allowed = {'csvText', 'delimiter', 'skuColumn', 'requiredColumns',
               'priceColumns', 'decimalSeparator'}
    if set(payload) - allowed:
        raise InputError('Unknown input setting; check the input schema.')
    text = payload.get('csvText')
    if not isinstance(text, str) or not text.strip():
        raise InputError('csvText must contain a header and data.')
    if len(text) > MAX_BYTES or len(text.encode('utf-8')) > MAX_BYTES:
        raise InputError('CSV exceeds the 5 MB UTF-8 input limit.')
    if '\x00' in text:
        raise InputError('NUL characters are not supported.')
    delimiter = payload.get('delimiter', ',')
    if delimiter not in (',', ';', '\t'):
        raise InputError('delimiter must be comma, semicolon, or tab.')
    decimal = payload.get('decimalSeparator', '.')
    if decimal not in ('.', ','):
        raise InputError('decimalSeparator must be a dot or comma.')
    sku = payload.get('skuColumn', 'sku')
    if not isinstance(sku, str) or not sku.strip():
        raise InputError('skuColumn must be a nonempty column name.')
    required = payload.get('requiredColumns', ['sku', 'name'])
    prices = payload.get('priceColumns', [])
    for key, value in [('requiredColumns', required), ('priceColumns', prices)]:
        if (not isinstance(value, list) or len(value) > MAX_COLUMNS
                or any(not isinstance(x, str) or not x.strip() for x in value)
                or len(value) != len(set(value))):
            raise InputError(key + ' must be a list of distinct nonempty column names.')

    reader = csv.reader(io.StringIO(text.lstrip('\ufeff'), newline=''),
                        delimiter=delimiter, strict=True)
    try:
        header = next(reader)
        if not header or len(header) > MAX_COLUMNS:
            raise InputError('The CSV must have 1 to 30 columns.')
        normalized = [name.strip() for name in header]
        if any(not name for name in normalized) or len(set(normalized)) != len(header):
            raise InputError('Blank or duplicate column names are not supported.')
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise InputError('CSV exceeds the 10000 data-record limit.')
            if len(row) != len(header):
                raise InputError('Every record must have the same number of fields as the header.')
            rows.append(row)
    except (csv.Error, StopIteration) as error:
        raise InputError('The CSV is empty, malformed, or contains an oversized field.') from error
    if not rows:
        raise InputError('At least one data record is required.')

    issues = []
    counts = Counter()
    severities = Counter()
    affected = set()

    def issue(record, column, code, message, severity='error'):
        counts[code] += 1
        severities[severity] += 1
        if record > 1:
            affected.add(record)
        if len(issues) < MAX_ISSUES:
            issues.append({'record': record, 'column': column, 'code': code,
                           'severity': severity, 'message': message})

    expected = list(dict.fromkeys([sku] + required + prices))
    for column in expected:
        if column not in header:
            issue(1, column, 'missing_column', 'Configured column is absent; no name guessing was applied.')
    for original, stripped in zip(header, normalized):
        if original != stripped:
            issue(1, original, 'header_whitespace', 'Header contains surrounding whitespace.', 'warning')

    price_pattern = re.compile(r'[0-9]+(?:' + re.escape(decimal) + r'[0-9]+)?\Z')
    seen = {}
    for record, row in enumerate(rows, 2):
        item = dict(zip(header, row))
        for column, value in item.items():
            if value != value.strip():
                issue(record, column, 'surrounding_whitespace', 'Value has surrounding whitespace; unchanged.', 'warning')
        for column in dict.fromkeys([sku] + required + prices):
            if column in item and not item[column].strip():
                issue(record, column, 'missing_value', 'Configured field is blank.')
        if sku in item and item[sku].strip():
            # Exact original text comparison: identifiers are never normalized or merged.
            value = item[sku]
            if value in seen:
                issue(record, sku, 'duplicate_sku', 'Exact identifier first appears in record %d.' % seen[value])
            else:
                seen[value] = record
        for column in prices:
            if column in item and item[column].strip() and not price_pattern.fullmatch(item[column]):
                issue(record, column, 'invalid_price',
                      'Expected nonnegative digits with the configured decimal separator; no grouping or currency symbol.')

    total = sum(counts.values())
    return {
        'schemaVersion': '1.0',
        'sourceSha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'rows': len(rows),
        'columns': header,
        'passedConfiguredChecks': severities['error'] == 0,
        'summary': {'errors': severities['error'], 'warnings': severities['warning'],
                    'affectedDataRecords': len(affected), 'issuesTotal': total,
                    'issuesReturned': len(issues), 'issuesTruncated': total > len(issues),
                    'byCode': dict(sorted(counts.items()))},
        'issues': issues,
        'scope': {
            'readOnly': True, 'recordNumbering': 'CSV records, header is 1; not physical lines',
            'identifierComparison': 'exact original text, case sensitive',
            'decimalSeparator': decimal,
            'limitation': 'Checks only configured fields. Does not certify any store import, tax, product truth, or barcode registration.'
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_json', type=Path)
    args = parser.parse_args()
    if args.input_json.stat().st_size > MAX_BYTES * 7:
        parser.error('JSON input is too large.')
    try:
        result = audit_catalog(json.loads(args.input_json.read_text(encoding='utf-8-sig')))
    except (InputError, ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
