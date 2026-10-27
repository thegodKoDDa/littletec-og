from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.catalog import MODELS
from littletec.profile import load, new_profile, save, validate, validate_action


class ProfileTests(unittest.TestCase):
    def test_roundtrip_all_action_types_encoders_and_lighting(self):
        profile = new_profile()
        actions = [
            {'type': 'keyboard', 'steps': [{'key': 'C', 'modifiers': ['Ctrl']}, {'key': 'F24', 'modifiers': ['RightAlt']}]},
            {'type': 'media', 'command': 'volume_up'},
            {'type': 'mouse', 'command': 'wheel_down', 'modifiers': ['Shift']},
            {'type': 'delay', 'ms': 6000},
        ]
        profile['layers'][1][:4] = deepcopy(actions)
        profile['layers'][2][12] = {'type': 'media', 'command': 'previous'}
        profile['lighting'][2] = {'mode': 5, 'color': 'purple'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'perfil.json'
            save(path, profile)
            restored = load(path)
        self.assertEqual(restored, profile)
        self.assertEqual(profile['layers'][0][0], {'type': 'none'})
        self.assertEqual(profile['lighting'][0]['color'], 'red')
        self.assertEqual(len(profile['layers'][0]), 18)

    def test_all_models_have_independent_valid_layers(self):
        for name, (keys, encoders, columns) in MODELS.items():
            with self.subTest(model=name):
                profile = new_profile(keys, encoders, columns, model=name)
                self.assertEqual(validate(profile), profile)
                self.assertEqual(len(profile['layers'][0]), keys + encoders * 3)
                self.assertIsNot(profile['layers'][0], profile['layers'][1])
                self.assertIsNot(profile['layers'][0][0], profile['layers'][1][0])

    def test_v1_migration_preserves_assignments_without_inventing_encoders(self):
        legacy = {'format': 'littletec-profile', 'version': 1, 'name': 'Legado', 'key_count': 2,
                  'layers': [[{'key': '', 'modifiers': []}, {'key': 'C', 'modifiers': ['Ctrl']}]
                             for _ in range(3)]}
        original = deepcopy(legacy)
        converted = validate(legacy)
        self.assertEqual(converted['version'], 2)
        self.assertEqual(converted['encoder_count'], 0)
        self.assertEqual(converted['key_count'], 2)
        self.assertEqual(converted['layers'][2][1]['steps'][0], {'key': 'C', 'modifiers': ['Ctrl']})
        self.assertEqual(legacy, original)

    def test_invalid_save_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'perfil.json'
            profile = new_profile()
            save(path, profile)
            original = path.read_bytes()
            profile['layers'][0][0] = {'type': 'media', 'command': 'Invalid'}
            with self.assertRaises(ValueError):
                save(path, profile)
            self.assertEqual(path.read_bytes(), original)

    def test_rejects_malformed_profiles(self):
        for field, value in [('version', True), ('version', 3), ('key_count', 61),
                             ('key_count', True), ('encoder_count', 5), ('name', ''),
                             ('columns', 0), ('layers', [[]]), ('lighting', [])]:
            with self.subTest(field=field, value=value):
                profile = new_profile()
                profile[field] = value
                with self.assertRaises(ValueError):
                    validate(profile)
        for action in ({'type': 'unknown'}, {'type': 'keyboard', 'steps': []},
                       {'type': 'delay', 'ms': True}, {'type': 'delay', 'ms': 6001},
                       {'type': 'media', 'command': []},
                       {'type': 'keyboard', 'steps': [{'key': 'C', 'modifiers': ['Ctrl', 'Ctrl']}]},
                       {'type': 'mouse', 'command': 'left', 'modifiers': ['Win']}):
            with self.subTest(action=action), self.assertRaises(ValueError):
                validate_action(action)
