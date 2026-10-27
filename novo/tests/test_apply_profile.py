from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.protocol import profile_from_layers
from littletec.write_service import apply_profile
from test_write_trial import Backend


class ApplyTests(unittest.TestCase):
    def profile(self, backend):
        snapshot = backend.read()
        return snapshot, profile_from_layers(snapshot['layers'], snapshot['identity'])

    def test_refuses_before_validated_restore(self):
        backend = Backend()
        snapshot, profile = self.profile(backend)
        with patch('littletec.write_service.validation_for', return_value=False), self.assertRaises(PermissionError):
            apply_profile(snapshot, profile, backend)
        self.assertEqual(backend.sent, [])

    def test_applies_selected_key_after_fresh_backup_and_verifies(self):
        backend = Backend()
        snapshot, profile = self.profile(backend)
        profile['layers'][0][0] = {'type': 'keyboard', 'steps': [{'key': 'F24', 'modifiers': []}]}
        with patch('littletec.write_service.validation_for', return_value=True):
            result = apply_profile(snapshot, profile, backend)
        self.assertEqual(len(backend.sent), 2)
        self.assertEqual(profile_from_layers(result['layers'], result['identity'])['layers'][0][0], profile['layers'][0][0])

    def test_failure_restores_original_configuration(self):
        backend = Backend(fail_change=True)
        initial = deepcopy(backend.layers)
        snapshot, profile = self.profile(backend)
        profile['layers'][0][0] = {'type': 'keyboard', 'steps': [{'key': 'F24', 'modifiers': []}]}
        with patch('littletec.write_service.validation_for', return_value=True), self.assertRaisesRegex(RuntimeError, 'restaurada'):
            apply_profile(snapshot, profile, backend)
        self.assertEqual(backend.layers, initial)

    def test_device_change_with_identical_records_never_writes(self):
        for field in ('path', 'identity'):
            backend = Backend()
            snapshot, profile = self.profile(backend)
            profile['layers'][0][0] = {'type': 'keyboard', 'steps': [{'key': 'F24', 'modifiers': []}]}
            fresh = deepcopy(snapshot)
            if field == 'path':
                fresh['manifest']['capabilities']['devices'][0]['path'] = 'other-path'
            else:
                fresh['identity'] = dict(snapshot['identity'], variant=99)
            with self.subTest(field=field), patch.object(backend, 'read', return_value=fresh), patch(
                    'littletec.write_service.validation_for', return_value=True):
                with self.assertRaisesRegex(RuntimeError, 'dispositivo mudou'):
                    apply_profile(snapshot, profile, backend)
            self.assertEqual(backend.sent, [])
            self.assertEqual(backend.allowed, set())

    def test_revoked_receipt_before_send_never_writes(self):
        backend = Backend()
        snapshot, profile = self.profile(backend)
        profile['layers'][0][0] = {'type': 'keyboard', 'steps': [{'key': 'F24', 'modifiers': []}]}
        with patch('littletec.write_service.validation_for', side_effect=[True, False]):
            with self.assertRaisesRegex(PermissionError, 'leitura atual'):
                apply_profile(snapshot, profile, backend)
        self.assertEqual(backend.sent, [])
        self.assertEqual(backend.allowed, set())

    def test_stale_backup_or_encoder_changes_never_write(self):
        for kind in ('stale', 'encoder'):
            backend = Backend()
            snapshot, profile = self.profile(backend)
            if kind == 'encoder':
                profile['layers'][0][12] = {'type': 'keyboard', 'steps': [{'key': 'F24', 'modifiers': []}]}
            else:
                data = bytearray(backend.layers[0][0]);data[12] = 5;backend.layers[0][0] = bytes(data)
            with self.subTest(kind=kind), patch('littletec.write_service.validation_for', return_value=True):
                with self.assertRaises((RuntimeError, ValueError)):
                    apply_profile(snapshot, profile, backend)
            self.assertEqual(backend.sent, [])
