"""Smoke da fundação Qt com arquivos locais; não importa serviços USB."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWidgets import QApplication
    from littletec.catalog import KEYS
    from littletec.ui_qt.controller import StudioController
    QQuickStyle.setStyle('Basic')
    app = QApplication([sys.argv[0]])
    controller = StudioController()
    keys = controller.search('Teclado', '')
    assert len(keys) == len(KEYS)
    assert len(controller.search('Multimídia', '')) == 21
    assert len(controller.search('Mouse', '')) == 11
    assert len(controller.search('Atalhos prontos', '')) >= 35
    # Tecla 06 (índice 5): apertar '4' diretamente pelo reconhecimento de teclado
    controller.select(5)
    assert controller.captureKeyEvent(0x34, 0, '4', False, False)
    assert controller.state['positions'][5]['label'] == '4'
    # Tecla 09 (índice 8): apertar Ctrl+C diretamente pelo teclado
    controller.select(8)
    assert controller.captureKeyEvent(0x43, 0x04000000, '', False, False)
    assert controller.state['positions'][8]['label'] == 'Ctrl + C'
    # Tecla 10 (índice 9): apertar Ctrl+V diretamente pelo teclado
    controller.select(9)
    assert controller.captureKeyEvent(0x56, 0x04000000, '', False, False)
    assert controller.state['positions'][9]['label'] == 'Ctrl + V'
    # Faixa anterior, reproduzir/pausar e próxima faixa em qualquer tecla (1, 2, 3)
    controller.select(0)
    controller.assignQuick(0, False)
    assert controller.state['positions'][0]['label'] == 'Faixa anterior'
    controller.select(1)
    controller.assignQuick(1, False)
    assert controller.state['positions'][1]['label'] == 'Reproduzir / pausar'
    controller.select(2)
    controller.assignQuick(2, False)
    assert controller.state['positions'][2]['label'] == 'Próxima faixa'
    # Tonalidade livre e cópia entre camadas
    controller.setCustomTone(1, '#14b8a6')
    assert controller.state['lighting']['color'] == 'cyan'
    assert controller.state['visualColorHex'] == '#14b8a6'
    controller.copyLightingToAllLayers()
    ctrl_c = next(row for row in keys if row['title'] == 'C')
    controller.assign(ctrl_c['catalogIndex'], ['Ctrl'], False)
    assert controller.state['action']['steps'][0] == {'key': 'C', 'modifiers': ['Ctrl']}
    controller.switchLayer(1)
    controller.select(17)
    controller.assignDelay(1234)
    assert controller.state['action'] == {'type': 'delay', 'ms': 1234}
    controller.undo()
    controller.redo()
    controller.setLighting(1, 'cyan')
    assert controller.state['lighting']['color'] == 'cyan'
    # Perfis recuperados por USB têm LED desconhecido: QML deve aceitá-los.
    controller.session.profile['lighting'][controller.session.layer] = {'mode': None, 'color': None}
    controller.changed.emit()
    assert not any(name in sys.modules for name in ('hid', 'littletec.device_service', 'littletec.write_service', 'littletec.lighting_service'))
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda messages: warnings.extend(str(m) for m in messages))
    engine.setInitialProperties({'studio': controller})
    engine.load(QUrl.fromLocalFile(str(ROOT / 'src/littletec/ui_qt/qml/Main.qml')))
    assert engine.rootObjects(), warnings
    window = engine.rootObjects()[0]
    for width, height in ((1040, 720), (1280, 840)):
        window.setWidth(width)
        window.setHeight(height)
        for page in ('Mapeamento', 'Iluminação', 'Perfis', 'Diagnóstico'):
            window.setProperty('page', page)
            app.processEvents()
            assert window.property('page') == page
    window.setProperty('dark', False)
    app.processEvents()
    assert not warnings, warnings
    controller.session.mark_saved()
    window.close()
    print('Prévia Qt: catálogo, edição, camadas, histórico, iluminação local e QML passaram. Sem USB.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
