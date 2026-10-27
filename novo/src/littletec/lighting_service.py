"""LED compacto: envio isolado e confirmação visual; não existe readback de LED.

Origem: docs/LED_INVESTIGACAO.md e captura nativa FE B0 com saída simulada.
O transporte de teclas permanece separado e continua recusando FE.
"""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import time

from . import device_service
from .catalog import COLORS
from .identity import OBSERVED_REQUEST, query, validate_capabilities
from .protocol import COMMIT_PACKET, encode_lighting, packet_for_record
from .write_trial import signature
from .write_service import receipt_path as key_receipt_path


def lighting_packet(mode, color, layer):
    if type(layer) is not int:
        raise ValueError('Camada deve ser inteira.')
    return packet_for_record(encode_lighting(mode, color, layer))


def parse_lighting_packet(packet):
    if not isinstance(packet, bytes) or len(packet) != 65:
        raise ValueError('Pacote LED deve ter exatamente 65 bytes.')
    if packet[:3] != b'\x03\xfe\xb0' or not 1 <= packet[3] <= 3:
        raise ValueError('Somente FE B0 nas camadas 1–3 é permitido.')
    mode, color_number = packet[12] & 15, packet[12] >> 4
    if mode > 5 or not 1 <= color_number <= len(COLORS):
        raise ValueError('Cor/modo fora do formato LED recuperado.')
    color = list(COLORS)[color_number - 1]
    if packet != lighting_packet(mode, color, packet[3]):
        raise ValueError('Campos extras não autorizados no pacote LED.')
    return {'mode': mode, 'color': color, 'layer': packet[3]}


def device_path(snapshot):
    return snapshot['manifest']['capabilities']['devices'][0]['path']


def same_device(before, after):
    if (device_path(before).lower() != device_path(after).lower()
            or before['identity'] != after['identity']):
        raise RuntimeError('Identidade/caminho HID mudou durante a operação LED.')


def unchanged_keys(before, after):
    same_device(before, after)
    if signature(before) != signature(after):
        raise RuntimeError('Os 72 registros de teclas/encoders divergiram após o envio LED.')


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def send_lighting(packet, expected_snapshot):
    """Só um registro LED canônico + finalização; revalida antes de comunicar."""
    parse_lighting_packet(packet)
    if sys.platform != 'win32':
        raise RuntimeError('Envio LED disponível somente no Windows.')
    if not getattr(sys, 'frozen', False):
        sys.path.insert(0, str(device_service.ROOT / '.devtools/windows'))
    import hid
    # HIDAPI Windows 0.15 tem timeout de escrita padrão de 1000 ms. Não usar uma
    # implementação desconhecida que possa bloquear sem prazo.
    if hid.version_str() != '0.15.0':
        raise RuntimeError('Envio LED requer HIDAPI nativa 0.15.0 validada.')
    spec = importlib.util.spec_from_file_location(
        'littletec_led_caps', device_service.ROOT / 'tools/hid_caps_windows.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata = module.collect()
    if len(metadata['devices']) != 1:
        raise RuntimeError('Interface ausente/ambígua.')
    caps = metadata['devices'][0]
    validate_capabilities(caps)
    path = device_path(expected_snapshot)
    if caps['path'].lower() != path.lower():
        raise RuntimeError('Caminho HID mudou antes do envio LED.')
    candidates = [d for d in hid.enumerate(0x1189, 0x8842)
                  if d['path'].decode().lower() == path.lower() and d['interface_number'] == 0
                  and d['usage_page'] == 0xff00 and d['usage'] == 1]
    if len(candidates) != 1:
        raise RuntimeError('Enumeração não corresponde às capacidades validadas.')
    def opened():
        handle = hid.device()
        try:
            handle.open_path(candidates[0]['path'])
        except Exception:
            handle.close()
            raise
        return handle
    _, identity = query(opened(), caps, OBSERVED_REQUEST, timeout_ms=1000)
    if identity != expected_snapshot['identity']:
        raise RuntimeError('Identificação mudou antes do envio LED.')
    handle = opened()
    try:
        for outgoing in (packet, COMMIT_PACKET):
            if handle.write(outgoing) != 65:
                raise OSError('Escrita LED incompleta; estado visual precisa de conferência.')
        time.sleep(0.2)
    finally:
        handle.close()


class LedBackend:
    def __init__(self):
        self.snapshot = None

    def read(self):
        result = device_service.read_keyboard()
        if self.snapshot is not None:
            same_device(self.snapshot, result)
        self.snapshot = result
        return result

    def send(self, packet):
        if self.snapshot is None:
            raise RuntimeError('Faça uma cópia bruta antes de enviar LED.')
        send_lighting(packet, self.snapshot)


def trial_plan(layer=1):
    baseline = lighting_packet(1, 'cyan', layer)
    test = lighting_packet(1, 'red', layer)
    return {'format': 'littletec-led-trial', 'version': 1, 'layer': layer,
            'initial_led_read': False, 'initial_state_restorable': False,
            'baseline': parse_lighting_packet(baseline), 'test': parse_lighting_packet(test),
            'baseline_packet_hex': baseline.hex(), 'test_packet_hex': test.hex(),
            'restore_packet_hex': baseline.hex(), 'commit_packet_hex': COMMIT_PACKET.hex(),
            'scope': 'Estabelecer ciano estático, testar vermelho e voltar ao ciano, somente nesta camada.',
            'limitation': 'Ciano é uma referência definida e confirmada visualmente, não uma leitura do LED anterior.'}


def state_path(layer):
    lighting_packet(1, 'cyan', layer)  # Recusa também bool, float e índices inválidos.
    return key_receipt_path().parent / f'led-validation-layer-{layer}.json'


def record_validated_trial(report):
    if (report.get('format') != 'littletec-led-trial' or report.get('complete') is not True
            or report.get('approved_replace_unread_led') is not True
            or not all(report.get(field) is True for field in (
                'baseline_visual_verified', 'test_visual_verified',
                'restoration_visual_verified', 'keys_unchanged'))
            or report.get('error') or report.get('restoration_error')):
        raise ValueError('Ensaio visual incompleto; envio normal de LED continua bloqueado.')
    packet = bytes.fromhex(report['restore_packet_hex'])
    if packet != lighting_packet(1, 'cyan', report['layer']):
        raise ValueError('Referência de retorno divergente do ensaio.')
    state = {'format': 'littletec-led-validation', 'version': 1,
             'identity': report['identity'], 'device_path': report['device_path'],
             'layer': report['layer'], 'current_packet_hex': packet.hex(),
             'visual_confirmed': True, 'restoration_trial_verified': True,
             'led_readback': False, 'source_backup': report['source_backup']}
    write_json(state_path(report['layer']), state)
    return state


def load_state(snapshot, layer):
    try:
        state = json.loads(state_path(layer).read_text(encoding='utf-8'))
        if (state.get('format') != 'littletec-led-validation' or state.get('version') != 1
                or state.get('visual_confirmed') is not True
                or state.get('restoration_trial_verified') is not True
                or state.get('led_readback') is not False
                or state.get('layer') != layer or state.get('identity') != snapshot['identity']
                or state.get('device_path', '').lower() != device_path(snapshot).lower()):
            return None
        spec = parse_lighting_packet(bytes.fromhex(state['current_packet_hex']))
        return state if spec['layer'] == layer else None
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def apply_lighting(snapshot, mode, color, layer, observe, report_path, backend=None):
    """Aplica uma cor após ensaio visual, com pacote inverso e retorno em falha.

    A confirmação do estado anterior é obrigatória porque alterações feitas por
    outro programa ou no teclado não podem ser detectadas por readback de LED.
    """
    target = lighting_packet(mode, color, layer)
    state = load_state(snapshot, layer)
    if state is None:
        raise PermissionError('Valide primeiro a troca e o retorno de LED nesta camada.')
    original = bytes.fromhex(state['current_packet_hex'])
    original_spec = parse_lighting_packet(original)
    if observe('before', original_spec) is not True:
        write_json(state_path(layer), dict(state, visual_confirmed=False))
        raise RuntimeError('A referência visual atual não foi confirmada; nenhum LED enviado.')
    backend = backend or LedBackend()
    before = backend.read()
    unchanged_keys(snapshot, before)
    if load_state(before, layer) != state:
        raise RuntimeError('O registro de LED mudou durante a revisão; envio cancelado.')
    report = {'format': 'littletec-led-apply', 'version': 1, 'layer': layer,
              'identity': before['identity'], 'device_path': device_path(before),
              'source_backup': before['folder'], 'before_packet_hex': original.hex(),
              'packet_hex': target.hex(), 'restore_packet_hex': original.hex(),
              'commit_packet_hex': COMMIT_PACKET.hex(), 'led_readback': False,
              'complete': False, 'restoration_visual_verified': False}
    write_json(report_path, report)
    invalid = dict(state, visual_confirmed=False, pending_report=str(report_path))
    write_json(state_path(layer), invalid)  # Uma interrupção não mantém estado confirmado falso.
    try:
        backend.send(target)
        after = backend.read()
        unchanged_keys(before, after)
        if observe('applied', parse_lighting_packet(target)) is not True:
            raise RuntimeError('A nova aparência não foi confirmada.')
        confirmed = dict(state, current_packet_hex=target.hex(), source_backup=after['folder'])
        write_json(state_path(layer), confirmed)
        report.update(complete=True, keys_unchanged=True, visual_confirmed=True,
                      after_backup=after['folder'])
    except Exception as error:
        report['error'] = str(error)
        try:
            backend.send(original)
            restored = backend.read()
            unchanged_keys(before, restored)
            if observe('restore_previous', original_spec) is not True:
                raise RuntimeError('Retorno à aparência anterior não confirmado.')
            report.update(restoration_visual_verified=True, keys_unchanged=True,
                          restored_backup=restored['folder'])
            write_json(state_path(layer), state)
        except Exception as restore_error:
            report['restoration_error'] = str(restore_error)
    finally:
        write_json(report_path, report)
    return report


def run_trial(backend, observe, report_path, layer=1, approved_replace_unread_led=False):
    """Exige exceção explícita para estabelecer LED inicial sem readback.

    observe(stage, spec) deve ter prazo finito e retornar True somente quando o
    usuário confirmar a aparência no hardware. Retorno acontece em finally.
    """
    if approved_replace_unread_led is not True:
        raise PermissionError('Falta aprovação específica para estabelecer a referência LED sem ler o estado anterior.')
    report = trial_plan(layer)
    before = backend.read()
    report.update(device_path=device_path(before), identity=before['identity'],
                  source_backup=before['folder'], complete=False,
                  baseline_visual_verified=False, test_visual_verified=False,
                  restoration_visual_verified=False, keys_unchanged=False,
                  approved_replace_unread_led=True, collected_at_utc=datetime.now(timezone.utc).isoformat())
    write_json(report_path, report)  # Plano e cópia registrados antes do primeiro FE.
    write_json(state_path(layer), {'format': 'littletec-led-validation', 'version': 1,
        'layer': layer, 'identity': before['identity'], 'device_path': device_path(before),
        'visual_confirmed': False, 'pending_report': str(report_path)})
    baseline = bytes.fromhex(report['baseline_packet_hex'])
    test = bytes.fromhex(report['test_packet_hex'])
    attempted = False
    try:
        attempted = True
        backend.send(baseline)
        unchanged_keys(before, backend.read())
        report['baseline_visual_verified'] = observe('baseline', report['baseline']) is True
        write_json(report_path, report)
        if not report['baseline_visual_verified']:
            raise RuntimeError('Ciano estático não confirmado; teste vermelho cancelado.')
        backend.send(test)
        unchanged_keys(before, backend.read())
        report['test_visual_verified'] = observe('test', report['test']) is True
    except Exception as error:
        report['error'] = str(error)
    finally:
        if attempted:
            try:
                backend.send(baseline)
                restored = backend.read()
                unchanged_keys(before, restored)
                report['keys_unchanged'] = True
                report['restored_backup'] = restored['folder']
                report['restoration_visual_verified'] = observe('restore', report['baseline']) is True
            except Exception as error:
                report['restoration_error'] = str(error)
        report['complete'] = not report.get('error') and not report.get('restoration_error') and all(report[field] for field in (
            'baseline_visual_verified', 'test_visual_verified',
            'restoration_visual_verified', 'keys_unchanged'))
        write_json(report_path, report)
    return report
