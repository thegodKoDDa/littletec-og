"""Perfil local versionado. Sem codificação ou envio de pacotes USB."""
import json
from pathlib import Path
from .catalog import COLORS, KEYS, MEDIA, MODIFIERS, MOUSE


def empty_action():
    return {'type': 'none'}


def new_profile(count=12, encoders=2, columns=4, model='12+2'):
    # A escolha é manual: 12+2 é o layout observado no programa original.
    return validate({'format': 'littletec-profile', 'version': 2, 'name': 'Meu perfil',
                     'key_count': count, 'encoder_count': encoders, 'columns': columns, 'model': model,
                     'layers': [[empty_action() for _ in range(count + encoders * 3)] for _ in range(3)],
                     'lighting': [{'mode': 0, 'color': 'red'} for _ in range(3)]})


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name}: valor esperado entre {low} e {high}.')
    return value


def modifiers(value, allowed=MODIFIERS):
    if not isinstance(value, list) or any(not isinstance(m, str) or m not in allowed for m in value):
        raise ValueError('Modificadores inválidos no perfil.')
    if len(set(value)) != len(value):
        raise ValueError('Modificadores repetidos no perfil.')
    return [m for m in allowed if m in value]


def validate_action(action):
    if not isinstance(action, dict):
        raise ValueError('Ação inválida no perfil.')
    kind = action.get('type')
    if kind == 'raw':
        value = action.get('data_hex')
        try:
            raw = bytes.fromhex(value) if isinstance(value, str) else b''
        except ValueError:
            raw = b''
        if len(raw) != 50:
            raise ValueError('Registro não interpretado deve conter 50 bytes.')
        return {'type': 'raw', 'data_hex': raw.hex()}
    if kind == 'none':
        return empty_action()
    if kind == 'keyboard':
        steps = action.get('steps')
        # Limite do editor, sem promessa de capacidade equivalente no hardware.
        if not isinstance(steps, list) or not 1 <= len(steps) <= 256:
            raise ValueError('A sequência local deve conter entre 1 e 256 etapas.')
        clean = []
        for step in steps:
            if not isinstance(step, dict) or step.get('key') not in ('', *KEYS):
                raise ValueError('Tecla inválida no perfil.')
            mods = modifiers(step.get('modifiers'))
            if not step['key'] and not mods:
                raise ValueError('Etapa sem tecla ou modificadores.')
            clean.append({'key': step['key'], 'modifiers': mods})
        return {'type': kind, 'steps': clean}
    if kind in ('media', 'mouse'):
        allowed = MEDIA if kind == 'media' else MOUSE
        if not isinstance(action.get('command'), str) or action['command'] not in allowed:
            raise ValueError('Comando inválido no perfil.')
        result = {'type': kind, 'command': action['command']}
        if kind == 'mouse':
            result['modifiers'] = modifiers(action.get('modifiers'), ('Ctrl', 'Shift', 'Alt'))
        return result
    if kind == 'delay':
        return {'type': kind, 'ms': integer(action.get('ms'), 0, 6000, 'Atraso em ms')}
    raise ValueError('Tipo de ação desconhecido.')


def migrate_v1(data):
    count = integer(data.get('key_count'), 1, 60, 'Posições')
    layers = data.get('layers')
    if not isinstance(layers, list) or len(layers) != 3:
        raise ValueError('O perfil deve conter três camadas.')
    converted = []
    for layer in layers:
        if not isinstance(layer, list) or len(layer) != count:
            raise ValueError('Quantidade de posições inconsistente entre camadas.')
        result = []
        for action in layer:
            if not isinstance(action, dict):
                raise ValueError('Ação inválida no perfil antigo.')
            key = action.get('key')
            mods = modifiers(action.get('modifiers'), ('Ctrl', 'Alt', 'Shift', 'Win'))
            if key == '' and not mods:
                result.append(empty_action())
            else:
                result.append(validate_action({'type': 'keyboard', 'steps': [{'key': key, 'modifiers': mods}]}))
        converted.append(result)
    return {**data, 'version': 2, 'encoder_count': 0, 'columns': min(count, 6),
            'model': 'personalizado', 'layers': converted,
            'lighting': [{'mode': 0, 'color': 'red'} for _ in range(3)]}


def validate(data):
    if not isinstance(data, dict) or data.get('format') != 'littletec-profile' or type(data.get('version')) is not int:
        raise ValueError('Formato de perfil inválido.')
    if data['version'] == 1:
        data = migrate_v1(data)
    if data['version'] != 2:
        raise ValueError('Versão de perfil não suportada.')
    count = integer(data.get('key_count'), 0, 60, 'Teclas')
    encoders = integer(data.get('encoder_count'), 0, 4, 'Encoders')
    if not 1 <= count + encoders * 3 <= 60:
        raise ValueError('O perfil deve conter de 1 a 60 ações físicas.')
    columns = integer(data.get('columns'), 1, 10, 'Colunas')
    name = data.get('name')
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError('O nome deve ter entre 1 e 100 caracteres.')
    model = data.get('model')
    if not isinstance(model, str) or not model or len(model) > 100:
        raise ValueError('Modelo de rascunho inválido.')
    layers = data.get('layers')
    if not isinstance(layers, list) or len(layers) != 3:
        raise ValueError('O perfil deve conter três camadas.')
    clean = []
    total = count + encoders * 3
    for layer in layers:
        if not isinstance(layer, list) or len(layer) != total:
            raise ValueError('Quantidade de ações inconsistente entre camadas.')
        clean.append([validate_action(a) for a in layer])
    lighting = data.get('lighting')
    if not isinstance(lighting, list) or len(lighting) != 3:
        raise ValueError('Iluminação deve conter três camadas.')
    leds = []
    for led in lighting:
        if isinstance(led, dict) and led.get('mode') is None and led.get('color') is None:
            leds.append({'mode': None, 'color': None})
            continue
        if not isinstance(led, dict) or not isinstance(led.get('color'), str) or led['color'] not in COLORS:
            raise ValueError('Cor inválida.')
        leds.append({'mode': integer(led.get('mode'), 0, 5, 'Modo LED'), 'color': led['color']})
    return {'format': 'littletec-profile', 'version': 2, 'name': name.strip(),
            'key_count': count, 'encoder_count': encoders, 'columns': columns, 'model': model,
            'layers': clean, 'lighting': leds}


def load(path):
    path = Path(path)
    if path.stat().st_size > 1_000_000:
        raise ValueError('Arquivo de perfil muito grande.')
    return validate(json.loads(path.read_text(encoding='utf-8-sig')))


def save(path, profile):
    import os
    import tempfile
    path = Path(path)
    content = json.dumps(validate(profile), ensure_ascii=False, indent=2) + '\n'
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.littletec-', delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
