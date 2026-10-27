from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.diagnostics import presence


class PresenceTests(unittest.TestCase):
    def test_vendor_interface_is_required_for_windows_presence(self):
        report = {'environment': {}, 'windows': {'devices': [
            {'InstanceId': 'HID\\VID_1189&PID_8842&MI_01', 'Status': 'OK', 'Class': 'Keyboard'}]}, 'errors': []}
        self.assertEqual(presence(report), 'NÃO DETECTADO')
        report['windows']['devices'].append(
            {'InstanceId': 'HID\\VID_1189&PID_8842&MI_00\\123', 'Status': 'OK', 'Class': 'HIDClass'})
        self.assertEqual(presence(report), '1189:8842 NO WINDOWS')
        report['windows']['devices'][1]['Status'] = 'Error'
        self.assertEqual(presence(report), 'NÃO DETECTADO')

    def test_failure_is_distinct_from_absence(self):
        self.assertEqual(presence({'errors': ['timeout']}), 'FALHA NO DIAGNÓSTICO')
        self.assertEqual(presence({'errors': []}), 'NÃO DETECTADO')
        self.assertEqual(presence({'environment': {'candidate_devices': [{'vid': '1189'}]}}), 'FAMÍLIA HID NO LINUX')
