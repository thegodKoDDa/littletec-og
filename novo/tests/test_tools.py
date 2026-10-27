import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('littletec', Path(__file__).resolve().parents[1] / 'tools/littletec.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ToolsTests(unittest.TestCase):
    def test_integrity_detects_tampering_and_missing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'docs').mkdir()
            (root / 'original.bin').write_bytes(b'original')
            (root / 'docs/original-manifest.json').write_text(json.dumps([
                {'path': 'original.bin', 'sha256': hashlib.sha256(b'original').hexdigest()}]))
            self.assertEqual(module.verify(root, original_root=root), (1, []))
            (root / 'original.bin').write_bytes(b'changed')
            self.assertIn('Alterado', module.verify(root, original_root=root)[1][0])
            (root / 'original.bin').unlink()
            self.assertIn('Ausente', module.verify(root, original_root=root)[1][0])

    def test_device_filter_and_hidraw_discovery(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, identifier in [('target', '0003:00001189:00008842'), ('other', '0003:00001234:00008842'), ('bad', 'invalid')]:
                node = root / name
                node.mkdir()
                (node / 'uevent').write_text(f'HID_ID={identifier}\nHID_NAME=Test\n')
            (root / 'target/hidraw/hidraw0').mkdir(parents=True)
            found = module.devices(root)
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]['hidraw'], ['hidraw0'])
            self.assertEqual(found[0]['vid'], '1189')


if __name__ == '__main__':
    unittest.main()
