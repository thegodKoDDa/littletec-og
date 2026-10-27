from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.catalog import (
    COLOR_SHADES, ENCODER_PRESETS, LAYER_TEMPLATES, QUICK_ACTIONS,
    SHORTCUT_PRESETS, action_from_qt_event, action_from_text,
    closest_hardware_color, hex_to_hsv, hsv_to_hex
)
from littletec.configuration_service import ConfigurationService
from littletec.editor_session import EditorSession
from littletec.protocol import decode_record, encode_record
from test_configuration_service import ProductBackend
import tempfile


class EnhancementsTests(unittest.TestCase):
    def test_physical_keyboard_recognition_key_4_and_ctrl_c_ctrl_v(self):
        session = EditorSession()
        # Tecla 06 (índice 5) -> usuário aperta '4' (0x34) no teclado principal
        session.select(5)
        act_4 = action_from_qt_event(0x34, 0, '4')
        session.assign(act_4)
        self.assertEqual(session.profile['layers'][0][5],
                         {'type': 'keyboard', 'steps': [{'key': '4', 'modifiers': []}]})

        # Tecla 09 (índice 8) -> usuário aperta Ctrl + C (0x43 + ControlModifier 0x04000000)
        session.select(8)
        act_copy = action_from_qt_event(0x43, 0x04000000, '\x03')
        session.assign(act_copy)
        self.assertEqual(session.profile['layers'][0][8],
                         {'type': 'keyboard', 'steps': [{'key': 'C', 'modifiers': ['Ctrl']}]})

        # Tecla 10 (índice 9) -> usuário aperta Ctrl + V (0x56 + ControlModifier 0x04000000)
        session.select(9)
        act_paste = action_from_qt_event(0x56, 0x04000000, '\x16')
        session.assign(act_paste)
        self.assertEqual(session.profile['layers'][0][9],
                         {'type': 'keyboard', 'steps': [{'key': 'V', 'modifiers': ['Ctrl']}]})

    def test_media_actions_work_on_any_regular_key_or_encoder(self):
        session = EditorSession()
        for key_idx, cmd in ((0, 'previous'), (1, 'play_pause'), (2, 'next'), (11, 'volume_up')):
            session.select(key_idx)
            action = {'type': 'media', 'command': cmd}
            session.assign(action)
            encoded = encode_record(session.action, key_idx + 1, 1)
            self.assertEqual(decode_record(encoded), action)

    def test_quick_actions_and_shortcut_presets_are_valid_hardware_records(self):
        for item in QUICK_ACTIONS:
            encoded = encode_record(item['action'], 1, 1)
            self.assertEqual(decode_record(encoded), item['action'])
        for title, steps in SHORTCUT_PRESETS:
            action = {'type': 'keyboard', 'steps': steps}
            encoded = encode_record(action, 1, 1)
            self.assertEqual(decode_record(encoded), action, title)

    def test_text_macro_conversion(self):
        action = action_from_text('1234', press_enter=True)
        self.assertEqual(len(action['steps']), 5)
        self.assertEqual(action['steps'][0], {'key': '1', 'modifiers': []})
        self.assertEqual(action['steps'][-1], {'key': 'Enter', 'modifiers': []})
        encoded = encode_record(action, 6, 1)
        self.assertEqual(decode_record(encoded), action)

    def test_custom_color_tones_map_to_valid_hardware_colors(self):
        self.assertEqual(len(COLOR_SHADES), 28)
        for shade in COLOR_SHADES:
            mapped = closest_hardware_color(shade['hex'])
            self.assertEqual(mapped, shade['hw'], f"Falha na tonalidade {shade['name']} ({shade['hex']})")
        # Estabilidade de matiz em qualquer saturação/brilho
        expected_by_hue = {0: 'red', 30: 'orange', 55: 'yellow', 120: 'green', 180: 'cyan', 220: 'blue', 280: 'purple'}
        for sat in (20, 50, 80, 100):
            for val in (30, 60, 100):
                for hue, expected_hw in expected_by_hue.items():
                    self.assertEqual(closest_hardware_color(hsv_to_hex(hue, sat, val)), expected_hw)
        h, s, v = hex_to_hsv('#eab308')
        self.assertTrue(40 <= h <= 50 and s >= 80 and v >= 80)

    def test_apply_led_all_layers_updates_all_three_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = ProductBackend()
            service = ConfigurationService(backend, directory)
            result = service.apply_led_all_layers(1, 'yellow')
            self.assertEqual(len(backend.leds), 3)
            for layer in (1, 2, 3):
                last = service.last_led(result['snapshot'], layer)
                self.assertIsNotNone(last)
                self.assertEqual(last['color'], 'yellow')
                self.assertEqual(last['mode'], 1)

    def test_encoder_presets_and_layer_templates_encode_valid_records(self):
        self.assertGreaterEqual(len(ENCODER_PRESETS), 9)
        for preset in ENCODER_PRESETS:
            self.assertEqual(len(preset['actions']), 3, preset['title'])
            for offset, act in enumerate(preset['actions']):
                for base in (13, 16):
                    encoded = encode_record(act, base + offset, 1)
                    self.assertEqual(decode_record(encoded), act, f"{preset['title']} pos {base + offset}")

        self.assertGreaterEqual(len(LAYER_TEMPLATES), 5)
        for tpl in LAYER_TEMPLATES:
            self.assertEqual(len(tpl['positions']), 18, tpl['title'])
            for pos, act in enumerate(tpl['positions'], start=1):
                encoded = encode_record(act, pos, 1)
                self.assertEqual(decode_record(encoded), act, f"{tpl['title']} pos {pos}")


if __name__ == '__main__':
    unittest.main()
