"""Diagnóstico de presença, sem abrir interfaces HID."""
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[2]


def collect_report():
    spec = importlib.util.spec_from_file_location('littletec_tools', ROOT / 'tools/littletec.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    report = {'environment': {'system': platform.system(), 'kernel': platform.release(),
                             'candidate_devices': tool.devices(),
                             'note': 'Enumeração apenas; nenhuma interface HID aberta.'},
              'windows': None, 'errors': []}
    powershell = shutil.which('powershell.exe') or shutil.which('powershell')
    if powershell:
        script = (ROOT / 'tools/diagnose_windows.ps1').read_text()
        try:
            options = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
            result = subprocess.run([powershell, '-NoProfile', '-NonInteractive', '-Command', script],
                                    capture_output=True, timeout=20, check=True, **options)
            report['windows'] = json.loads(result.stdout.decode('utf-8-sig'))
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            report['errors'].append(f'Falha na enumeração Windows: {error}')
    return report


def format_report(report):
    sections = ['AMBIENTE\n' + json.dumps(report['environment'], ensure_ascii=False, indent=2)]
    if report['windows'] is not None:
        sections.append('WINDOWS / ENUMERAÇÃO PNP\n' + json.dumps(report['windows'], ensure_ascii=False, indent=2))
    sections.extend(report['errors'])
    return '\n\n'.join(sections)


def collect():
    return format_report(collect_report())


def presence(report):
    """Resume somente presença PnP/sysfs; não declara compatibilidade validada."""
    windows = report.get('windows') or {}
    devices = windows.get('devices', [])
    if any('VID_1189&PID_8842&MI_00' in d.get('InstanceId', '').upper()
           and d.get('Status') == 'OK' and d.get('Class') == 'HIDClass' for d in devices):
        return '1189:8842 NO WINDOWS'
    if report.get('environment', {}).get('candidate_devices'):
        return 'FAMÍLIA HID NO LINUX'
    return 'FALHA NO DIAGNÓSTICO' if report.get('errors') else 'NÃO DETECTADO'
