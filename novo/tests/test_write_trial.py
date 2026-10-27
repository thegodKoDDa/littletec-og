from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.protocol import record_from_response
from littletec.write_trial import run_trial
from test_protocol import IDENTITY, sample_layers


class Backend:
    def __init__(self, fail_change=False):
        self.layers = sample_layers()
        self.sent = []
        self.allowed = set()
        self.fail_change = fail_change

    def read(self):
        return {'folder': 'fake-backup', 'layers': deepcopy(self.layers), 'identity': IDENTITY,
                'manifest': {'capabilities': {'devices': [{'path': 'fake-path'}]}}}

    def allow_packets(self, values):
        self.allowed = values

    def send(self, packets):
        self.sent.extend(packets)
        for packet in packets:
            if packet[:4] == b'\x03\xfd\xfe\xff':
                continue
            self.layers[0][0] = b'\x03\xfa' + packet[2:51] + bytes(14)
            if self.fail_change and packet[12] == 0x73:
                raise OSError('simulated disconnect after temporary write')


class WriteTrialTests(unittest.TestCase):
    def test_approval_required_before_read_or_write(self):
        backend = Backend()
        with self.assertRaises(PermissionError):
            run_trial(backend)
        self.assertEqual(backend.sent, [])

    def test_noop_change_and_exact_restoration(self):
        backend = Backend()
        initial = deepcopy(backend.layers)
        report = run_trial(backend, approved=True)
        self.assertTrue(report['complete'])
        self.assertTrue(report['noop_verified'])
        self.assertTrue(report['change_verified'])
        self.assertTrue(report['restoration_verified'])
        self.assertEqual(backend.layers, initial)
        self.assertEqual(len(backend.sent), 6)

    def test_failure_after_write_still_restores_original(self):
        backend = Backend(fail_change=True)
        initial = deepcopy(backend.layers)
        report = run_trial(backend, approved=True)
        self.assertFalse(report['complete'])
        self.assertTrue(report['restoration_verified'])
        self.assertEqual(backend.layers, initial)
