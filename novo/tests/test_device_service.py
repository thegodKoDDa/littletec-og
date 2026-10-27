import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.device_service import load_backup
from test_protocol import IDENTITY, sample_layers


class BackupTests(unittest.TestCase):
    def test_encoder_alias_normalization_keeps_raw_capture_and_hashes_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            manifest = self.fixture(folder)
            # Reproduz a ordem real observada e o cabeçalho persistido após FD16.
            for number in (1, 2, 3):
                packets = sample_layers()[number-1]
                by_id = {p[2]: p for p in packets}
                packets = [by_id[i] for i in (*range(1,16),18,17,16,21,20,19,24,23,22)]
                changed = bytearray(packets[15]); changed[2] = 16; packets[15] = bytes(changed)
                data = b''.join(packets)
                (folder / f'layer-{number}.bin').write_bytes(data)
                manifest['files'][number-1]['sha256'] = hashlib.sha256(data).hexdigest()
            manifest['encoder_header_policy'] = 'stored-id-in-fixed-trios-v1'
            (folder / 'manifest.json').write_text(json.dumps(manifest))
            result = load_backup(folder)
            self.assertEqual(result['raw_layers'][0][15][2], 16)
            self.assertEqual(result['layers'][0][15][2], 18)
            self.assertEqual(result['raw_layers'][0][15][3:], result['layers'][0][15][3:])
            self.assertEqual(result['profile']['layers'][0][12]['command'], 'volume_down')

    def fixture(self, folder):
        files = []
        for index, layer in enumerate(sample_layers(), 1):
            data = b''.join(layer)
            name = f'layer-{index}.bin'
            (folder / name).write_bytes(data)
            files.append({'path': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        manifest = {'complete': True, 'identity': IDENTITY, 'files': files, 'restoration_validated': False}
        (folder / 'manifest.json').write_text(json.dumps(manifest))
        return manifest

    def test_loads_validated_backup_and_decodes_real_positions(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder)
            loaded = load_backup(folder)
            self.assertEqual(loaded['profile']['layers'][0][12]['command'], 'volume_down')
            self.assertFalse(loaded['manifest']['restoration_validated'])

    def test_tampering_incomplete_and_path_traversal_are_refused(self):
        for mode in ('tamper', 'incomplete', 'path'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                manifest = self.fixture(folder)
                if mode == 'tamper':
                    (folder / 'layer-1.bin').write_bytes(bytes(1560))
                elif mode == 'incomplete':
                    manifest['complete'] = False
                else:
                    manifest['files'][0]['path'] = '../outside.bin'
                (folder / 'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    load_backup(folder)
