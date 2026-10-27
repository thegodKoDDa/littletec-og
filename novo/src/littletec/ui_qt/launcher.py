"""Aplicativo Qt integrado. Modos de verificação nunca fazem gravação automática."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback


def main():
    try:
        os.environ['QML_DISABLE_DISK_CACHE'] = '1'
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--profile', type=Path)
        parser.add_argument('--offline', action='store_true', help='Não conectar automaticamente.')
        parser.add_argument('--read-usb', action='store_true', help='Ler pelo worker e fechar após captura, sem gravar.')
        parser.add_argument('--screenshot', type=Path)
        parser.add_argument('--result', type=Path)
        parser.add_argument('--page', choices=('Mapeamento', 'Iluminação', 'Perfis', 'Diagnóstico'), default='Mapeamento')
        args = parser.parse_args()
        from PySide6.QtCore import QTimer, QUrl
        from PySide6.QtQml import QQmlApplicationEngine
        from PySide6.QtQuickControls2 import QQuickStyle
        from PySide6.QtWidgets import QApplication
        from ..profile import load
        from .controller import StudioController
        QQuickStyle.setStyle('Basic')
        app = QApplication([sys.argv[0]])
        app.setApplicationName('LittleTec Studio')
        controller = StudioController(load(args.profile) if args.profile else None)
        engine = QQmlApplicationEngine()
        errors = []
        engine.warnings.connect(lambda messages: errors.extend(str(m) for m in messages))
        engine.setInitialProperties({'studio': controller})
        qml = (Path(sys._MEIPASS) / 'littletec/ui_qt/qml/Main.qml' if getattr(sys, 'frozen', False)
               else Path(__file__).parent / 'qml/Main.qml')
        engine.load(QUrl.fromLocalFile(str(qml)))
        if not engine.rootObjects():
            msg = 'Erro ao abrir a interface Qt:\n' + '\n'.join(errors)
            try:
                (Path(sys.executable).parent / 'startup-error.log').write_text(msg, encoding='utf-8')
            except OSError:
                pass
            raise SystemExit(msg)
        window = engine.rootObjects()[0]
        window.setProperty('page', args.page)
        app.aboutToQuit.connect(controller.shutdown)
        def finish():
            ok = not errors and (not args.read_usb or controller._snapshot is not None and controller.state['connection'] == 'conectado')
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                ok = window.grabWindow().save(str(args.screenshot)) and ok
            if args.result:
                args.result.parent.mkdir(parents=True, exist_ok=True)
                args.result.write_text(json.dumps({'ok': ok, 'state': controller.state, 'message': controller.message,
                                                   'detail': controller.detail, 'qml_errors': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
            if errors:
                print('\n'.join(errors), file=sys.stderr)
            controller.session.mark_saved()
            app.exit(0 if ok else 1)
        if args.read_usb:
            controller.readKeyboard()
            def wait_read():
                if controller.state['busy']:
                    QTimer.singleShot(100, wait_read)
                else:
                    QTimer.singleShot(500, finish)
            QTimer.singleShot(100, wait_read)
        elif args.screenshot:
            QTimer.singleShot(1200, finish)
        elif not args.offline:
            QTimer.singleShot(300, controller.readKeyboard)
        return app.exec()
    except Exception:
        try:
            log_dir = Path(sys._MEIPASS).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[3]
            (log_dir / 'startup-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        except OSError:
            pass
        raise
