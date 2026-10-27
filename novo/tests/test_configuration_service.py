from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.configuration_service import ConfigurationService, validate_configuration_packets
from littletec.protocol import (COMMIT_PACKET, READ_TO_WRITE, index_layers, profile_from_layers,
                               encode_record, packet_for_record, normalize_encoder_headers)
from test_write_trial import Backend


class ProductBackend(Backend):
    def __init__(self, fail_led=False, fail_keys=False):
        super().__init__()
        self.fail_led, self.fail_keys = fail_led, fail_keys
        self.leds = []
        for layer, packets in enumerate(self.layers):
            by_id = {p[2]: p for p in packets}
            self.layers[layer] = [by_id[i] for i in (*range(1,16),18,17,16,21,20,19,24,23,22)]

    def read(self):
        snapshot = super().read()
        snapshot['raw_layers'] = deepcopy(snapshot['layers'])
        snapshot['layers'] = normalize_encoder_headers(snapshot['layers'])
        snapshot['profile'] = profile_from_layers(snapshot['layers'], snapshot['identity'])
        return snapshot

    def send_led(self, packet, snapshot):
        self.leds.append(packet)
        if self.fail_led:
            raise OSError('LED desconectado')

    def send_keys(self, packets, snapshot):
        validate_configuration_packets(packets)
        self.sent.extend(packets)
        for packet in packets:
            if packet == COMMIT_PACKET:
                continue
            write_id, layer = packet[2], packet[3]
            response = bytearray(b'\x03\xfa' + packet[2:51] + bytes(14))
            index = write_id - 1
            self.layers[layer-1][index] = bytes(response)
            if self.fail_keys:
                self.fail_keys = False
                raise OSError('Falha após escrita parcial')


class ProductServiceTests(unittest.TestCase):
    def test_direct_led_needs_no_trial_or_observer_and_preserves_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = ProductBackend()
            before = deepcopy(backend.layers)
            service = ConfigurationService(backend, directory)
            result = service.apply_led(1, 'blue', 3)
            self.assertEqual(result['lighting']['layer'], 3)
            self.assertEqual(service.last_led(result['snapshot'], 3)['color'], 'blue')
            self.assertEqual(before, backend.layers)
            self.assertTrue(Path(result['journal']).exists())
            self.assertEqual(len(backend.leds), 1)

    def test_failed_led_invalidates_last_command_instead_of_claiming_success(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = ProductBackend()
            service = ConfigurationService(backend, directory)
            result = service.apply_led(1, 'cyan', 1)
            backend.fail_led = True
            with self.assertRaisesRegex(RuntimeError, 'LED desconectado'):
                service.apply_led(1, 'red', 1, result['snapshot'])
            self.assertIsNone(service.last_led(result['snapshot'], 1))

    def test_write_all_layers_and_encoder_indices_and_verify_normalized_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = ProductBackend()
            snapshot = backend.read()
            profile = profile_from_layers(snapshot['layers'], snapshot['identity'])
            for layer, position in ((0, 0), (1, 12), (2, 17)):
                profile['layers'][layer][position] = {'type': 'keyboard', 'steps': [{'key': 'B', 'modifiers': []}]}
            result = ConfigurationService(backend, directory).apply_keys(snapshot, profile)
            self.assertEqual(profile_from_layers(result['snapshot']['layers'], snapshot['identity'])['layers'], profile['layers'])
            self.assertEqual([p[2] for p in backend.sent if p != COMMIT_PACKET], [1, 16, 21])

    def test_failed_mapping_restores_all_records(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = ProductBackend(fail_keys=True)
            snapshot = backend.read()
            before = backend.read()['layers']
            profile = profile_from_layers(snapshot['layers'], snapshot['identity'])
            profile['layers'][1][14] = {'type': 'media', 'command': 'mute'}
            with self.assertRaisesRegex(RuntimeError, 'restaurada e relida'):
                ConfigurationService(backend, directory).apply_keys(snapshot, profile)
            self.assertEqual(backend.read()['layers'], before)

    def test_stale_snapshot_never_sends_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = ProductBackend()
            snapshot = backend.read()
            profile = profile_from_layers(snapshot['layers'], snapshot['identity'])
            data = bytearray(backend.layers[0][0]); data[12] = 7; backend.layers[0][0] = bytes(data)
            with self.assertRaises(RuntimeError):
                ConfigurationService(backend, directory).apply_keys(snapshot, profile)
            self.assertEqual(backend.sent, [])

    def test_limits_forbid_flash_led_reserved_and_missing_commit(self):
        good = packet_for_record(encode_record({'type': 'none'}, 16, 1))
        validate_configuration_packets([good, COMMIT_PACKET])
        for value in ([], [COMMIT_PACKET], [good], [b'\x03\xef' + bytes(63), COMMIT_PACKET],
                      [packet_for_record(encode_record({'type':'none'}, 13, 1)), COMMIT_PACKET]):
            with self.assertRaises(ValueError):
                validate_configuration_packets(value)
