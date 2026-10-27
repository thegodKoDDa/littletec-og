"""Executa pacote Qt copiado para pasta isolada. Padrão offline; --read-usb opt-in.

Nunca aciona aplicação nem ensaios físicos. Não depende do código-fonte no runtime.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--read-usb', action='store_true')
    parser.add_argument('--promoted', action='store_true', help='Compatibilidade; dist/ já é o único pacote.')
    args = parser.parse_args()
    package = ROOT / 'dist'
    destination = ROOT / 'captures'
    with tempfile.TemporaryDirectory(prefix='littletec-qt-isolated-') as temp:
        isolated = Path(temp)
        shutil.copy2(package / 'LittleTec.exe', isolated / 'LittleTec.exe')
        shutil.copytree(package / '_internal', isolated / '_internal')
        result = destination / ('qt-release-usb.json' if args.read_usb else 'qt-release-offline.json')
        image = result.with_suffix('.png')
        log = result.with_suffix('.log')
        command = [str(isolated / 'LittleTec.exe'), '--page', 'Iluminação', '--screenshot', str(image),
                   '--result', str(result), '--read-usb' if args.read_usb else '--offline']
        with log.open('w') as output:
            completed = subprocess.run(command, cwd=isolated, stdout=output, stderr=subprocess.STDOUT, timeout=60)
        if completed.returncode != 0 or not result.exists():
            raise RuntimeError(f'Executável isolado falhou ({completed.returncode}); veja {log}')
        data = json.loads(result.read_text())
        assert data['ok'] and not data['qml_errors'], data
        if args.read_usb:
            assert data['state']['connected'] and data['state']['backup'], data
        print(json.dumps({'isolated': True, 'ok': data['ok'], 'read_usb': args.read_usb,
                          'backup': data['state']['backup'], 'result': str(result)}), flush=True)

if __name__ == '__main__':
    main()
