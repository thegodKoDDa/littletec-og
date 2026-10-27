from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.config_read import OBSERVED_READ_REQUESTS, read_configuration
from test_identity import capabilities


class FakeDevice:
    def __init__(self, mutate=None, written=65):
        self.responses = [bytes([3, 0xfa, index, layer]) + bytes(61)
                          for layer in range(1, 4) for index in
                          [*range(1, 16), 18, 17, 16, 21, 20, 19, 24, 23, 22]]
        if mutate:
            mutate(self.responses)
        self.written, self.writes, self.reads, self.closed = written, [], [], 0

    def write(self, packet):
        self.writes.append(packet)
        return self.written

    def read(self, size, timeout):
        self.reads.append((size, timeout))
        return self.responses.pop(0)

    def close(self):
        self.closed += 1


class ConfigurationReadTests(unittest.TestCase):
    def test_known_encoder_stored_ids_may_repeat_only_in_validated_trio_slots(self):
        def alias(responses):
            raw = bytearray(responses[15]); raw[2] = 16; responses[15] = bytes(raw)
        device = FakeDevice(mutate=alias)
        raw = read_configuration(device, capabilities(), allow_encoder_aliases=True)
        self.assertEqual([p[2] for p in raw[0]][15:18], [16, 17, 16])
        # A repetição de uma tecla ou ID fora do par não vira um alias permitido.
        for mutate in (lambda r: r.__setitem__(1, r[0]),
                       lambda r: r.__setitem__(15, r[16])):
            with self.assertRaises(ValueError):
                read_configuration(FakeDevice(mutate=mutate), capabilities(), allow_encoder_aliases=True)

    def test_reads_complete_layers_preserving_arrival_order(self):
        device = FakeDevice()
        captured = []
        layers = read_configuration(device, capabilities(), on_packet=lambda *args: captured.append(args))
        self.assertEqual(device.writes, list(OBSERVED_READ_REQUESTS))
        self.assertEqual(len(device.reads), 72)
        self.assertTrue(all(size == 65 and 0 < timeout <= 1000 for size, timeout in device.reads))
        self.assertEqual([len(b''.join(layer)) for layer in layers], [1560, 1560, 1560])
        self.assertEqual([p[2] for p in layers[0]][15:18], [18, 17, 16])
        self.assertEqual(len(captured), 72)
        self.assertEqual(device.closed, 1)

    def test_refuses_other_requests_before_any_write(self):
        device = FakeDevice()
        with self.assertRaises(ValueError):
            read_configuration(device, capabilities(), requests=[b'\x03\xfd' + bytes(63)])
        self.assertEqual(device.writes, [])
        self.assertEqual(device.closed, 1)

    def test_duplicate_record_stops_without_next_layer(self):
        device = FakeDevice(mutate=lambda responses: responses.__setitem__(1, responses[0]))
        with self.assertRaisesRegex(ValueError, 'duplicado'):
            read_configuration(device, capabilities())
        self.assertEqual(len(device.writes), 1)
        self.assertEqual(len(device.reads), 2)
        self.assertEqual(device.closed, 1)

    def test_rejects_wrong_layer_short_packet_and_timeout(self):
        for first, exception in ((bytes([3, 0xfa, 1, 2]) + bytes(61), ValueError),
                                 (bytes(64), ValueError), (b'', TimeoutError)):
            device = FakeDevice(mutate=lambda responses: responses.__setitem__(0, first))
            with self.subTest(first=first), self.assertRaises(exception):
                read_configuration(device, capabilities())
            self.assertEqual(len(device.reads), 1)
            self.assertEqual(device.closed, 1)

    def test_short_write_does_not_read(self):
        device = FakeDevice(written=64)
        with self.assertRaises(OSError):
            read_configuration(device, capabilities())
        self.assertEqual(device.reads, [])
        self.assertEqual(device.closed, 1)

    def test_total_deadline_stops_even_if_individual_reads_might_succeed(self):
        device = FakeDevice()
        with patch('littletec.config_read.time.monotonic', side_effect=[0, 1, 16]):
            with self.assertRaises(TimeoutError):
                read_configuration(device, capabilities())
        self.assertEqual(len(device.writes), 1)
        self.assertEqual(device.reads, [])
        self.assertEqual(device.closed, 1)

    def test_refuses_invalid_timeout_and_capabilities(self):
        for timeout in (-1, 0, True, 2001):
            device = FakeDevice()
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                read_configuration(device, capabilities(), timeout_ms=timeout)
            self.assertEqual(device.writes, [])
        device = FakeDevice()
        caps = capabilities()
        caps['interface'] = 'MI_01'
        with self.assertRaises(ValueError):
            read_configuration(device, caps)
        self.assertEqual(device.writes, [])
        self.assertEqual(device.closed, 1)
