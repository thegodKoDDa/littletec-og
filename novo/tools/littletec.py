"""Ferramentas locais de análise. Não abre dispositivos nem envia comandos USB."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PIDS = [0x8842, 0x8840, 0x8830, 0x8831, 0x8832, 0x8833, 0x8850, 0x8851]


def verify(root=ROOT, original_root=None):
    original_root = original_root if original_root is not None else root.parent / 'original'
    manifest = json.loads((root / 'docs/original-manifest.json').read_text(encoding='utf-8-sig'))
    errors = []
    for entry in manifest:
        path = original_root / entry['path']
        if not path.is_file():
            errors.append(f"Ausente: {entry['path']}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            errors.append(f"Alterado: {entry['path']}")
    return len(manifest), errors


def devices(sysfs=Path('/sys/bus/hid/devices')):
    result = []
    if not sysfs.exists():
        return result
    for path in sorted(sysfs.iterdir()):
        event = path / 'uevent'
        if not event.is_file():
            continue
        attrs = dict(line.split('=', 1) for line in event.read_text().splitlines() if '=' in line)
        parts = attrs.get('HID_ID', '').split(':')
        if len(parts) != 3:
            continue
        try:
            vid, pid = int(parts[1], 16), int(parts[2], 16)
        except ValueError:
            continue
        if vid in (0x1189, 0x514C) and pid in PIDS:
            result.append({'vid': f'{vid:04x}', 'pid': f'{pid:04x}',
                           'name': attrs.get('HID_NAME', ''), 'sysfs': str(path),
                           'hidraw': [p.name for p in (path / 'hidraw').glob('hidraw*')]})
            descriptor = path / 'report_descriptor'
            try:
                result[-1]['descriptor'] = descriptor_summary(descriptor)
            except (OSError, ValueError) as error:
                result[-1]['descriptor_error'] = str(error)
    return result


def descriptor_summary(path):
    # Importação funciona tanto no CLI quanto nos testes carregados por spec.
    import importlib.util
    spec = importlib.util.spec_from_file_location('hid_descriptor', ROOT / 'tools/hid_descriptor.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raw = path.read_bytes()
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'length': len(raw),
            **module.summarize(raw)}


def analyze():
    for binary in ('objdump', 'strings'):
        if not shutil.which(binary):
            raise RuntimeError(f'Ferramenta ausente: {binary}; instale binutils no Ubuntu.')
    destination = ROOT / 'analysis'
    destination.mkdir(exist_ok=True)
    commands = [
        ('widget-disassembly.txt', ['objdump', '-dr', '-Mintel', str(ROOT.parent / 'original/widget.o')]),
        ('widget-symbols.txt', ['objdump', '-t', str(ROOT.parent / 'original/widget.o')]),
        ('widget-data.txt', ['objdump', '-s', '-j', '.data', str(ROOT.parent / 'original/widget.o')]),
        ('widget-strings.txt', ['strings', str(ROOT.parent / 'original/widget.o')]),
        ('exe-imports.txt', ['objdump', '-p', str(ROOT.parent / 'original/MINI_KEYBOARD.exe')]),
    ]
    for filename, command in commands:
        result = subprocess.run(command, check=True, capture_output=True)
        (destination / filename).write_bytes(result.stdout)
        print(f'Gerado: analysis/{filename}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['verify', 'doctor', 'analyze', 'descriptor'])
    parser.add_argument('--file', type=Path, help='Descritor HID binário para análise offline')
    args = parser.parse_args()
    if args.command == 'descriptor':
        if args.file is None:
            parser.error('descriptor exige --file')
        try:
            print(json.dumps(descriptor_summary(args.file), indent=2, ensure_ascii=False))
        except (OSError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
        return 0
    if args.command == 'verify':
        count, errors = verify()
        print(f'{count} arquivos originais verificados.')
        for error in errors:
            print(error)
        return bool(errors)
    if args.command == 'analyze':
        analyze()
        return 0
    found = devices()
    print(json.dumps({'python': sys.version.split()[0],
                      'kernel': platform.release(),
                      'wsl': 'microsoft' in platform.release().lower(),
                      'powershell': shutil.which('powershell.exe'),
                      'objdump': shutil.which('objdump'), 'strings': shutil.which('strings'),
                      'hidraw_nodes': [str(p) for p in Path('/dev').glob('hidraw*')],
                      'candidate_devices': found,
                      'note': 'Candidatos pela família VID/PID; compatibilidade ainda não validada.',
                      'usb_access': 'Nenhum dispositivo foi aberto; consulta somente a sysfs.'},
                     indent=2, ensure_ascii=False))
    if not found:
        print('Teclado não visível ao Linux. Isso pode ocorrer mesmo conectado ao Windows.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
