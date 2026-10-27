from copy import deepcopy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.editor_session import EditorSession
from littletec.profile import new_profile


def key(name):
    return {'type': 'keyboard', 'steps': [{'key': name, 'modifiers': []}]}


class SessionTests(unittest.TestCase):
    def test_imported_long_sequence_can_be_reduced_without_losing_history(self):
        profile = new_profile()
        profile['layers'][0][0] = {'type': 'keyboard', 'steps': [key('A')['steps'][0]] * 22}
        session = EditorSession(profile)
        session.remove_step(0)
        self.assertEqual(len(session.action['steps']), 21)
        session.move_step(1, -1)
        session.remove_step(0)
        self.assertEqual(len(session.action['steps']), 20)
        session.undo()
        self.assertEqual(len(session.action['steps']), 21)

    def test_edits_history_and_saved_state_are_independent(self):
        original = new_profile()
        session = EditorSession(original)
        session.assign(key('A'))
        self.assertTrue(session.dirty)
        self.assertEqual(original, new_profile())
        session.mark_saved()
        session.assign(key('B'))
        session.undo()
        self.assertFalse(session.dirty)
        session.redo()
        self.assertEqual(session.action, key('B'))
        exposed = session.action
        exposed['steps'].clear()
        self.assertEqual(session.action, key('B'))

    def test_sequence_limits_are_atomic_and_layer_specific(self):
        session = EditorSession()
        for _ in range(20):
            session.assign(key('A'), append=True)
        before = deepcopy(session.profile)
        with self.assertRaises(ValueError):
            session.assign(key('B'), append=True)
        self.assertEqual(before, session.profile)
        session.switch_layer(1)
        self.assertEqual(session.action, {'type': 'none'})
        session.select(17)
        self.assertTrue(session.state()['positions'][17]['encoder'])

    def test_lighting_and_clear_are_undoable(self):
        session = EditorSession()
        session.assign(key('A'))
        session.assign(key('B'), append=True)
        session.move_step(1, -1)
        self.assertEqual(session.action['steps'][0]['key'], 'B')
        session.remove_step(0)
        self.assertEqual(session.action, key('A'))
        session.set_lighting(1, 'cyan')
        session.clear('all')
        self.assertEqual(session.action, {'type': 'none'})
        session.undo()
        self.assertEqual(session.action, key('A'))
        self.assertEqual(session.profile['lighting'][0], {'mode': 1, 'color': 'cyan'})

    def test_invalid_edits_and_selections_preserve_state(self):
        session = EditorSession()
        before = deepcopy(session.profile)
        for operation in (lambda: session.select(-1), lambda: session.switch_layer(3),
                          lambda: session.set_lighting(99, 'cyan'),
                          lambda: session.assign({'type': 'delay', 'ms': 6001})):
            with self.assertRaises(ValueError):
                operation()
        self.assertEqual(before, session.profile)


if __name__ == '__main__':
    unittest.main()
