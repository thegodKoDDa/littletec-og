"""Build do Studio Qt integrado. Entry point em src/; sem cópias manuais de módulos."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import distribution

ROOT = Path(__file__).resolve().parents[1]


def check_icu(folder):
    bundled = folder / '_internal/icuuc.dll'
    if not bundled.exists():
        return
    import pefile
    def exports(path):
        with pefile.PE(str(path)) as binary:
            return {symbol.name for symbol in binary.DIRECTORY_ENTRY_EXPORT.symbols}
    if b'ucnv_open' not in exports(bundled):
        system = Path(os.environ['SystemRoot']) / 'System32/icuuc.dll'
        if not system.is_file() or b'ucnv_open' not in exports(system):
            raise RuntimeError('ICU compatível não disponível; distribuição não liberada.')
        bundled.unlink()
        print('ICU incompatível coletada do PATH removida; usando ICU do Windows validada.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true', help='Confere a ICU do pacote já compilado, sem modificar módulos Python.')
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise SystemExit('Use o ambiente .venv-qt-windows no Windows.')
    target = ROOT / 'dist'
    if args.validate_only:
        if not (target / 'LittleTec.exe').is_file() or not (target / '_internal').is_dir():
            raise RuntimeError('Pacote integrado ausente em dist/.')
        check_icu(target)
        print('Pós-build do pacote compilado validado.')
        return
    with tempfile.TemporaryDirectory(prefix='littletec-product-build-') as temp:
        temp_path = Path(temp)
        staging = temp_path / 'dist'
        package = staging / 'LittleTec'
        license_data = []
        for package_name in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6', 'hidapi'):
            dist = distribution(package_name)
            for file in dist.files or []:
                if '.dist-info/licenses/' in str(file).replace('\\', '/'):
                    license_data.extend(['--add-data', f'{dist.locate_file(file)};licenses/{package_name}'])
        command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
                   '--onedir', '--windowed', '--name', 'LittleTec',
                   '--paths', str(ROOT / 'src'),
                   '--add-data', f'{ROOT / "src/littletec/ui_qt/qml"};littletec/ui_qt/qml',
                   '--add-data', f'{ROOT / "tools/hid_caps_windows.py"};tools',
                   '--add-data', f'{ROOT / "tools/hid_descriptor.py"};tools',
                   '--add-data', f'{ROOT / "tools/littletec.py"};tools',
                   '--add-data', f'{ROOT / "tools/diagnose_windows.ps1"};tools',
                   '--add-data', f'{ROOT / "licenses"};licenses',
                   '--hidden-import', 'hid', '--hidden-import', 'ctypes.wintypes',
                   '--hidden-import', 'PySide6.QtQuick', '--hidden-import', 'PySide6.QtQuickControls2',
                   '--hidden-import', 'littletec.configuration_service',
                   '--exclude-module', 'tkinter', '--exclude-module', 'PySide6.QtWebEngineCore',
                   '--exclude-module', 'PySide6.QtWebEngineQuick', '--exclude-module', 'PySide6.QtWebEngineWidgets',
                   '--exclude-module', 'PySide6.QtPdf', '--exclude-module', 'PySide6.QtPdfWidgets',
                   '--distpath', str(staging),
                   '--workpath', str(temp_path / 'work'), '--specpath', temp,
                   *license_data, str(ROOT / 'src/desktop_qt.py')]
        subprocess.run(command, check=True)
        check_icu(package)
        promote(package)
    print(f'Pacote integrado instalado em: {target / "LittleTec.exe"}')


def promote(package):
    target = ROOT / 'dist'
    target.mkdir(parents=True, exist_ok=True)
    if (target / '_internal').exists():
        shutil.rmtree(target / '_internal')
    shutil.copytree(package / '_internal', target / '_internal')
    shutil.copy2(package / 'LittleTec.exe', target / 'LittleTec.exe')
    print('Versão atual: dist/LittleTec.exe; manter dist/_internal junto.')

if __name__ == '__main__':
    main()
