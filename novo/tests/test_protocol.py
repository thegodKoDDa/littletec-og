from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.catalog import KEYS
from littletec.profile import validate_action
from littletec.protocol import (KEY_CODES, PHYSICAL_RECORDS, COMMIT_PACKET, encode_record,
                               decode_record, encode_lighting, packet_for_record,
                               record_from_response, profile_from_layers, build_plan)

FIXTURE = json.loads((Path(__file__).parent / 'fixtures/original-record-vectors.json').read_text())
IDENTITY = {'key_count': 12, 'encoder_count': 2, 'variant': 0}


def sample_layers():
    layers = []
    for layer in (1, 2, 3):
        packets = []
        for index in range(1, 25):
            raw = bytearray(65)
            raw[:5] = bytes([3, 0xfa, index, layer, 1])
            raw[10], raw[12] = 1, 4
            if index in (16, 17, 18):
                raw[4] = 2
                raw[11], raw[12] = {16: 0xe9, 17: 0xe2, 18: 0xea}[index], 0
            packets.append(bytes(raw))
        layers.append(packets)
    return layers


class ProtocolTests(unittest.TestCase):
    def test_real_encoder_headers_after_write_preserve_same_actions(self):
        from littletec.protocol import normalize_encoder_headers
        vectors = json.loads((Path(__file__).parent / 'fixtures/encoder-stored-id-vectors.json').read_text())
        snapshots = []
        for name in ('before_trios', 'after_trios'):
            layers = sample_layers()
            for number in range(3):
                by_id = {p[2]: p for p in layers[number]}
                layers[number] = [by_id[i] for i in (*range(1,16),18,17,16,21,20,19,24,23,22)]
            layers[0][15:21] = [bytes.fromhex(raw) for raw in vectors[name]]
            snapshots.append(profile_from_layers(normalize_encoder_headers(layers), IDENTITY))
        self.assertEqual(snapshots[0]['layers'], snapshots[1]['layers'])
        self.assertEqual([a.get('command') for a in snapshots[1]['layers'][0][12:15]], ['volume_down', 'mute', 'volume_up'])

    def test_206_independent_records_match_original_editor(self):
        self.assertGreaterEqual(len(FIXTURE['vectors']), 206)
        for vector in FIXTURE['vectors']:
            with self.subTest(case=vector['case']):
                if 'lighting' in vector:
                    actual = encode_lighting(**vector['lighting'], layer=vector['layer'])
                else:
                    actual = encode_record(vector['action'], vector['index'], vector['layer'])
                    self.assertEqual(decode_record(actual), validate_action(vector['action']))
                self.assertEqual(actual.hex(), vector['record_hex'])

    def test_packets_match_native_hid_write_with_no_hardware_io(self):
        macro = {'type': 'keyboard', 'steps': [{'key': 'C', 'modifiers': ['Ctrl']}, {'key': 'D', 'modifiers': ['Shift']}]}
        packets = [packet_for_record(encode_lighting(0, 'yellow', 1)),
                   packet_for_record(encode_record(macro, 1, 1)), COMMIT_PACKET]
        self.assertEqual([p.hex() for p in packets], FIXTURE['simulated_packets'])
        self.assertTrue(all(len(p) == 65 for p in packets))

    def test_every_editor_key_has_recovered_usage_code(self):
        self.assertEqual(set(KEYS), set(KEY_CODES))
        self.assertEqual(len(KEY_CODES), len(set(KEY_CODES.values())))

    def test_encoder_read_ids_are_normalized_to_original_editing_slots(self):
        profile = profile_from_layers(sample_layers(), IDENTITY)
        self.assertEqual([a['command'] for a in profile['layers'][0][12:15]], ['volume_down', 'mute', 'volume_up'])
        self.assertEqual(profile['lighting'], [{'mode': None, 'color': None}] * 3)

    def test_noop_plan_preserves_factory_media_count_and_has_no_changes(self):
        layers = sample_layers()
        profile = profile_from_layers(layers, IDENTITY)
        plan = build_plan(layers, IDENTITY, profile)
        self.assertEqual(plan['changes'], [])
        self.assertFalse(plan['hardware_sent'])
        self.assertFalse(plan['restoration_validated'])

    def test_change_plan_includes_exact_inverse_and_targets_selected_slot(self):
        layers = sample_layers()
        profile = profile_from_layers(layers, IDENTITY)
        profile['layers'][0][12] = {'type': 'keyboard', 'steps': [{'key': 'F24', 'modifiers': []}]}
        plan = build_plan(layers, IDENTITY, profile)
        self.assertEqual(len(plan['changes']), 1)
        change = plan['changes'][0]
        self.assertEqual(change['record_index'], 16)
        before = bytes.fromhex(change['restore_packet_hex'])
        self.assertEqual(before[:5], bytes([3, 0xfd, 16, 1, 2]))
        self.assertEqual(before[11:13], b'\xea\x00')

    def test_unknown_types_reserved_fields_and_usage_are_preserved(self):
        record = bytearray(encode_record({'type': 'keyboard', 'steps': [{'key': 'A', 'modifiers': []}]}, 1, 1))
        for offset, value in ((3, 99), (7, 1), (11, 255)):
            sample = bytearray(record)
            sample[offset] = value
            action = decode_record(sample)
            self.assertEqual(action['type'], 'raw')
            self.assertEqual(encode_record(action, 1, 1, original=sample), sample)
            with self.assertRaises(ValueError):
                encode_record(action, 2, 1)

    def test_sequence_limit_prevents_overwriting_50_byte_record(self):
        action = {'type': 'keyboard', 'steps': [{'key': 'A', 'modifiers': []}] * 20}
        self.assertEqual(decode_record(encode_record(action, 1, 1)), action)
        action['steps'].append({'key': 'B', 'modifiers': []})
        with self.assertRaisesRegex(ValueError, '20'):
            encode_record(action, 1, 1)
