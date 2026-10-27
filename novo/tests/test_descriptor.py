import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'descriptor', Path(__file__).resolve().parents[1] / 'tools/hid_descriptor.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DescriptorTests(unittest.TestCase):
    def test_vendor_report_and_padding(self):
        result = module.summarize(bytes.fromhex(
            '06 00 ff 09 01 a1 01 85 03 75 08 95 3f 81 02 '
            '95 40 91 02 c0'))
        self.assertEqual(result['usage_pages'], ['0xff00'])
        self.assertEqual(result['reports'][0]['wire_bytes'], 64)
        self.assertEqual(result['reports'][1]['wire_bytes'], 65)
        self.assertEqual(result['reports'][1]['report_id'], 3)

    def test_push_pop_and_partial_bytes(self):
        reports = module.summarize(bytes.fromhex(
            '75 01 95 03 81 02 a4 75 08 95 02 91 02 b4 81 03'))['reports']
        self.assertEqual(reports[0]['payload_bits'], 6)
        self.assertEqual(reports[0]['wire_bytes'], 1)
        self.assertEqual(reports[1]['wire_bytes'], 2)

    def test_separate_ids(self):
        reports = module.summarize(bytes.fromhex(
            '75 08 95 02 85 01 81 02 85 02 81 02'))['reports']
        self.assertEqual([r['report_id'] for r in reports], [1, 2])

    def test_rejects_incomplete_or_ambiguous_descriptors(self):
        for raw in ('76 08', 'fe', 'b4', 'a4', 'a1 01', 'c0',
                    '85 00', '81 02',
                    '75 08 95 01 81 02 85 01 81 02'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                module.summarize(bytes.fromhex(raw))


if __name__ == '__main__':
    unittest.main()
