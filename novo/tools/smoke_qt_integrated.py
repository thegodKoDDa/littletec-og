"""Regressão Qt + serviço com backend simulado. Nenhuma operação física."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))


def main():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject, QMetaObject, QUrl
    from PySide6.QtQml import QQmlApplicationEngine
    from littletec.ui_qt.controller import StudioController
    from littletec.configuration_service import ConfigurationService
    from test_configuration_service import ProductBackend
    class Backend(ProductBackend):
        def __init__(self):
            super().__init__()
            self.entered = threading.Event()
            self.release = threading.Event()
            self.slow = False
            self.thread_ids = []
        def read(self):
            self.thread_ids.append(threading.get_ident())
            if self.slow:
                self.entered.set()
                assert self.release.wait(5)
                self.slow = False
            return super().read()
    app = QApplication([sys.argv[0]])
    with tempfile.TemporaryDirectory() as directory:
        backend = Backend()
        controller = StudioController(service=ConfigurationService(backend, directory))
        engine = QQmlApplicationEngine()
        warnings = []
        engine.warnings.connect(lambda messages: warnings.extend(str(m) for m in messages))
        engine.setInitialProperties({'studio': controller})
        engine.load(QUrl.fromLocalFile(str(ROOT / 'src/littletec/ui_qt/qml/Main.qml')))
        assert engine.rootObjects(), warnings
        window = engine.rootObjects()[0]
        def wait():
            deadline = time.monotonic() + 10
            while controller.state['busy'] and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)
            assert not controller.state['busy'], controller.message
        try:
            controller.readKeyboard()
            assert controller.state['busy']
            controller.readKeyboard()  # O segundo clique não cria outro executor.
            wait()
            assert controller.state['connected'] and controller.state['keyCount'] == 12
            assert controller.session.action['steps'][0]['key'] == 'A'
            controller.setLighting(1, 'purple')
            window.setProperty('page', 'Iluminação')
            app.processEvents()
            lighting_button = window.findChild(QObject, 'applyLightingButton')
            assert lighting_button is not None and lighting_button.property('enabled')
            assert QMetaObject.invokeMethod(lighting_button, 'clicked')
            controller.setLighting(1, 'blue')  # Edição durante o envio não se perde.
            wait()
            assert controller.state['lastLighting']['color'] == 'purple'
            assert controller.state['lighting']['color'] == 'blue'
            assert len(backend.leds) == 1
            keys = controller.search('Teclado', '')
            index = next(row['catalogIndex'] for row in keys if row['title'] == 'B')
            controller.select(14)
            controller.assign(index, ['RightCtrl'], False)
            assert controller.state['pendingCount'] == 1
            app.processEvents()
            mapping_button = window.findChild(QObject, 'applyMappingButton')
            assert mapping_button is not None and mapping_button.property('enabled')
            assert QMetaObject.invokeMethod(mapping_button, 'clicked')
            wait()
            assert controller.state['pendingCount'] == 0, controller.message
            controller.session.mark_saved()
            backend.slow = True
            controller.readKeyboard()
            assert backend.entered.wait(2)
            controller.assignDelay(200)
            desired = deepcopy(controller.session.profile)
            backend.release.set()
            wait()
            assert controller.session.profile == desired
            assert 'rascunho foi mantido' in controller.message
            assert all(i != threading.get_ident() for i in backend.thread_ids)
            assert controller.search('Atalhos e símbolos', 'Mac command')
            assert not warnings, warnings
            # Um perfil salvo/fornecido continua sendo rascunho, mesmo dirty=False.
            from littletec.profile import new_profile
            draft = new_profile()
            draft['name'] = 'Perfil salvo que não pode sumir'
            saved_controller = StudioController(profile=draft, service=ConfigurationService(backend, directory))
            try:
                saved_controller.readKeyboard()
                deadline = time.monotonic() + 10
                while saved_controller.state['busy'] and time.monotonic() < deadline:
                    app.processEvents(); time.sleep(0.01)
                assert saved_controller.session.profile == draft
                assert saved_controller.state['connected']
            finally:
                saved_controller.shutdown()
            print('Qt integrado simulado: fila serial, LED direto, encoder, revisão, edições durante I/O e preservação de rascunho passaram. Sem USB.')
        finally:
            backend.release.set()
            controller.shutdown()
            controller.session.mark_saved()
            window.close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
