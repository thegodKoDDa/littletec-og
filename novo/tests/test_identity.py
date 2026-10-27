from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from littletec.identity import OBSERVED_REQUEST, parse_response, query, validate_capabilities
spec = importlib.util.spec_from_file_location('hid_caps_windows', ROOT / 'tools/hid_caps_windows.py')
caps_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(caps_tool)


def capabilities():
    entry = {'report_id': 3, 'bit_size': 8, 'report_count': 64}
    return {'vid': '1189', 'pid': '8842', 'interface': 'MI_00',
            'path': r'\\?\hid#vid_1189&pid_8842&mi_00#test',
            'caps': {'Usage': 1, 'UsagePage': 0xff00, 'InputReportByteLength': 65,
                     'OutputReportByteLength': 65, 'FeatureReportByteLength': 0},
            'reports': {'input': [entry.copy()], 'output': [entry.copy()]}}


class FakeDevice:
    def __init__(self, response=b'\x03\xfb\x0c\x02\x00' + bytes(60), written=65):
        self.response, self.written = response, written
        self.writes, self.reads = [], []
        self.closed = 0

    def write(self, packet):
        self.writes.append(packet)
        return self.written

    def read(self, size, timeout):
        self.reads.append((size, timeout))
        return self.response

    def close(self):
        self.closed += 1


class IdentityTests(unittest.TestCase):
    def test_exact_request_and_full_response_with_timeout(self):
        device = FakeDevice()
        response, identity = query(device, capabilities(), OBSERVED_REQUEST)
        self.assertEqual(device.writes, [OBSERVED_REQUEST])
        self.assertEqual(device.reads, [(65, 1000)])
        self.assertEqual(device.closed, 1)
        self.assertEqual(len(response), 65)
        self.assertEqual((identity['key_count'], identity['encoder_count']), (12, 2))

    def test_refuses_other_packets_without_writing(self):
        for request in (b'\x03\xef\xef' + bytes(62), b'\x03\xfb\xfb\xfb' + bytes(61),
                        OBSERVED_REQUEST[:64], b'\x03\xfa' + bytes(63)):
            device = FakeDevice()
            with self.subTest(request=request.hex()), self.assertRaises(ValueError):
                query(device, capabilities(), request)
            self.assertEqual(device.writes, [])
            self.assertEqual(device.closed, 1)

    def test_wrong_identity_interface_or_lengths_never_write(self):
        for change in ('vid', 'interface', 'path', 'length', 'report_id'):
            caps = capabilities()
            if change in ('vid', 'interface', 'path'):
                caps[change] = 'wrong'
            elif change == 'length':
                caps['caps']['InputReportByteLength'] = 64
            else:
                caps['reports']['input'][0]['report_id'] = 0
            device = FakeDevice()
            with self.subTest(change=change), self.assertRaises(ValueError):
                query(device, caps, OBSERVED_REQUEST)
            self.assertEqual(device.writes, [])
            self.assertEqual(device.closed, 1)

    def test_short_write_stops_before_read(self):
        device = FakeDevice(written=64)
        with self.assertRaises(OSError):
            query(device, capabilities(), OBSERVED_REQUEST)
        self.assertEqual(device.reads, [])
        self.assertEqual(device.closed, 1)

    def test_timeout_short_and_wrong_prefix_responses_close_device(self):
        for response, exception in ((b'', TimeoutError), (bytes(64), ValueError),
                                    (bytes(65), ValueError), (b'\x03\xfb\xff\xff\x00' + bytes(60), ValueError)):
            device = FakeDevice(response=response)
            with self.subTest(response=response), self.assertRaises(exception):
                query(device, capabilities(), OBSERVED_REQUEST)
            self.assertEqual(device.closed, 1)

    def test_invalid_timeouts_never_write(self):
        for timeout in (-1, 0, 2001, True):
            device = FakeDevice()
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                query(device, capabilities(), OBSERVED_REQUEST, timeout)
            self.assertEqual(device.writes, [])
            self.assertEqual(device.closed, 1)

    def test_path_filter_excludes_other_interfaces_and_partial_matches(self):
        self.assertTrue(caps_tool.target_path(r'\\?\hid#vid_1189&pid_8842&mi_00#test'))
        for path in (r'\\?\hid#vid_1189&pid_8842&mi_01#test',
                     r'\\?\hid#vid_1189&pid_8842&mi_000#test',
                     r'\\?\hid#vid_1234&pid_8842&mi_00#test', r'C:\file'):
            self.assertFalse(caps_tool.target_path(path))
