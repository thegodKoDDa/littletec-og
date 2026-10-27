"""Estado do editor independente de Tk, Qt e USB; base da migração visual."""
from copy import deepcopy

from .catalog import label_action
from .profile import empty_action, new_profile, validate, validate_action


class EditorSession:
    def __init__(self, profile=None):
        self.profile = validate(deepcopy(profile)) if profile is not None else new_profile()
        self.saved = deepcopy(self.profile)
        self.layer = 0
        self.selected = 0
        self._undo = []
        self._redo = []

    @property
    def dirty(self):
        return self.profile != self.saved

    @property
    def action(self):
        return deepcopy(self.profile['layers'][self.layer][self.selected])

    @property
    def can_undo(self):
        return bool(self._undo)

    @property
    def can_redo(self):
        return bool(self._redo)

    def select(self, position):
        if type(position) is not int or not 0 <= position < len(self.profile['layers'][self.layer]):
            raise ValueError('Posição inválida.')
        self.selected = position

    def switch_layer(self, layer):
        if type(layer) is not int or not 0 <= layer < 3:
            raise ValueError('Camada inválida.')
        self.layer = layer

    def _commit(self, candidate):
        candidate = validate(candidate)
        if candidate == self.profile:
            return
        self._undo.append(deepcopy(self.profile))
        self._undo = self._undo[-100:]
        self._redo.clear()
        self.profile = candidate

    def assign(self, action, append=False):
        action = validate_action(action)
        if append and action['type'] == 'keyboard' and self.action['type'] == 'keyboard':
            action['steps'] = self.action['steps'] + action['steps']
        if action['type'] == 'keyboard' and len(action['steps']) > 20:
            raise ValueError('Esta posição comporta até 20 etapas de teclado.')
        candidate = deepcopy(self.profile)
        candidate['layers'][self.layer][self.selected] = action
        self._commit(candidate)

    def clear(self, scope='position'):
        candidate = deepcopy(self.profile)
        if scope == 'position':
            candidate['layers'][self.layer][self.selected] = empty_action()
        elif scope == 'layer':
            candidate['layers'][self.layer] = [empty_action() for _ in candidate['layers'][self.layer]]
        elif scope == 'all':
            candidate['layers'] = [[empty_action() for _ in layer] for layer in candidate['layers']]
        else:
            raise ValueError('Escopo de limpeza inválido.')
        self._commit(candidate)

    def move_step(self, index, delta):
        action = self.action
        if action['type'] != 'keyboard' or not 0 <= index < len(action['steps']):
            raise ValueError('Etapa inválida.')
        target = index + delta
        if not 0 <= target < len(action['steps']):
            return
        action['steps'][index], action['steps'][target] = action['steps'][target], action['steps'][index]
        candidate = deepcopy(self.profile)
        candidate['layers'][self.layer][self.selected] = action
        self._commit(candidate)

    def remove_step(self, index):
        action = self.action
        if action['type'] != 'keyboard' or not 0 <= index < len(action['steps']):
            raise ValueError('Etapa inválida.')
        del action['steps'][index]
        candidate = deepcopy(self.profile)
        candidate['layers'][self.layer][self.selected] = action if action['steps'] else empty_action()
        self._commit(candidate)

    def set_lighting(self, mode, color):
        candidate = deepcopy(self.profile)
        candidate['lighting'][self.layer] = {'mode': mode, 'color': color}
        self._commit(candidate)

    def undo(self):
        if self._undo:
            self._redo.append(deepcopy(self.profile))
            self.profile = self._undo.pop()

    def redo(self):
        if self._redo:
            self._undo.append(deepcopy(self.profile))
            self.profile = self._redo.pop()

    def mark_saved(self):
        self.saved = deepcopy(self.profile)

    def rename(self, name):
        candidate = deepcopy(self.profile)
        candidate['name'] = name
        self._commit(candidate)

    def reset_history(self):
        self._undo.clear()
        self._redo.clear()

    def state(self):
        count = self.profile['key_count']
        positions = []
        for index, action in enumerate(self.profile['layers'][self.layer]):
            encoder, part = divmod(index - count, 3)
            title = (f'Tecla {index + 1:02}' if index < count else
                     f'Giro {encoder + 1} · {("Esquerda", "Pressionar", "Direita")[part]}')
            positions.append({'index': index, 'title': title, 'label': label_action(action),
                              'kind': action['type'], 'encoder': index >= count})
        return {'name': self.profile['name'], 'layer': self.layer, 'selected': self.selected,
                'keyCount': count, 'encoderCount': self.profile['encoder_count'],
                'columns': self.profile['columns'], 'positions': positions,
                'action': self.action, 'lighting': deepcopy(self.profile['lighting'][self.layer]),
                'dirty': self.dirty, 'canUndo': self.can_undo, 'canRedo': self.can_redo}
