"""Transporte FD restrito a teclas comuns. LED/encoders/atualização recusados."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

from . import device_service
from .identity import validate_capabilities
from .protocol import COMMIT_PACKET, decode_record


def receipt_path():
    if getattr(sys, 'frozen', False) or sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'LittleTec/write-validation.json'
    return device_service.capture_directory() / 'write-validation.json'


def validation_for(snapshot):
    try:
        receipt = json.loads(receipt_path().read_text(encoding='utf-8'))
        path = snapshot['manifest']['capabilities']['devices'][0]['path']
        return (receipt.get('complete') is True and receipt.get('restoration_verified') is True
                and receipt.get('device_path', '').lower() == path.lower()
                and receipt.get('identity') == snapshot['identity'])
    except (OSError, ValueError, KeyError, IndexError):
        return False


class TrialBackend:
    def __init__(self):
        self.allowed = set()
        self.path = None

    def read(self):
        snapshot = device_service.read_keyboard()
        current = snapshot['manifest']['capabilities']['devices'][0]['path']
        if self.path is not None and self.path.lower() != current.lower():
            raise RuntimeError('O dispositivo mudou durante o ensaio.')
        self.path = current
        return snapshot

    def allow_packets(self, packets):
        self.allowed = set(packets)

    def send(self, packets):
        if not self.path or not packets or any(p not in self.allowed for p in packets):
            raise ValueError('Pacote fora da lista exata permitida para o ensaio.')
        send_checked(packets, self.path)


def send_checked(packets, expected_path):
    # Nenhum transporte genérico: só FD de posições 1..12 em camadas 1..3.
    for packet in packets:
        if packet == COMMIT_PACKET:
            continue
        if len(packet) != 65 or packet[:2] != b'\x03\xfd' or any(packet[51:]):
            raise ValueError('Pacote fora do formato FD de tecla.')
        record = packet[1:51]
        if not 1 <= record[1] <= 12 or not 1 <= record[2] <= 3 or record[3] not in (1, 2, 3, 5):
            raise ValueError('Envio limitado a teclas comuns; encoder/LED não validado para gravação.')
        if decode_record(record)['type'] == 'raw':
            raise ValueError('Tipo/campos não interpretados recusados no transporte.')
    if sys.platform != 'win32':
        raise RuntimeError('Envio disponível apenas no Windows.')
    if not getattr(sys, 'frozen', False):
        sys.path.insert(0, str(device_service.ROOT / '.devtools/windows'))
    import hid
    spec = importlib.util.spec_from_file_location('littletec_write_caps', device_service.ROOT / 'tools/hid_caps_windows.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata = module.collect()
    if len(metadata['devices']) != 1:
        raise RuntimeError('Interface de configuração ausente/ambígua.')
    caps = metadata['devices'][0]
    validate_capabilities(caps)
    if caps['path'].lower() != expected_path.lower():
        raise RuntimeError('Caminho HID mudou antes do envio.')
    paths = [d['path'] for d in hid.enumerate(0x1189, 0x8842)
             if d['path'].decode().lower() == expected_path.lower() and d['interface_number'] == 0
             and d['usage_page'] == 0xff00 and d['usage'] == 1]
    if len(paths) != 1:
        raise RuntimeError('Enumeração não corresponde à interface validada.')
    device = hid.device()
    try:
        device.open_path(paths[0])
        deadline = time.monotonic() + 15
        for packet in packets:
            if time.monotonic() >= deadline:
                raise TimeoutError('Prazo total do envio excedido.')
            if device.write(packet) != 65:
                raise OSError('Escrita HID incompleta.')
            if packet == COMMIT_PACKET:
                time.sleep(0.2)  # Mesma espera observada no cliente original.
    finally:
        device.close()


def save_validation(report):
    report = dict(report, collected_at_utc=datetime.now(timezone.utc).isoformat())
    path = receipt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def _packets(changes, restore=False):
    packets = []
    for layer in (1, 2, 3):
        group = [change for change in changes if change['layer'] == layer]
        for change in group:
            packets.append(bytes.fromhex(change['restore_packet_hex' if restore else 'packet_hex']))
        if group:
            packets.append(COMMIT_PACKET)
    return packets


def _verify_change(before, after, changes):
    from .write_trial import records
    old, new = records(before), records(after)
    expected = {(c['layer'] - 1, c['record_index']): bytes.fromhex(c['after_hex']) for c in changes}
    for layer in range(3):
        for index in range(1, 25):
            if (layer, index) in expected:
                if decode_record(new[layer][index]) != decode_record(expected[(layer, index)]):
                    raise RuntimeError(f'Releitura divergente na camada {layer + 1}, tecla {index}.')
            elif new[layer][index] != old[layer][index]:
                raise RuntimeError(f'Alteração não prevista na camada {layer + 1}, registro {index}.')


def apply_profile(snapshot, profile, backend=None):
    """Cópia recente, pré-condição, envio restrito, releitura e retorno em falha."""
    from .protocol import build_plan
    from .write_trial import signature
    if not validation_for(snapshot):
        raise PermissionError('Ensaio de gravação/restauração não validado para este dispositivo neste Windows.')
    plan = build_plan(snapshot['layers'], snapshot['identity'], profile)
    if any(c['record_index'] > 12 for c in plan['changes']):
        raise ValueError('Há encoders alterados no perfil. A gravação deles ainda não foi validada; mantenha o envio nas teclas 1–12.')
    if any(decode_record(bytes.fromhex(c['before_hex']))['type'] == 'raw' for c in plan['changes']):
        raise ValueError('Recusada substituição de registro com campos não interpretados.')
    backend = backend or TrialBackend()
    before = backend.read()  # Esta leitura salva uma nova cópia bruta antes de qualquer envio.
    source_path = snapshot['manifest']['capabilities']['devices'][0]['path']
    current_path = before['manifest']['capabilities']['devices'][0]['path']
    if (source_path.lower() != current_path.lower()
            or before['identity'] != snapshot['identity']):
        raise RuntimeError('O dispositivo mudou desde a leitura carregada. Leia o teclado novamente antes de aplicar.')
    if not validation_for(before):
        raise PermissionError('Validação de restauração indisponível para a leitura atual; envio recusado.')
    if signature(before) != signature(snapshot):
        raise RuntimeError('A configuração mudou desde a leitura carregada. Leia o teclado novamente antes de aplicar.')
    changes = plan['changes']
    if not changes:
        return before
    forward, backward = _packets(changes), _packets(changes, restore=True)
    backend.allow_packets(set(forward + backward))
    try:
        backend.send(forward)
        after = backend.read()
        _verify_change(before, after, changes)
        return after
    except Exception as error:
        try:
            backend.send(backward)
            restored = backend.read()
            if signature(restored) != signature(before):
                raise RuntimeError('Dados restaurados divergem da cópia anterior.')
        except Exception as restore_error:
            save_validation({'complete': False, 'restoration_verified': False, 'error': str(error),
                             'restoration_error': str(restore_error), 'backup': before['folder']})
            raise RuntimeError(f'Falha no envio e no retorno automático: {restore_error}. Cópia preservada em {before["folder"]}.') from error
        raise RuntimeError(f'Envio não confirmado; a configuração anterior foi restaurada e relida. Detalhe: {error}') from error
