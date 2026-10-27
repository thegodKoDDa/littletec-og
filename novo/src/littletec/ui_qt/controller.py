"""Ponte Qt: edição local, captura de teclado, atalhos prontos, tonalidades e I/O serial."""
from copy import deepcopy
import json
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot, QThread
from PySide6.QtWidgets import QFileDialog, QMessageBox

from ..catalog import (
    COLORS, COLOR_SHADES, ENCODER_PRESETS, KEYS, LAYER_TEMPLATES, LED_MODES,
    MEDIA, MODIFIERS, MOUSE, MODELS, QUICK_ACTIONS, SHORTCUT_PRESETS,
    action_from_qt_event, action_from_text, closest_hardware_color,
    hex_to_hsv, hsv_to_hex, label_key, label_action, _parse_hex_rgb
)
from ..editor_session import EditorSession
from ..profile import load, save, new_profile


def action_catalog():
    result = [{'title': title, 'category': 'Atalhos prontos',
               'action': {'type': 'keyboard', 'steps': deepcopy(steps)}}
              for title, steps in SHORTCUT_PRESETS]
    result += [{'title': label_key(key), 'category': 'Teclado',
                'action': {'type': 'keyboard', 'steps': [{'key': key, 'modifiers': []}]}}
               for key in KEYS]
    result += [{'title': title, 'category': 'Multimídia', 'action': {'type': 'media', 'command': key}}
               for key, title in MEDIA.items()]
    result += [{'title': title, 'category': 'Mouse', 'action': {'type': 'mouse', 'command': key, 'modifiers': []}}
               for key, title in MOUSE.items()]
    for modifier in ('Ctrl', 'Shift', 'Alt'):
        for key in ('wheel_up', 'wheel_down'):
            result.append({'title': f'{modifier} + {MOUSE[key]}', 'category': 'Mouse',
                           'action': {'type': 'mouse', 'command': key, 'modifiers': [modifier]}})
    symbols = list(zip('~!@#$%^&*()_+{}|:"<>?',
                       ('Grave', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'Minus', 'Equal',
                        'BracketLeft', 'BracketRight', 'Backslash', 'Semicolon', 'Quote', 'Comma', 'Period', 'Slash')))
    result += [{'title': symbol, 'category': 'Atalhos e símbolos',
                'action': {'type': 'keyboard', 'steps': [{'key': key, 'modifiers': ['Shift']}]}}
               for symbol, key in symbols]
    result += [{'title': title, 'category': 'Atalhos e símbolos',
                'action': {'type': 'keyboard', 'steps': [{'key': '', 'modifiers': [mod]}]}}
               for title, mod in (('Mac command', 'Win'), ('Mac option', 'Alt'), ('Mac control', 'Ctrl'),
                                  ('Mac command direito', 'RightWin'), ('Mac option direito', 'RightAlt'))]
    return result


class StudioController(QObject):
    changed = Signal()
    messageChanged = Signal()
    requested = Signal(object)

    def __init__(self, profile=None, parent=None, service=None):
        super().__init__(parent)
        self.session = EditorSession(profile)
        if profile is None:
            for idx in range(3):
                self.session.profile['lighting'][idx]['mode'] = 1
            self.session.mark_saved()
        self._keep_draft = profile is not None
        self._catalog = action_catalog()
        self._message = 'Selecione qualquer tecla e pressione no seu teclado (ou escolha uma ação abaixo).'
        self._detail = ''
        self._snapshot = None
        self._busy = False
        self._connection = 'desconectado'
        self._thread = self._worker = None
        self._service = service
        self._file = None
        self._last_lighting = [None] * 3
        self._custom_tints = [None] * 3
        self._custom_hsv = [None] * 3
        self._pending_led = None
        self._clipboard_action = None
        self._request_profile = None
        self._request_session = None
        self._review = []
        self._plan = None
        self._state_cache = None

    @Property('QVariantMap', notify=changed)
    def state(self):
        if self._state_cache is not None:
            return self._state_cache
        state = self.session.state()
        review, plan_error = [], ''
        if self._snapshot:
            try:
                from ..protocol import build_plan, decode_record
                self._plan = build_plan(self._snapshot['layers'], self._snapshot['identity'], self.session.profile)
                for change in self._plan['changes']:
                    pos = change['position']
                    title = f'Tecla {pos + 1}' if pos < 12 else f'Giro {(pos - 12)//3 + 1} · {("Esquerda", "Pressionar", "Direita")[(pos-12)%3]}'
                    review.append({'layer': change['layer'], 'title': title,
                                   'before': label_action(decode_record(bytes.fromhex(change['before_hex']))),
                                   'after': label_action(decode_record(bytes.fromhex(change['after_hex'])))})
            except ValueError as error:
                plan_error = str(error)
        self._review = review
        if self._snapshot and not plan_error:
            baseline = self._snapshot['profile']['layers'][self.session.layer]
            for position in state['positions']:
                idx = position['index']
                position['modified'] = (idx < len(baseline)
                                        and self.session.profile['layers'][self.session.layer][idx] != baseline[idx])
        else:
            for position in state['positions']:
                position['modified'] = False
        last = self._last_lighting[self.session.layer]
        hw_color = state['lighting'].get('color')
        hw_mode = state['lighting'].get('mode')
        default_hex = COLORS[hw_color][1] if hw_color in COLORS else '#22d3ee'
        visual_hex = self._custom_tints[self.session.layer] or default_hex
        if self._custom_hsv[self.session.layer] is not None:
            v_hue, v_sat, v_val = self._custom_hsv[self.session.layer]
        else:
            v_hue, v_sat, v_val = hex_to_hsv(visual_hex)
        hw_name = COLORS[hw_color][0] if hw_color in COLORS else 'Ciano'
        hw_hex = COLORS[hw_color][1] if hw_color in COLORS else '#22d3ee'
        eff_mode = hw_mode if isinstance(hw_mode, int) else 1
        color_idx = (list(COLORS).index(hw_color) + 1) if hw_color in COLORS else 5
        hw_byte_hex = f'0x{(color_idx << 4) | eff_mode:02X}'
        layers_summary = []
        for l_idx in range(3):
            l_light = self.session.profile['lighting'][l_idx]
            l_color = l_light.get('color') if l_light.get('color') in COLORS else 'cyan'
            l_mode = l_light.get('mode') if isinstance(l_light.get('mode'), int) else 1
            l_mode_name = next((m['name'] for m in LED_MODES if m['id'] == l_mode), f'Modo {l_mode}')
            assigned = sum(1 for a in self.session.profile['layers'][l_idx] if a.get('type') != 'none')
            l_last = self._last_lighting[l_idx]
            layers_summary.append({
                'index': l_idx,
                'number': l_idx + 1,
                'colorId': l_color,
                'colorName': COLORS[l_color][0],
                'colorHex': COLORS[l_color][1],
                'modeId': l_mode,
                'modeName': l_mode_name,
                'assignedCount': assigned,
                'totalCount': len(self.session.profile['layers'][l_idx]),
                'sentColorName': COLORS[l_last['color']][0] if l_last and l_last.get('color') in COLORS else '',
                'sentModeId': l_last['mode'] if l_last and 'mode' in l_last else -1,
            })
        state.update(busy=self._busy, connection=self._connection, connected=self._snapshot is not None,
                     review=review, pendingCount=len(review), planError=plan_error,
                     filePath=str(self._file or ''), lastLighting=deepcopy(last or {}),
                     visualColorHex=visual_hex, visualHue=v_hue, visualSat=v_sat, visualVal=v_val,
                     hwColorName=hw_name, hwColorHex=hw_hex, hwByteHex=hw_byte_hex,
                     layersSummary=layers_summary,
                     canPaste=self._clipboard_action is not None,
                     clipboardLabel=label_action(self._clipboard_action) if self._clipboard_action else '',
                     backup=self._snapshot['folder'] if self._snapshot else '',
                     canApply=bool(review) and not plan_error and not self._busy,
                     canApplyLighting=state['lighting']['mode'] is not None and state['lighting']['color'] is not None)
        self._state_cache = state
        return state

    @Property('QVariantList', constant=True)
    def colors(self):
        return [{'id': key, 'name': name, 'color': color} for key, (name, color) in COLORS.items()]

    @Property('QVariantList', constant=True)
    def colorShades(self):
        return [dict(item, index=idx, hwName=COLORS[item['hw']][0], hwHex=COLORS[item['hw']][1])
                for idx, item in enumerate(COLOR_SHADES)]

    @Property('QVariantList', constant=True)
    def ledModes(self):
        return [dict(item) for item in LED_MODES]

    @Property('QVariantList', constant=True)
    def quickActions(self):
        return [{'index': idx, 'title': item['title']} for idx, item in enumerate(QUICK_ACTIONS)]

    @Property('QVariantList', constant=True)
    def encoderPresets(self):
        return [{'index': idx, 'title': item['title'], 'subtitle': item['subtitle']}
                for idx, item in enumerate(ENCODER_PRESETS)]

    @Property('QVariantList', constant=True)
    def layerTemplates(self):
        return [{'index': idx, 'title': item['title'], 'subtitle': item['subtitle']}
                for idx, item in enumerate(LAYER_TEMPLATES)]

    @Property('QVariantList', constant=True)
    def models(self):
        return [{'id': key, 'keys': data[0], 'encoders': data[1], 'columns': data[2]} for key, data in MODELS.items()]

    @Property('QStringList', constant=True)
    def modifiers(self):
        return list(MODIFIERS)

    @Property(str, notify=messageChanged)
    def message(self):
        return self._message

    @Property(str, notify=messageChanged)
    def detail(self):
        return self._detail

    def _notify(self, message=None):
        self._state_cache = None
        if message is not None:
            self._message = message
        self.changed.emit()
        self.messageChanged.emit()

    def _run(self, command, custom_message=None):
        try:
            before = deepcopy(self.session.profile)
            command()
            if before != self.session.profile:
                self._keep_draft = True
                self._message = custom_message or 'Rascunho atualizado. Clique em Aplicar mapeamento para gravar no teclado.'
            elif custom_message:
                self._message = custom_message
        except (ValueError, OSError, KeyError) as error:
            self._message = str(error)
        self._notify()

    def _start(self, operation, **payload):
        if self._busy:
            if operation in ('led', 'led_all'):
                self._pending_led = (operation, payload)
                self._notify('Aguardando envio atual concluir para aplicar a nova cor…')
            return
        if self._thread is None:
            from .device_worker import DeviceWorker
            self._thread = QThread(self)
            self._worker = DeviceWorker(self._service)
            self._worker.moveToThread(self._thread)
            self.requested.connect(self._worker.execute)
            self._worker.completed.connect(self._completed)
            self._thread.finished.connect(self._worker.deleteLater)
            self._thread.start()
        self._busy = True
        self._connection = 'ocupado'
        self._request_profile = deepcopy(self.session.profile)
        self._request_session = self.session
        self._request_dirty = self.session.dirty
        self._notify({'read': 'Lendo o teclado e salvando cópia…',
                      'led': 'Enviando iluminação para esta camada…',
                      'led_all': 'Enviando iluminação para as 3 camadas…',
                      'apply': 'Aplicando e conferindo o mapeamento…',
                      'diagnose': 'Verificando conexão…'}[operation])
        self.requested.emit(dict(operation=operation, **payload))

    @Slot(object)
    def _completed(self, event):
        self._busy = False
        if 'error' in event:
            self._pending_led = None
            self._connection = 'erro'
            self._detail = event['error']
            self._notify(event['error'])
            return
        result = event['result']
        operation = event['operation']
        self._connection = 'conectado' if result.get('snapshot') or self._snapshot else 'desconectado'
        if 'snapshot' in result:
            self._snapshot = result['snapshot']
        if operation == 'read':
            self._last_lighting = result['lastLighting']
            if (self.session is self._request_session and self.session.profile == self._request_profile
                    and not self._keep_draft and not self._request_dirty and not self.session.dirty):
                self._adopt_snapshot()
                message = 'Teclado carregado. Clique em uma tecla e pressione no seu teclado ou escolha uma ação.'
            else:
                message = 'Teclado lido. Seu rascunho foi mantido; use Carregar leitura para substituí-lo.'
        elif operation == 'led':
            self._last_lighting[result['lighting']['layer'] - 1] = result['lighting']
            self.session.mark_saved()
            message = result['message']
        elif operation == 'led_all':
            for item in result.get('lighting_all', []):
                self._last_lighting[item['layer'] - 1] = item
            self.session.mark_saved()
            message = result['message']
        elif operation == 'apply':
            if self.session is self._request_session and self.session.profile == self._request_profile:
                self.session.reset_history()
                self.session.mark_saved()
            message = result['message']
        else:
            from ..diagnostics import format_report
            self._detail = format_report(result['diagnostic'])
            message = 'Diagnóstico concluído.'
        if result.get('journal'):
            self._detail = 'Registro da operação: ' + result['journal']
        self._notify(message)
        if self._pending_led is not None:
            next_op, next_payload = self._pending_led
            self._pending_led = None
            if 'snapshot' in next_payload and self._snapshot is not None:
                next_payload['snapshot'] = self._snapshot
            self._start(next_op, **next_payload)

    def _adopt_snapshot(self):
        prev_layer = self.session.layer if self.session else 0
        prev_selected = self.session.selected if self.session else 0
        profile = deepcopy(self._snapshot['profile'])
        for layer, last in enumerate(self._last_lighting):
            if last:
                profile['lighting'][layer] = {'mode': last['mode'], 'color': last['color']}
            else:
                profile['lighting'][layer] = {'mode': 1, 'color': 'cyan'}
        self.session = EditorSession(profile)
        if 0 <= prev_layer < 3:
            self.session.layer = prev_layer
        if 0 <= prev_selected < len(self.session.profile['layers'][self.session.layer]):
            self.session.selected = prev_selected
        self._file = None
        self._keep_draft = False

    @Slot()
    def readKeyboard(self):
        self._start('read')

    @Slot()
    def loadDeviceProfile(self):
        if self._snapshot and not self._busy and self.confirmDiscard():
            self._adopt_snapshot()
            self._notify('Leitura carregada no editor.')

    @Slot()
    def applyLighting(self):
        light = self.session.profile['lighting'][self.session.layer]
        mode = light['mode'] if light['mode'] is not None else 1
        color = light['color'] if light['color'] in COLORS else 'cyan'
        if light['mode'] is None or light['color'] is None:
            self.session.set_lighting(mode, color)
        self._start('led', mode=mode, color=color, layer=self.session.layer + 1, snapshot=self._snapshot)

    @Slot()
    def applyLightingAllLayers(self):
        light = self.session.profile['lighting'][self.session.layer]
        mode = light['mode'] if light['mode'] is not None else 1
        color = light['color'] if light['color'] in COLORS else 'cyan'
        tint = self._custom_tints[self.session.layer]
        hsv = self._custom_hsv[self.session.layer]
        for layer_idx in range(3):
            self._custom_tints[layer_idx] = tint
            self._custom_hsv[layer_idx] = hsv
            self.session.profile['lighting'][layer_idx] = {'mode': mode, 'color': color}
        self.session._commit(deepcopy(self.session.profile))
        self._start('led_all', mode=mode, color=color, snapshot=self._snapshot)

    @Slot()
    def applyMapping(self):
        self._start('apply', snapshot=self._snapshot, profile=deepcopy(self.session.profile))

    @Slot()
    def diagnose(self):
        self._start('diagnose')

    @Slot(int)
    def select(self, index):
        self._run(lambda: self.session.select(index))

    @Slot(int)
    def switchLayer(self, layer):
        self._run(lambda: self.session.switch_layer(layer))

    @Slot(str, str, result='QVariantList')
    def search(self, category, query):
        query = query.casefold().strip()
        return [dict(row, catalogIndex=index) for index, row in enumerate(self._catalog)
                if (category == 'Todas' or row['category'] == category)
                and query in (row['title'] + ' ' + row['category']).casefold()]

    @Slot(int, 'QVariantList', bool)
    def assign(self, index, modifiers, append):
        def update():
            if not 0 <= index < len(self._catalog):
                raise ValueError('Ação inválida.')
            action = deepcopy(self._catalog[index]['action'])
            if action['type'] == 'keyboard':
                old = action['steps'][0]['modifiers']
                action['steps'][0]['modifiers'] = list(dict.fromkeys(old + list(modifiers)))
            elif action['type'] == 'mouse':
                action['modifiers'] = list(dict.fromkeys(action['modifiers'] + list(modifiers)))
            self.session.assign(action, append)
        self._run(update)

    @Slot(int, bool)
    def assignQuick(self, index, append=False):
        def update():
            if not 0 <= index < len(QUICK_ACTIONS):
                raise ValueError('Ação rápida inválida.')
            item = QUICK_ACTIONS[index]
            self.session.assign(deepcopy(item['action']), append)
        if 0 <= index < len(QUICK_ACTIONS):
            pos_title = self.session.state()['positions'][self.session.selected]['title']
            self._run(update, f"{pos_title} definida como: {QUICK_ACTIONS[index]['title']}")
        else:
            self._run(update)

    @Slot(int, int, str, bool, bool, result=bool)
    def captureKeyEvent(self, qt_key, qt_modifiers, text='', append=False, auto_advance=False):
        action = action_from_qt_event(qt_key, qt_modifiers, text)
        if action is None:
            return False
        pos_title = self.session.state()['positions'][self.session.selected]['title']
        action_label = label_action(action)

        def update():
            self.session.assign(action, append)
            if auto_advance and not append:
                total = len(self.session.profile['layers'][self.session.layer])
                self.session.select((self.session.selected + 1) % total)

        self._run(update, f'Reconhecido do seu teclado em {pos_title}: {action_label}')
        return True

    @Slot(str, bool, bool)
    def assignTextMacro(self, text, press_enter=False, append=False):
        def update():
            action = action_from_text(text, press_enter=press_enter)
            self.session.assign(action, append)
        pos_title = self.session.state()['positions'][self.session.selected]['title']
        self._run(update, f'Sequência de texto atribuída em {pos_title}.')

    @Slot()
    def copyPosition(self):
        self._clipboard_action = deepcopy(self.session.action)
        pos_title = self.session.state()['positions'][self.session.selected]['title']
        self._notify(f'Ação copiada de {pos_title}: {label_action(self._clipboard_action)}')

    @Slot()
    def pastePosition(self):
        if self._clipboard_action is None:
            self._notify('Copie uma tecla primeiro antes de colar.')
            return
        pos_title = self.session.state()['positions'][self.session.selected]['title']
        self._run(lambda: self.session.assign(deepcopy(self._clipboard_action), False),
                  f'Ação colada em {pos_title}: {label_action(self._clipboard_action)}')

    @Slot('QVariantList')
    def assignModifiers(self, modifiers):
        self._run(lambda: self.session.assign({'type': 'keyboard', 'steps': [{'key': '', 'modifiers': list(modifiers)}]}))

    @Slot(int, 'QVariantList')
    def editStepModifiers(self, index, modifiers):
        def update():
            action = self.session.action
            if action['type'] != 'keyboard' or not 0 <= index < len(action['steps']):
                raise ValueError('Selecione uma etapa de teclado.')
            action['steps'][index]['modifiers'] = list(modifiers)
            self.session.assign(action)
        self._run(update)

    @Slot(int)
    def assignDelay(self, milliseconds):
        self._run(lambda: self.session.assign({'type': 'delay', 'ms': milliseconds}))

    def _effective_color_mode(self, requested_mode):
        current_mode = self.session.profile['lighting'][self.session.layer].get('mode')
        if isinstance(requested_mode, int) and 1 <= requested_mode <= 5:
            return requested_mode
        if isinstance(current_mode, int) and 1 <= current_mode <= 5:
            return current_mode
        return 1

    @Slot(int)
    @Slot(int, bool)
    def setLightingMode(self, mode, apply_now=False):
        if not 0 <= int(mode) <= 5:
            self._notify('Modo de iluminação inválido.')
            return
        mode = int(mode)
        current_color = self.session.profile['lighting'][self.session.layer].get('color')
        color = current_color if current_color in COLORS else 'cyan'
        mode_name = next((m['name'] for m in LED_MODES if m['id'] == mode), f'Modo {mode}')
        self.session.set_lighting(mode, color)
        self._keep_draft = True
        if apply_now:
            self._start('led', mode=mode, color=color, layer=self.session.layer + 1, snapshot=self._snapshot)
        else:
            self._notify(f'{mode_name} selecionado (cor física: {COLORS[color][0]}).')

    @Slot(int, str)
    @Slot(int, str, bool)
    def setLighting(self, mode, color, apply_now=False):
        eff_mode = mode if isinstance(mode, int) and 0 <= mode <= 5 else self._effective_color_mode(mode)
        if eff_mode == 0 and self.session.profile['lighting'][self.session.layer].get('mode') is None:
            eff_mode = 1
        if color in COLORS:
            self._custom_tints[self.session.layer] = COLORS[color][1]
            self._custom_hsv[self.session.layer] = hex_to_hsv(COLORS[color][1])
        else:
            self._custom_tints[self.session.layer] = None
            self._custom_hsv[self.session.layer] = None
        self.session.set_lighting(eff_mode, color)
        self._keep_draft = True
        hw_name = COLORS[color][0] if color in COLORS else color
        if apply_now:
            self._start('led', mode=eff_mode, color=color, layer=self.session.layer + 1, snapshot=self._snapshot)
        else:
            self._notify(f'Cor física {hw_name} selecionada na Camada {self.session.layer + 1}.')

    @Slot(int, int)
    def selectShade(self, mode, shade_index):
        if not 0 <= int(shade_index) < len(COLOR_SHADES):
            self._notify('Tonalidade inválida.')
            return
        shade = COLOR_SHADES[int(shade_index)]
        eff_mode = self._effective_color_mode(mode)
        hw_color = shade['hw']
        hw_name = COLORS[hw_color][0]
        normalized_hex = shade['hex'].lower()

        def update():
            self._custom_tints[self.session.layer] = normalized_hex
            self._custom_hsv[self.session.layer] = hex_to_hsv(normalized_hex)
            self.session.set_lighting(eff_mode, hw_color)

        self._run(update, f"Tonalidade '{shade['name']}' ({normalized_hex}) → Canal físico USB: {hw_name}.")

    @Slot(int, str)
    def setCustomTone(self, mode, hex_color):
        try:
            r, g, b = _parse_hex_rgb(hex_color)
            normalized_hex = f'#{r:02x}{g:02x}{b:02x}'
            hw_color = closest_hardware_color(normalized_hex)
            hw_name = COLORS[hw_color][0]
        except ValueError as error:
            self._notify(str(error))
            return
        eff_mode = self._effective_color_mode(mode)

        def update():
            self._custom_tints[self.session.layer] = normalized_hex
            self._custom_hsv[self.session.layer] = hex_to_hsv(normalized_hex)
            self.session.set_lighting(eff_mode, hw_color)

        self._run(update, f'Tonalidade {normalized_hex} selecionada → Canal físico USB: {hw_name}.')

    @Slot(int, float, float, float)
    def setHsvTone(self, mode, hue, saturation, value):
        h_int = int(round(float(hue))) % 360
        s_int = max(0, min(100, int(round(float(saturation)))))
        v_int = max(0, min(100, int(round(float(value)))))
        hex_color = hsv_to_hex(h_int, s_int, v_int)
        hw_color = closest_hardware_color(hex_color)
        hw_name = COLORS[hw_color][0]
        eff_mode = self._effective_color_mode(mode)

        def update():
            self._custom_tints[self.session.layer] = hex_color
            self._custom_hsv[self.session.layer] = (h_int, s_int, v_int)
            self.session.set_lighting(eff_mode, hw_color)

        self._run(update, f'Misturador HSV ({h_int}°, {s_int}%, {v_int}%) → {hex_color} · Canal físico USB: {hw_name}.')

    @Slot()
    def copyLightingToAllLayers(self):
        current = deepcopy(self.session.profile['lighting'][self.session.layer])
        if current.get('mode') is None or current.get('color') is None:
            current = {'mode': 1, 'color': 'cyan'}
        tint = self._custom_tints[self.session.layer]
        hsv = self._custom_hsv[self.session.layer]

        def update():
            for layer_idx in range(3):
                self._custom_tints[layer_idx] = tint
                self._custom_hsv[layer_idx] = hsv
                self.session.profile['lighting'][layer_idx] = deepcopy(current)
            self.session._commit(deepcopy(self.session.profile))

        self._run(update, 'Configuração de cor/modo copiada para as 3 camadas.')

    @Slot(int, int, str, bool)
    def setLayerLighting(self, layer_index, mode, color, apply_now=True):
        if not 0 <= int(layer_index) < 3 or color not in COLORS:
            self._notify('Camada ou cor inválida.')
            return
        layer_index = int(layer_index)
        eff_mode = int(mode) if isinstance(mode, int) and 0 <= int(mode) <= 5 else 1

        def update():
            self._custom_tints[layer_index] = COLORS[color][1]
            self._custom_hsv[layer_index] = hex_to_hsv(COLORS[color][1])
            candidate = deepcopy(self.session.profile)
            candidate['lighting'][layer_index] = {'mode': eff_mode, 'color': color}
            self.session._commit(candidate)

        self._run(update, f'Camada {layer_index + 1}: {COLORS[color][0]} · Modo {eff_mode} configurado.')
        if apply_now:
            self._start('led', mode=eff_mode, color=color, layer=layer_index + 1, snapshot=self._snapshot)

    @Slot(int, int)
    def applyEncoderPreset(self, encoder_index, preset_index):
        if not 0 <= int(encoder_index) < self.session.profile['encoder_count']:
            self._notify('Giratório inválido.')
            return
        if not 0 <= int(preset_index) < len(ENCODER_PRESETS):
            self._notify('Preset de giratório inválido.')
            return
        preset = ENCODER_PRESETS[int(preset_index)]
        base = self.session.profile['key_count'] + int(encoder_index) * 3

        def update():
            candidate = deepcopy(self.session.profile)
            for offset, act in enumerate(preset['actions']):
                candidate['layers'][self.session.layer][base + offset] = deepcopy(act)
            self.session._commit(candidate)

        self._run(update, f"Giro {int(encoder_index) + 1} configurado como: {preset['title']}.")

    @Slot(int)
    def applyLayerTemplate(self, template_index):
        if not 0 <= int(template_index) < len(LAYER_TEMPLATES):
            self._notify('Template de camada inválido.')
            return
        tmpl = LAYER_TEMPLATES[int(template_index)]

        def update():
            candidate = deepcopy(self.session.profile)
            target_len = len(candidate['layers'][self.session.layer])
            for idx in range(min(target_len, len(tmpl['positions']))):
                candidate['layers'][self.session.layer][idx] = deepcopy(tmpl['positions'][idx])
            self.session._commit(candidate)

        self._run(update, f"Template '{tmpl['title']}' aplicado na Camada {self.session.layer + 1}.")

    @Slot()
    def copyEncodersToAllLayers(self):
        key_count = self.session.profile['key_count']
        current_encoders = deepcopy(self.session.profile['layers'][self.session.layer][key_count:])

        def update():
            candidate = deepcopy(self.session.profile)
            for l_idx in range(3):
                candidate['layers'][l_idx][key_count:] = deepcopy(current_encoders)
            self.session._commit(candidate)

        self._run(update, f'Giratórios 1 e 2 da Camada {self.session.layer + 1} replicados nas 3 camadas.')

    @Slot(int)
    def invertEncoderDirections(self, encoder_index):
        if not 0 <= int(encoder_index) < self.session.profile['encoder_count']:
            self._notify('Giratório inválido.')
            return
        base = self.session.profile['key_count'] + int(encoder_index) * 3

        def update():
            candidate = deepcopy(self.session.profile)
            layer_list = candidate['layers'][self.session.layer]
            layer_list[base], layer_list[base + 2] = deepcopy(layer_list[base + 2]), deepcopy(layer_list[base])
            self.session._commit(candidate)

        self._run(update, f'Sentido de giro (↶ / ↷) invertido no Giratório {int(encoder_index) + 1}.')

    @Slot()
    def swapEncoders(self):
        if self.session.profile['encoder_count'] < 2:
            return
        b1 = self.session.profile['key_count']
        b2 = b1 + 3

        def update():
            candidate = deepcopy(self.session.profile)
            layer_list = candidate['layers'][self.session.layer]
            trio1 = deepcopy(layer_list[b1:b1 + 3])
            trio2 = deepcopy(layer_list[b2:b2 + 3])
            layer_list[b1:b1 + 3] = trio2
            layer_list[b2:b2 + 3] = trio1
            self.session._commit(candidate)

        self._run(update, 'Funções do Giratório 1 e Giratório 2 trocadas entre si.')

    @Slot(int)
    def clearEncoder(self, encoder_index):
        if not 0 <= int(encoder_index) < self.session.profile['encoder_count']:
            return
        base = self.session.profile['key_count'] + int(encoder_index) * 3

        def update():
            from ..profile import empty_action
            candidate = deepcopy(self.session.profile)
            for offset in range(3):
                candidate['layers'][self.session.layer][base + offset] = empty_action()
            self.session._commit(candidate)

        self._run(update, f'Giratório {int(encoder_index) + 1} limpo.')

    @Slot(int)
    def cloneLayerTo(self, target_layer):
        if not 0 <= int(target_layer) < 3 or int(target_layer) == self.session.layer:
            return
        target_layer = int(target_layer)
        source_layer = self.session.layer

        def update():
            candidate = deepcopy(self.session.profile)
            candidate['layers'][target_layer] = deepcopy(candidate['layers'][source_layer])
            self.session._commit(candidate)

        self._run(update, f'Camada {source_layer + 1} clonada para a Camada {target_layer + 1}.')

    @Slot(int)
    def swapWithPosition(self, other_index):
        total = len(self.session.profile['layers'][self.session.layer])
        if not 0 <= int(other_index) < total or int(other_index) == self.session.selected:
            return
        other_index = int(other_index)
        cur_index = self.session.selected

        def update():
            candidate = deepcopy(self.session.profile)
            layer_list = candidate['layers'][self.session.layer]
            layer_list[cur_index], layer_list[other_index] = deepcopy(layer_list[other_index]), deepcopy(layer_list[cur_index])
            self.session._commit(candidate)
            self.session.select(other_index)

        self._run(update, 'Posições trocadas com sucesso.')

    @Slot(str)
    def clear(self, scope):
        msg = {'position': 'Posição limpa.', 'layer': 'Camada limpa (use Desfazer se precisar).',
               'all': 'Todas as camadas limpas (use Desfazer se precisar).'}
        self._run(lambda: self.session.clear(scope), msg.get(scope, 'Limpo.'))

    @Slot(int, int)
    def moveStep(self, index, delta):
        self._run(lambda: self.session.move_step(index, delta))

    @Slot(int)
    def removeStep(self, index):
        self._run(lambda: self.session.remove_step(index))

    @Slot()
    def undo(self):
        self._run(self.session.undo)

    @Slot()
    def redo(self):
        self._run(self.session.redo)

    @Slot(str)
    def rename(self, name):
        self._run(lambda: self.session.rename(name))

    @Slot(str, int, int, int)
    def newProfile(self, model='12+2', keys=12, encoders=2, columns=4):
        if not self.confirmDiscard():
            return
        def update():
            dimensions = MODELS[model] if model in MODELS else (keys, encoders, columns)
            self.session = EditorSession(new_profile(*dimensions, model=model))
            self._file = None
            self._keep_draft = True
        self._run(update)

    @Slot()
    def openProfile(self):
        if not self.confirmDiscard():
            return
        path, _ = QFileDialog.getOpenFileName(None, 'Abrir perfil', '', 'Perfis LittleTec (*.json)')
        if path:
            def update():
                self.session = EditorSession(load(path))
                self._file = Path(path)
                self._keep_draft = True
            self._run(update)

    @Slot()
    def saveProfile(self):
        if self._file is None:
            self.saveProfileAs()
        else:
            self._save(self._file)

    def _save(self, path):
        try:
            save(path, self.session.profile)
            self.session.mark_saved()
            self._file = Path(path)
            self._notify('Perfil salvo no computador.')
        except (ValueError, OSError) as error:
            self._notify(str(error))

    @Slot()
    def saveProfileAs(self):
        path, _ = QFileDialog.getSaveFileName(None, 'Salvar perfil como', str(self._file or ''), 'Perfis LittleTec (*.json)')
        if path:
            self._save(path if Path(path).suffix else path + '.json')

    @Slot()
    def importBackup(self):
        if not self.confirmDiscard():
            return
        folder = QFileDialog.getExistingDirectory(None, 'Importar cópia bruta LittleTec')
        if folder:
            def update():
                from ..device_service import load_backup
                self._snapshot = load_backup(folder)
                self._last_lighting = [None] * 3
                self._adopt_snapshot()
                self._keep_draft = True
                self._connection = 'cópia local'
            self._run(update)

    @Slot()
    def exportReview(self):
        self.state
        if self._snapshot is None or self._plan is None:
            self._notify('Leia o teclado para exportar diferenças.')
            return
        self._export_json(self._plan, 'Exportar revisão')

    def _export_json(self, value, title):
        path, _ = QFileDialog.getSaveFileName(None, title, '', 'JSON (*.json)')
        if path:
            try:
                Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                self._notify('Arquivo exportado.')
            except OSError as error:
                self._notify(str(error))

    @Slot()
    def exportDiagnostic(self):
        self._export_json({'message': self._message, 'detail': self._detail,
                           'backup': self._snapshot['folder'] if self._snapshot else None}, 'Exportar diagnóstico')

    @Slot(result=bool)
    def confirmDiscard(self):
        if self._busy:
            self._notify('Aguarde a operação terminar antes de substituir o perfil ou fechar.')
            return False
        return True

    @Slot()
    def shutdown(self):
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
