import copy
import hashlib
import unittest

from catalog_preflight import InputError, MAX_ISSUES, audit_catalog


class CatalogPreflightTests(unittest.TestCase):
    def test_identifiers_and_unicode_remain_exact(self):
        payload = {'csvText': 'sku,name\n00123,Żółta lampa\n123,Žlutá lampa\n'}
        original = copy.deepcopy(payload)
        result = audit_catalog(payload)
        self.assertEqual(payload, original)
        self.assertTrue(result['passedConfiguredChecks'])
        self.assertEqual(result['sourceSha256'], hashlib.sha256(payload['csvText'].encode()).hexdigest())

    def test_exact_duplicate_and_blank_name(self):
        result = audit_catalog({'csvText': 'sku,name\n001,A\n001,\n'})
        self.assertFalse(result['passedConfiguredChecks'])
        self.assertEqual(result['summary']['byCode'], {'duplicate_sku': 1, 'missing_value': 1})
        self.assertEqual(result['summary']['affectedDataRecords'], 1)

    def test_configured_comma_decimal_with_semicolon(self):
        result = audit_catalog({'csvText': 'sku;name;price\n01;Lampa;12,50\n',
                                'delimiter': ';', 'priceColumns': ['price'], 'decimalSeparator': ','})
        self.assertTrue(result['passedConfiguredChecks'])

    def test_no_silent_price_inference(self):
        for price in ('1,234.50', 'NaN', '1e3', '-5', '12 USD', ' 2.50 ', '١٢'):
            with self.subTest(price=price):
                result = audit_catalog({'csvText': 'sku;name;price\n01;A;' + price + '\n',
                                        'delimiter': ';', 'priceColumns': ['price']})
                self.assertIn('invalid_price', result['summary']['byCode'])

    def test_missing_schema_column_never_passes(self):
        result = audit_catalog({'csvText': 'id,name\n01,A\n'})
        self.assertFalse(result['passedConfiguredChecks'])
        self.assertEqual(result['issues'][0]['code'], 'missing_column')

    def test_multiline_quoted_values(self):
        result = audit_catalog({'csvText': '\ufeffsku,name\r\n01,"line 1\nline 2"\r\n'})
        self.assertTrue(result['passedConfiguredChecks'])
        self.assertEqual(result['rows'], 1)

    def test_invalid_structures_are_rejected(self):
        for text in ('', 'sku,name\n', 'sku,name\n01,A,extra\n', 'sku,name\n01\n',
                     'sku, sku\n01,A\n', 'sku,\n01,A\n', 'sku,name\n01,"broken\n',
                     'sku,name\n01,A\x00\n'):
            with self.subTest(text=text):
                with self.assertRaises(InputError):
                    audit_catalog({'csvText': text})

    def test_limit_and_truncation_preserve_totals(self):
        text = 'sku,name\n' + ''.join('same,\n' for _ in range(1000))
        result = audit_catalog({'csvText': text})
        self.assertEqual(result['summary']['errors'], 1999)
        self.assertEqual(len(result['issues']), MAX_ISSUES)
        self.assertTrue(result['summary']['issuesTruncated'])
        with self.assertRaises(InputError):
            audit_catalog({'csvText': 'sku,name\n' + 'a,b\n' * 10001})

    def test_sku_whitespace_is_flagged_without_merging(self):
        result = audit_catalog({'csvText': 'sku,name\n01,A\n 01 ,B\n'})
        self.assertEqual(result['summary']['warnings'], 1)
        self.assertNotIn('duplicate_sku', result['summary']['byCode'])

    def test_settings_are_validated(self):
        for change in ({'requiredColumns': 'sku'}, {'priceColumns': [False]},
                       {'unknown': 1}, {'delimiter': '|'}, {'skuColumn': ''},
                       {'decimalSeparator': ':'}):
            with self.subTest(change=change):
                with self.assertRaises(InputError):
                    audit_catalog({'csvText': 'sku,name\n01,A\n', **change})


if __name__ == '__main__':
    unittest.main()
