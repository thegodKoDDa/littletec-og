"""Casos de uso do Studio Qt; verificações automáticas, sem política de ensaios.

O controlador serializa este serviço. GUI e recibos experimentais não participam.
"""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import time

from . import device_service, lighting_service
from .identity import OBSERVED_REQUEST, query, validate_capabilities
from .protocol import (COMMIT_PACKET, PHYSICAL_RECORDS, build_plan, decode_record,
                       packet_for_record, index_layers)
from .write_service import _packets, _verify_change
from .write_trial import signature


def validate_configuration_packets(packets):
    if not packets:
        raise ValueError('Nenhum pacote para enviar.')
    pending = False
    for packet in packets:
        if packet == COMMIT_PACKET:
            if not pending:
                raise ValueError('Finalização sem registros.')
            pending = False
            continue
        if (not isinstance(packet, bytes) or len(packet) != 65 or packet[:2] != b'\x03\xfd'
                or any(packet[51:]) or packet[2] not in PHYSICAL_RECORDS
                or not 1 <= packet[3] <= 3):
            raise ValueError('Pacote fora das posições físicas do modelo 12+2.')
        if decode_record(packet[1:51])['type'] == 'raw':
            raise ValueError('Campos não interpretados recusados para escrita.')
        pending = True
    if pending:
        raise ValueError('Falta finalização dos registros.')


def send_configuration(packets, snapshot):
    validate_configuration_packets(packets)
    if sys.platform != 'win32':
        raise RuntimeError('Use o aplicativo Windows para comunicar com o teclado.')
    import hid
    if hid.version_str() != '0.15.0':
        raise RuntimeError('HIDAPI 0.15.0 é necessária para o timeout de escrita validado.')
    spec = importlib.util.spec_from_file_location('studio_caps', device_service.ROOT / 'tools/hid_caps_windows.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata = module.collect()
    if len(metadata['devices']) != 1:
        raise RuntimeError('Conecte somente um teclado LittleTec 12+2.')
    caps = metadata['devices'][0]
    validate_capabilities(caps)
    expected = lighting_service.device_path(snapshot)
    if caps['path'].lower() != expected.lower():
        raise RuntimeError('A interface do teclado mudou; reconecte pela leitura.')
    candidates = [d for d in hid.enumerate(0x1189, 0x8842)
                  if d['path'].decode().lower() == expected.lower() and d['interface_number'] == 0
                  and d['usage_page'] == 0xff00 and d['usage'] == 1]
    if len(candidates) != 1:
        raise RuntimeError('Enumeração HID incompatível com as capacidades.')
    def opened():
        handle = hid.device()
        try:
            handle.open_path(candidates[0]['path'])
        except Exception:
            handle.close()
            raise
        return handle
    _, identity = query(opened(), caps, OBSERVED_REQUEST)
    if identity != snapshot['identity']:
        raise RuntimeError('A identidade do teclado mudou antes da aplicação.')
    handle = opened()
    try:
        deadline = time.monotonic() + 15
        for packet in packets:
            if time.monotonic() >= deadline:
                raise TimeoutError('O envio excedeu seu prazo; iniciando retorno.')
            if handle.write(packet) != 65:
                raise OSError('Escrita HID incompleta.')
            if packet == COMMIT_PACKET:
                time.sleep(0.2)
    finally:
        handle.close()


class WindowsBackend:
    def read(self):
        return device_service.read_keyboard()

    def send_keys(self, packets, snapshot):
        send_configuration(packets, snapshot)

    def send_led(self, packet, snapshot):
        lighting_service.send_lighting(packet, snapshot)


class ConfigurationService:
    def __init__(self, backend=None, data_root=None):
        self.backend = backend or WindowsBackend()
        self.root = Path(data_root) if data_root else device_service.capture_directory()

    def read(self):
        return self.backend.read()

    def _journal(self, kind, value):
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        path = self.root / f'{kind}-{stamp}.json'
        value.update(collected_at_utc=datetime.now(timezone.utc).isoformat(), journal=str(path))
        lighting_service.write_json(path, value)
        return path

    def last_led(self, snapshot, layer):
        try:
            value = json.loads((self.root / f'last-led-layer-{layer}.json').read_text(encoding='utf-8'))
            if (value.get('device_path', '').lower() != lighting_service.device_path(snapshot).lower()
                    or value.get('identity') != snapshot['identity'] or value.get('status') != 'sent'):
                return None
            packet = bytes.fromhex(value['packet_hex'])
            spec = lighting_service.parse_lighting_packet(packet)
            return dict(value, **spec) if spec['layer'] == layer else None
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return None

    def apply_led(self, mode, color, layer, snapshot=None):
        packet = lighting_service.lighting_packet(mode, color, layer)
        before = self.backend.read()  # Cópia bruta recente automática.
        if snapshot:
            lighting_service.same_device(snapshot, before)
        previous = self.last_led(before, layer)
        report = {'operation': 'lighting', 'complete': False, 'led_readback': False,
                  'source_backup': before['folder'], 'packet_hex': packet.hex(),
                  'commit_packet_hex': COMMIT_PACKET.hex(), 'previous_sent': previous,
                  'device_path': lighting_service.device_path(before), 'identity': before['identity']}
        journal = self._journal('apply-led', report)
        state_file = self.root / f'last-led-layer-{layer}.json'
        lighting_service.write_json(state_file, dict(report, status='pending'))
        try:
            self.backend.send_led(packet, before)
            after = self.backend.read()
            lighting_service.unchanged_keys(before, after)
            sent = {'status': 'sent', 'packet_hex': packet.hex(), 'device_path': report['device_path'],
                    'identity': before['identity'], 'journal': str(journal), 'led_readback': False}
            lighting_service.write_json(state_file, sent)
            report.update(complete=True, keys_unchanged=True, after_backup=after['folder'])
            lighting_service.write_json(journal, report)
            return {'snapshot': after, 'lighting': dict(sent, mode=mode, color=color, layer=layer),
                    'message': f'Iluminação enviada à camada {layer}.', 'journal': str(journal)}
        except Exception as error:
            report['error'] = str(error)
            if previous:
                try:
                    self.backend.send_led(bytes.fromhex(previous['packet_hex']), before)
                    lighting_service.unchanged_keys(before, self.backend.read())
                    report['previous_command_resent'] = True
                    # Reenvio não prova aparência/readback: manter estado desconhecido após falha.
                except Exception as restore_error:
                    report['return_error'] = str(restore_error)
            lighting_service.write_json(state_file, dict(report, status='unknown'))
            lighting_service.write_json(journal, report)
            raise RuntimeError(f'Não foi possível concluir a iluminação: {error}. Detalhes: {journal}') from error

    def apply_led_all_layers(self, mode, color, snapshot=None):
        packets = {layer: lighting_service.lighting_packet(mode, color, layer) for layer in (1, 2, 3)}
        before = self.backend.read()
        if snapshot:
            lighting_service.same_device(snapshot, before)
        report = {'operation': 'lighting_all', 'complete': False, 'led_readback': False,
                  'source_backup': before['folder'],
                  'packets_hex': {str(k): v.hex() for k, v in packets.items()},
                  'commit_packet_hex': COMMIT_PACKET.hex(),
                  'device_path': lighting_service.device_path(before), 'identity': before['identity']}
        journal = self._journal('apply-led-all', report)
        try:
            for layer in (1, 2, 3):
                self.backend.send_led(packets[layer], before)
            after = self.backend.read()
            lighting_service.unchanged_keys(before, after)
            results = []
            for layer in (1, 2, 3):
                state_file = self.root / f'last-led-layer-{layer}.json'
                sent = {'status': 'sent', 'packet_hex': packets[layer].hex(),
                        'device_path': report['device_path'], 'identity': before['identity'],
                        'journal': str(journal), 'led_readback': False}
                lighting_service.write_json(state_file, sent)
                results.append(dict(sent, mode=mode, color=color, layer=layer))
            report.update(complete=True, keys_unchanged=True, after_backup=after['folder'])
            lighting_service.write_json(journal, report)
            return {'snapshot': after, 'lighting_all': results,
                    'message': 'Iluminação aplicada nas 3 camadas do teclado.', 'journal': str(journal)}
        except Exception as error:
            report['error'] = str(error)
            lighting_service.write_json(journal, report)
            raise RuntimeError(f'Não foi possível aplicar iluminação nas 3 camadas: {error}. Detalhes: {journal}') from error

    def apply_keys(self, snapshot, profile):
        if snapshot is None:
            raise ValueError('Leia o teclado antes de aplicar o mapeamento.')
        plan = build_plan(snapshot['layers'], snapshot['identity'], profile)
        for change in plan['changes']:
            if decode_record(bytes.fromhex(change['before_hex']))['type'] == 'raw':
                raise ValueError('Não é possível substituir uma ação com campos ainda não interpretados.')
        before = self.backend.read()
        lighting_service.unchanged_keys(snapshot, before)
        changes = plan['changes']
        if not changes:
            return {'snapshot': before, 'message': 'O mapeamento já está atualizado.'}
        forward, backward = _packets(changes), _packets(changes, restore=True)
        validate_configuration_packets(forward)
        validate_configuration_packets(backward)
        report = {'operation': 'mapping', 'complete': False, 'source_backup': before['folder'], 'plan': plan}
        journal = self._journal('apply-mapping', report)
        try:
            self.backend.send_keys(forward, before)
            after = self.backend.read()
            lighting_service.same_device(before, after)
            _verify_change(before, after, changes)
            report.update(complete=True, after_backup=after['folder'])
            lighting_service.write_json(journal, report)
            return {'snapshot': after, 'message': f"{len(changes)} posições aplicadas e relidas.", 'journal': str(journal)}
        except Exception as error:
            report['error'] = str(error)
            try:
                self.backend.send_keys(backward, before)
                restored = self.backend.read()
                lighting_service.unchanged_keys(before, restored)
                report['restored'] = True
            except Exception as restore_error:
                report['return_error'] = str(restore_error)
            lighting_service.write_json(journal, report)
            suffix = 'Configuração anterior restaurada e relida.' if report.get('restored') else 'Retorno não confirmado; cópia preservada em ' + before['folder']
            raise RuntimeError(f'Aplicação não concluída: {error}. {suffix} Detalhes: {journal}') from error
