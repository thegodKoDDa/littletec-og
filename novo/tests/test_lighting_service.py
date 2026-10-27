from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.lighting_service import (lighting_packet, parse_lighting_packet,
                                      run_trial, send_lighting, trial_plan,
                                      apply_lighting, load_state, record_validated_trial)
from littletec.protocol import COMMIT_PACKET
from littletec.write_service import send_checked
from test_write_trial import Backend
from test_identity import FakeDevice, capabilities
from littletec.identity import OBSERVED_REQUEST, parse_response


class LedBackend(Backend):
    def __init__(self, fail_red=False, diverge=False):
        super().__init__()
        self.fail_red = fail_red
        self.diverge = diverge
        self.reads = 0

    def read(self):
        self.reads += 1
        return super().read()

    def send(self, packet):
        parse_lighting_packet(packet)
        self.sent.append(packet)
        if self.fail_red and packet == lighting_packet(1, 'red', 1):
            raise OSError('simulated LED failure')
        if self.diverge:
            data = bytearray(self.layers[0][0])
            data[12] = 7
            self.layers[0][0] = bytes(data)


class LightingTests(unittest.TestCase):
    def test_windows_transport_revalidates_identity_and_closes_handles(self):
        for scenario in ('ok', 'short', 'wrong_identity', 'wrong_path', 'wrong_caps', 'wrong_version'):
            caps = capabilities()
            expected = Backend().read()
            expected['manifest']['capabilities']['devices'][0]['path'] = caps['path']
            expected['identity'] = parse_response(b'\x03\xfb\x0c\x02\x00' + bytes(60))
            identity = FakeDevice(response=b'\x03\xfb\x0c\x02' + bytes([1 if scenario == 'wrong_identity' else 0]) + bytes(60))
            outgoing = FakeDevice(written=64 if scenario == 'short' else 65)
            opened = []
            identity.open_path = lambda path: opened.append(('identity', path))
            outgoing.open_path = lambda path: opened.append(('led', path))
            handles = iter((identity, outgoing))
            hid = SimpleNamespace(version_str=lambda: '0.14.0' if scenario == 'wrong_version' else '0.15.0',
                enumerate=lambda *_: [{'path': caps['path'].encode(), 'interface_number': 0,
                                       'usage_page': 0xff00, 'usage': 1}], device=lambda: next(handles))
            if scenario == 'wrong_path':
                caps['path'] += '-other'
            if scenario == 'wrong_caps':
                caps['caps']['OutputReportByteLength'] = 64
            module = SimpleNamespace(collect=lambda: {'devices': [caps]})
            spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None))
            with self.subTest(scenario=scenario), patch('littletec.lighting_service.sys', SimpleNamespace(platform='win32', frozen=True)), patch.dict(
                    sys.modules, {'hid': hid}), patch('littletec.lighting_service.importlib.util.spec_from_file_location', return_value=spec), patch(
                    'littletec.lighting_service.importlib.util.module_from_spec', return_value=module), patch('littletec.lighting_service.time.sleep'):
                if scenario == 'ok':
                    packet = lighting_packet(1, 'cyan', 1)
                    send_lighting(packet, expected)
                    self.assertEqual(outgoing.writes, [packet, COMMIT_PACKET])
                    self.assertEqual(identity.writes, [OBSERVED_REQUEST])
                    self.assertEqual(identity.reads, [(65, 1000)])
                    self.assertEqual((identity.closed, outgoing.closed), (1, 1))
                else:
                    with self.assertRaises((RuntimeError, ValueError, OSError)):
                        send_lighting(lighting_packet(1, 'cyan', 1), expected)
                    self.assertNotIn(COMMIT_PACKET, outgoing.writes)
                    if scenario == 'short':
                        self.assertEqual(outgoing.closed, 1)
                    elif scenario == 'wrong_identity':
                        self.assertEqual(opened, [('identity', caps['path'].encode())])
                    else:
                        self.assertEqual(opened, [])

    def test_packets_match_independent_native_capture(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/original-led-trial-vectors.json').read_text())
        for color, expected in fixture['packets'].items():
            self.assertEqual(lighting_packet(1, color, 1).hex(), expected)

    def test_only_canonical_led_packets_allowed_and_key_transport_stays_separate(self):
        valid = lighting_packet(1, 'cyan', 1)
        invalid = [COMMIT_PACKET, valid[:-1], b'\x03\xef' + bytes(63)]
        for offset, value in ((1, 0xfd), (2, 1), (3, 0), (3, 4), (4, 1),
                              (10, 0), (11, 1), (12, 0x56), (12, 0x81), (51, 1)):
            packet = bytearray(valid)
            packet[offset] = value
            invalid.append(bytes(packet))
        for packet in invalid:
            with self.subTest(packet=packet.hex()), self.assertRaises(ValueError):
                send_lighting(packet, {})  # Recusa antes de carregar Windows/HID.
        with self.assertRaises(ValueError):
            send_checked([valid], 'fake-path')
        with self.assertRaises(ValueError):
            trial_plan(True)

    def test_initialization_requires_specific_approval_before_any_read_or_write(self):
        backend = LedBackend()
        with self.assertRaises(PermissionError):
            run_trial(backend, lambda *_: True, 'unused.json')
        self.assertEqual(backend.reads, 0)
        self.assertEqual(backend.sent, [])

    def run_with_report(self, backend, observer):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trial.json'
            def observed(stage, spec):
                # Plano inverso existe no disco antes da primeira confirmação.
                saved = json.loads(path.read_text())
                self.assertIn('source_backup', saved)
                self.assertEqual(saved['restore_packet_hex'], lighting_packet(1, 'cyan', 1).hex())
                return observer(stage, spec)
            with patch('littletec.lighting_service.state_path', return_value=Path(directory) / 'state.json'):
                report = run_trial(backend, observed, path, approved_replace_unread_led=True)
            self.assertEqual(json.loads(path.read_text()), report)
            return report

    def test_visual_trial_restores_cyan_and_preserves_all_key_records(self):
        backend = LedBackend()
        layers = deepcopy(backend.layers)
        observed = []
        report = self.run_with_report(backend, lambda stage, spec: observed.append(stage) or True)
        self.assertTrue(report['complete'])
        self.assertFalse(report['initial_led_read'])
        self.assertFalse(report['initial_state_restorable'])
        self.assertEqual(observed, ['baseline', 'test', 'restore'])
        self.assertEqual(backend.sent, [lighting_packet(1, c, 1) for c in ('cyan', 'red', 'cyan')])
        self.assertEqual(layers, backend.layers)

    def test_unconfirmed_baseline_never_sends_red(self):
        backend = LedBackend()
        report = self.run_with_report(backend, lambda stage, _: stage != 'baseline')
        self.assertFalse(report['complete'])
        self.assertNotIn(lighting_packet(1, 'red', 1), backend.sent)

    def test_error_or_visual_rejection_still_restores_but_never_claims_success(self):
        for kind in ('write', 'visual', 'observer'):
            backend = LedBackend(fail_red=kind == 'write')
            def observed(stage, _):
                if kind == 'observer' and stage == 'test':
                    raise TimeoutError('No visual response')
                return not (kind == 'visual' and stage == 'test')
            report = self.run_with_report(backend, observed)
            self.assertFalse(report['complete'])
            self.assertTrue(report['restoration_visual_verified'])
            self.assertEqual(backend.sent[-1], lighting_packet(1, 'cyan', 1))

    def test_unexpected_key_change_prevents_red_and_receipt(self):
        backend = LedBackend(diverge=True)
        report = self.run_with_report(backend, lambda *_: True)
        self.assertFalse(report['complete'])
        self.assertFalse(report['keys_unchanged'])
        self.assertNotIn(lighting_packet(1, 'red', 1), backend.sent)

    def test_changed_identity_is_refused_even_if_records_match(self):
        backend = LedBackend()
        original_read = backend.read
        def read():
            value = original_read()
            if backend.reads > 1:
                value['manifest']['capabilities']['devices'][0]['path'] = 'other-path'
            return value
        with patch.object(backend, 'read', side_effect=read):
            report = self.run_with_report(backend, lambda *_: True)
        self.assertFalse(report['complete'])
        self.assertNotIn(lighting_packet(1, 'red', 1), backend.sent)

    def test_incomplete_trial_cannot_release_normal_led_application(self):
        report = self.run_with_report(LedBackend(), lambda stage, _: stage != 'test')
        with self.assertRaises(ValueError):
            record_validated_trial(report)

    def test_normal_application_requires_layer_and_device_specific_validation(self):
        with tempfile.TemporaryDirectory() as directory, patch(
                'littletec.lighting_service.state_path', side_effect=lambda layer: Path(directory) / f'state-{layer}.json'):
            backend = LedBackend()
            snapshot = backend.read()
            with self.assertRaises(PermissionError):
                apply_lighting(snapshot, 1, 'green', 1, lambda *_: True, Path(directory) / 'apply.json', backend)
            self.assertEqual(backend.sent, [])
            report = run_trial(backend, lambda *_: True, Path(directory) / 'trial.json', approved_replace_unread_led=True)
            record_validated_trial(report)
            self.assertIsNotNone(load_state(snapshot, 1))
            self.assertIsNone(load_state(snapshot, 2))
            other = deepcopy(snapshot)
            other['manifest']['capabilities']['devices'][0]['path'] = 'other-path'
            self.assertIsNone(load_state(other, 1))

    def test_normal_application_confirms_color_or_restores_and_invalidates_uncertain_state(self):
        for scenario in ('success', 'reject_before', 'reject_after', 'reject_restore', 'short_write'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory, patch(
                    'littletec.lighting_service.state_path', return_value=Path(directory) / 'state.json'):
                backend = LedBackend()
                snapshot = backend.read()
                report = run_trial(backend, lambda *_: True, Path(directory) / 'trial.json', approved_replace_unread_led=True)
                record_validated_trial(report)
                backend.sent.clear()
                backend.fail_red = scenario == 'short_write'
                def observe(stage, _):
                    return not ((scenario == 'reject_before' and stage == 'before') or
                                (scenario in ('reject_after', 'reject_restore') and stage == 'applied') or
                                (scenario == 'reject_restore' and stage == 'restore_previous'))
                if scenario == 'reject_before':
                    with self.assertRaises(RuntimeError):
                        apply_lighting(snapshot, 1, 'red', 1, observe, Path(directory) / 'apply.json', backend)
                    self.assertEqual(backend.sent, [])
                    self.assertIsNone(load_state(snapshot, 1))
                    continue
                result = apply_lighting(snapshot, 1, 'red', 1, observe, Path(directory) / 'apply.json', backend)
                state = load_state(snapshot, 1)
                self.assertEqual(result['complete'], scenario == 'success')
                if scenario == 'success':
                    self.assertEqual(state['current_packet_hex'], lighting_packet(1, 'red', 1).hex())
                    self.assertEqual(backend.sent, [lighting_packet(1, 'red', 1)])
                elif scenario == 'reject_restore':
                    self.assertIsNone(state)
                    self.assertIn('restoration_error', result)
                else:
                    self.assertTrue(result['restoration_visual_verified'])
                    self.assertEqual(state['current_packet_hex'], lighting_packet(1, 'cyan', 1).hex())
                    self.assertEqual(backend.sent[-1], lighting_packet(1, 'cyan', 1))
