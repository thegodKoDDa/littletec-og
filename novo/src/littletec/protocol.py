"""Formato recuperado do editor original e das leituras reais do modelo 12+2.

Codificação pura: este módulo não abre dispositivos nem envia pacotes.
Origem e vetores independentes em docs/PROTOCOLO.md e captures/*oracle*.
"""
from copy import deepcopy
from .catalog import COLORS
from .profile import new_profile, validate, validate_action

KEY_CODES = {key: code for code, key in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 4)}
KEY_CODES.update({key: code for code, key in enumerate('1234567890', 0x1e)})
KEY_CODES.update({key: code for key, code in (
    ('Enter', 0x28), ('Escape', 0x29), ('Backspace', 0x2a), ('Tab', 0x2b), ('Space', 0x2c),
    ('Minus', 0x2d), ('Equal', 0x2e), ('BracketLeft', 0x2f), ('BracketRight', 0x30),
    ('Backslash', 0x31), ('Semicolon', 0x33), ('Quote', 0x34), ('Grave', 0x35),
    ('Comma', 0x36), ('Period', 0x37), ('Slash', 0x38), ('CapsLock', 0x39),
    ('PrintScreen', 0x46), ('ScrollLock', 0x47), ('Pause', 0x48), ('Insert', 0x49),
    ('Home', 0x4a), ('PageUp', 0x4b), ('Delete', 0x4c), ('End', 0x4d), ('PageDown', 0x4e),
    ('Right', 0x4f), ('Left', 0x50), ('Down', 0x51), ('Up', 0x52), ('NumLock', 0x53),
    ('NumDivide', 0x54), ('NumMultiply', 0x55), ('NumSubtract', 0x56), ('NumAdd', 0x57),
    ('NumEnter', 0x58), ('Num0', 0x62), ('NumDecimal', 0x63), ('IntlBackslash', 0x64), ('Menu', 0x65))})
KEY_CODES.update({f'Num{i}': 0x58 + i for i in range(1, 10)})
KEY_CODES.update({f'F{i}': 0x39 + i for i in range(1, 13)})
KEY_CODES.update({f'F{i}': 0x68 + i - 13 for i in range(13, 25)})
CODE_KEYS = {value: key for key, value in KEY_CODES.items()}
MOD_BITS = {'Ctrl': 1, 'Shift': 2, 'Alt': 4, 'Win': 8,
            'RightCtrl': 16, 'RightShift': 32, 'RightAlt': 64, 'RightWin': 128}
MEDIA_CODES = {'play_pause': 0xcd, 'stop': 0xb7, 'previous': 0xb6, 'next': 0xb5,
               'computer': 0x194, 'brightness_up': 0x6f, 'brightness_down': 0x70,
               'media_player': 0x183, 'mute': 0xe2, 'volume_up': 0xe9, 'volume_down': 0xea,
               'calculator': 0x192, 'browser_home': 0x223, 'email': 0x18a,
               'bass_up': 0x152, 'bass_down': 0x153, 'treble_up': 0x154, 'treble_down': 0x155,
               'browser_refresh': 0x227, 'browser_forward': 0x225, 'browser_back': 0x224}
CODE_MEDIA = {value: key for key, value in MEDIA_CODES.items()}
# Ordem física (esquerda, clique, direita) confirmada no original em execução.
PHYSICAL_RECORDS = (*range(1, 13), 16, 17, 18, 19, 20, 21)
# O fluxo original lê os trios na ordem 18,17,16 e edita slots 16,17,18.
READ_TO_WRITE = {index: index for index in range(1, 25)}
for _start in (16, 19, 22):
    READ_TO_WRITE[_start], READ_TO_WRITE[_start + 2] = _start + 2, _start
COMMIT_PACKET = bytes.fromhex('03fdfeff') + bytes(61)


def normalize_encoder_headers(layers):
    """Cópia para interpretação do fluxo 15+3x3, sem alterar respostas brutas.

    Hardware devolve o ID armazenado no registro, inclusive após FD16 gravar o
    primeiro membro que na fábrica tinha ID18. A ordem dos trios é a ordem de
    slots no fluxo observado; aceita só o ID de fábrica ou de edição em cada
    posição. Identidade 12+2/0 deve ser validada pelo chamador.
    """
    if len(layers) != 3:
        raise ValueError('Esperadas três camadas.')
    normalized = []
    for layer_number, packets in enumerate(layers, 1):
        if len(packets) != 24 or {p[2] for p in packets[:15]} != set(range(1, 16)):
            raise ValueError('Fluxo inicial das 15 teclas inválido.')
        result = []
        for arrival, response in enumerate(packets, 1):
            record_from_response(response)
            if response[3] != layer_number:
                raise ValueError('Camada incorreta.')
            copy = bytearray(response)
            if arrival >= 16:
                factory = READ_TO_WRITE[arrival]
                if response[2] not in (arrival, factory):
                    raise ValueError('Cabeçalho de encoder incompatível com o slot do fluxo validado.')
                copy[2] = factory
            result.append(bytes(copy))
        normalized.append(result)
    return normalized


def record_from_response(response):
    if len(response) != 65 or response[:2] != b'\x03\xfa':
        raise ValueError('Relatório bruto inválido.')
    if not 1 <= response[2] <= 24 or not 1 <= response[3] <= 3:
        raise ValueError('Índice/camada fora do fluxo validado.')
    # read_Hidkey_Data copia resposta[2:51] para record[1:50].
    return b'\xfd' + response[2:51]


def validate_record(record):
    if len(record) != 50 or not 1 <= record[2] <= 3:
        raise ValueError('Registro deve ter 50 bytes e camada válida.')
    if not ((record[0] == 0xfd and 1 <= record[1] <= 24) or
            (record[0] == 0xfe and record[1] == 0xb0 and record[3] == 8)):
        raise ValueError('Cabeçalho/índice de registro fora do formato recuperado.')


def opaque(record):
    return {'type': 'raw', 'data_hex': bytes(record).hex()}


def decode_record(record):
    validate_record(record)
    record = bytes(record)
    mode, count = record[3], record[9]
    # Não descartar reservados: campos não compreendidos tornam a ação opaca.
    if any(record[6:9]):
        return opaque(record)
    if mode == 1:
        if count <= 1 and not any(record[10:]):
            return {'type': 'none'} if not any(record[4:6]) else opaque(record)
        if count > 20:
            return opaque(record)
        steps = []
        slots = count or (1 if record[10] else 0)
        if any(record[10 + slots * 2:]):
            return opaque(record)
        for index in range(slots):
            modifier, code = record[10 + index * 2:12 + index * 2]
            if code and code not in CODE_KEYS:
                return opaque(record)
            if not code and not modifier:
                return opaque(record)
            steps.append({'key': CODE_KEYS.get(code, ''),
                          'modifiers': [m for m, bit in MOD_BITS.items() if modifier & bit]})
        action = {'type': 'keyboard', 'steps': steps} if steps else {'type': 'none'}
    elif mode == 2 and count in (1, 2) and not any(record[12:]):
        code = int.from_bytes(record[10:12], 'little')
        if code not in CODE_MEDIA:
            return opaque(record)
        action = {'type': 'media', 'command': CODE_MEDIA[code]}
    elif mode == 3 and count == 1 and not any(record[12:14]) and not any(record[15:]):
        modifier, buttons, wheel = record[10], record[11], record[14]
        if modifier & ~7:
            return opaque(record)
        if buttons in (1, 2, 4) and wheel == 0:
            command = {1: 'left', 2: 'right', 4: 'middle'}[buttons]
        elif buttons == 0 and wheel in (1, 255):
            command = 'wheel_up' if wheel == 1 else 'wheel_down'
        else:
            return opaque(record)
        action = {'type': 'mouse', 'command': command,
                  'modifiers': [m for m in ('Ctrl', 'Shift', 'Alt') if modifier & MOD_BITS[m]]}
    elif mode == 5 and count == 0 and not any(record[10:]):
        value = int.from_bytes(record[4:6], 'little')
        return {'type': 'delay', 'ms': value} if value <= 6000 else opaque(record)
    elif mode == 0 and count == 0 and not any(record[4:]):
        action = {'type': 'none'}
    else:
        return opaque(record)
    # Atraso associado a uma ação diferente de tipo 5 ainda é desconhecido.
    return opaque(record) if any(record[4:6]) else action


def encode_record(action, index, layer, original=None):
    action = validate_action(action)
    if type(index) is not int or not 1 <= index <= 24 or type(layer) is not int or not 1 <= layer <= 3:
        raise ValueError('Índice/camada inválido para codificação.')
    if original is not None:
        validate_record(original)
        if original[1:3] != bytes([index, layer]):
            raise ValueError('Registro original pertence a outra posição/camada.')
        if decode_record(original) == action:
            return bytes(original)
    if action['type'] == 'raw':
        raw = bytes.fromhex(action['data_hex'])
        validate_record(raw)
        if original is not None and raw != bytes(original):
            raise ValueError('Registro não interpretado só pode ser preservado sem alteração.')
        if raw[1:3] != bytes([index, layer]):
            raise ValueError('Ação não interpretada não pode ser movida de posição/camada.')
        return raw
    record = bytearray(50)
    record[:4] = bytes([0xfd, index, layer, 1])
    kind = action['type']
    if kind == 'none':
        record[9] = 1  # Botão NULL do original.
    elif kind == 'keyboard':
        steps = action['steps']
        if len(steps) > 20:
            raise ValueError('O registro de hardware comporta no máximo 20 etapas de teclado.')
        record[9] = len(steps)
        for offset, step in enumerate(steps):
            code = KEY_CODES.get(step['key'], 0)
            modifier = sum(MOD_BITS[m] for m in step['modifiers'])
            record[10 + offset * 2:12 + offset * 2] = bytes([modifier, code])
        if len(steps) == 1 and not steps[0]['key']:
            record[9] = 0  # Modificador isolado, como SetFunKey no original.
    elif kind == 'media':
        record[3], record[9] = 2, 2  # Original novo: 2. Registros de fábrica: 1.
        record[10:12] = MEDIA_CODES[action['command']].to_bytes(2, 'little')
    elif kind == 'mouse':
        record[3], record[9] = 3, 1
        record[10] = sum(MOD_BITS[m] for m in action['modifiers'])
        command = action['command']
        if command in ('left', 'right', 'middle'):
            record[11] = {'left': 1, 'right': 2, 'middle': 4}[command]
        else:
            record[14] = 1 if command == 'wheel_up' else 255
    elif kind == 'delay':
        record[3] = 5
        record[4:6] = action['ms'].to_bytes(2, 'little')
    return bytes(record)


def encode_lighting(mode, color, layer):
    if type(mode) is not int or not 0 <= mode <= 5 or color not in COLORS or not 1 <= layer <= 3:
        raise ValueError('Iluminação inválida.')
    record = bytearray(50)
    record[:4] = bytes([0xfe, 0xb0, layer, 8])
    record[9] = 1
    record[11] = ((list(COLORS).index(color) + 1) << 4) | mode
    return bytes(record)


def packet_for_record(record):
    validate_record(record)
    return b'\x03' + bytes(record) + bytes(14)


def index_layers(layers):
    if len(layers) != 3:
        raise ValueError('Esperadas três camadas brutas.')
    result = []
    for layer_number, packets in enumerate(layers, 1):
        records = {}
        for response in packets:
            record = bytearray(record_from_response(response))
            record[1] = READ_TO_WRITE[record[1]]
            record = bytes(record)
            if record[2] != layer_number or record[1] in records:
                raise ValueError('Camada incorreta ou índice repetido.')
            records[record[1]] = record
        if set(records) != set(range(1, 25)):
            raise ValueError('Camada bruta incompleta.')
        result.append(records)
    return result


def profile_from_layers(layers, identity):
    if (identity.get('key_count'), identity.get('encoder_count'), identity.get('variant')) != (12, 2, 0):
        raise ValueError('Mapeamento físico validado somente para 12+2/variante 0.')
    indexed = index_layers(layers)
    profile = new_profile()
    profile['name'] = 'Meu teclado USB'
    profile['layers'] = [[decode_record(records[index]) for index in PHYSICAL_RECORDS] for records in indexed]
    # Não inventar um LED lido: o fluxo FA observado não retorna esse registro.
    profile['lighting'] = [{'mode': None, 'color': None} for _ in range(3)]
    return validate(profile)


def build_plan(layers, identity, profile):
    profile = validate(profile)
    if (profile['key_count'], profile['encoder_count']) != (12, 2):
        raise ValueError('Envio planejado somente para o teclado 12+2.')
    profile_from_layers(layers, identity)  # Valida identidade e integridade da origem.
    indexed = index_layers(layers)
    changes = []
    for layer, records in enumerate(indexed, 1):
        for position, index in enumerate(PHYSICAL_RECORDS):
            before = records[index]
            after = encode_record(profile['layers'][layer - 1][position], index, layer, original=before)
            if after != before:
                changes.append({'layer': layer, 'position': position, 'record_index': index,
                                'before_hex': before.hex(), 'after_hex': after.hex(),
                                'packet_hex': packet_for_record(after).hex(),
                                'restore_packet_hex': packet_for_record(before).hex()})
    return {'format': 'littletec-change-plan', 'version': 1, 'hardware_sent': False,
            'restoration_validated': False, 'identity': deepcopy(identity), 'changes': changes,
            'commit_packet_hex': COMMIT_PACKET.hex(),
            'lighting_pending': any(led['mode'] is not None for led in profile['lighting']),
            'note': 'Plano offline; restauração física ainda não validada. Iluminação fora do plano de envio.'}
