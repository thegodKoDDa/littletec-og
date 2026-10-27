"""Integra identificação/leitura validadas ao aplicativo. Nenhuma API de gravação."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

from .config_read import OBSERVED_READ_REQUESTS, read_configuration
from .identity import OBSERVED_REQUEST, query, validate_capabilities
from .protocol import profile_from_layers, normalize_encoder_headers

ROOT = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[2]


def capture_directory():
    if getattr(sys, 'frozen', False):
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'LittleTec' / 'captures'
    return ROOT / 'captures'


def load_backup(folder):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('complete') is not True:
        raise ValueError('Cópia bruta incompleta.')
    files = manifest.get('files')
    if not isinstance(files, list) or len(files) != 3:
        raise ValueError('Cópia deve conter três camadas.')
    layers = []
    for layer, entry in enumerate(files, 1):
        name = f'layer-{layer}.bin'
        if entry.get('path') != name:
            raise ValueError('Nome de camada inesperado no manifesto.')
        data = (folder / name).read_bytes()
        if len(data) != 1560 or entry.get('size') != len(data) or hashlib.sha256(data).hexdigest() != entry.get('sha256'):
            raise ValueError(f'Integridade inválida: {name}')
        layers.append([data[offset:offset + 65] for offset in range(0, len(data), 65)])
    identity = manifest.get('identity', {})
    raw_layers = layers
    if manifest.get('encoder_header_policy') == 'stored-id-in-fixed-trios-v1':
        layers = normalize_encoder_headers(layers)
    profile = profile_from_layers(layers, identity)
    return {'folder': str(folder), 'manifest': manifest, 'identity': identity,
            'layers': layers, 'raw_layers': raw_layers, 'profile': profile}


def read_keyboard(destination_root=None):
    if sys.platform != 'win32':
        raise RuntimeError('A leitura USB está disponível no .exe Windows. O WSL não tem acesso direto ao teclado.')
    if not getattr(sys, 'frozen', False):
        sys.path.insert(0, str(ROOT / '.devtools/windows'))
    try:
        import hid
    except ImportError as error:
        raise RuntimeError('HIDAPI ausente. Use o executável Windows distribuído.') from error
    spec = importlib.util.spec_from_file_location('littletec_hid_caps', ROOT / 'tools/hid_caps_windows.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    metadata = tool.collect()
    if len(metadata['devices']) != 1:
        raise RuntimeError('Conecte somente um teclado 1189:8842 para ler a configuração.')
    caps = metadata['devices'][0]
    validate_capabilities(caps)
    candidates = [d for d in hid.enumerate(0x1189, 0x8842)
                  if d['path'].decode().lower() == caps['path'].lower()
                  and d['interface_number'] == 0 and d['usage_page'] == 0xff00 and d['usage'] == 1]
    if len(candidates) != 1:
        raise RuntimeError('Interface HIDAPI não corresponde às capacidades verificadas.')
    def opened():
        device = hid.device()
        try:
            device.open_path(candidates[0]['path'])
        except Exception:
            device.close()
            raise
        return device
    raw_identity, identity = query(opened(), caps, OBSERVED_REQUEST)
    if (identity['key_count'], identity['encoder_count'], identity['variant']) != (12, 2, 0):
        raise RuntimeError('Esta versão é exclusiva do modelo 12 teclas + 2 encoders, variante 0.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    root = Path(destination_root) if destination_root else capture_directory()
    folder = root / ('raw-configuration-' + stamp)
    folder.mkdir(parents=True)
    manifest = {'schema': 1, 'collected_at_utc': datetime.now(timezone.utc).isoformat(),
                'complete': False, 'restoration_validated': False, 'identity': identity,
                'identity_hex': raw_identity.hex(), 'capabilities': metadata,
                'requests_hex': [r.hex() for r in OBSERVED_READ_REQUESTS],
                'scope': '72 relatórios observados. Iluminação/cobertura total não comprovadas.',
                'encoder_header_policy': 'stored-id-in-fixed-trios-v1'}
    started = time.monotonic()
    try:
        with (folder / 'received.jsonl').open('x', encoding='utf-8') as log:
            def on_packet(layer, arrival, raw):
                log.write(json.dumps({'layer': layer, 'arrival': arrival, 'length': len(raw), 'hex': raw.hex()}) + '\n')
                log.flush()
            layers = read_configuration(opened(), caps, on_packet=on_packet, allow_encoder_aliases=True)
        manifest['files'] = []
        for layer, packets in enumerate(layers, 1):
            data = b''.join(packets)
            name = f'layer-{layer}.bin'
            (folder / name).write_bytes(data)
            manifest['files'].append({'path': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                      'record_indexes': [p[2] for p in packets]})
        manifest['complete'] = True
    except Exception as error:
        manifest['error'] = str(error)
        raise
    finally:
        manifest['elapsed_ms'] = round((time.monotonic() - started) * 1000, 2)
        (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = load_backup(folder)
    (folder / 'decoded-profile.json').write_text(json.dumps(result['profile'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result
