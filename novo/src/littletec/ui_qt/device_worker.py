"""Único executor de I/O da interface; slots vivem na QThread de trabalho."""
from PySide6.QtCore import QObject, Signal, Slot


class DeviceWorker(QObject):
    completed = Signal(object)

    def __init__(self, service=None):
        super().__init__()
        self.service = service

    @Slot(object)
    def execute(self, request):
        try:
            if self.service is None:
                from ..configuration_service import ConfigurationService
                self.service = ConfigurationService()
            operation = request['operation']
            if operation == 'read':
                snapshot = self.service.read()
                result = {'snapshot': snapshot, 'lastLighting': [self.service.last_led(snapshot, i) for i in (1, 2, 3)]}
            elif operation == 'led':
                result = self.service.apply_led(request['mode'], request['color'], request['layer'], request.get('snapshot'))
            elif operation == 'led_all':
                result = self.service.apply_led_all_layers(request['mode'], request['color'], request.get('snapshot'))
            elif operation == 'apply':
                result = self.service.apply_keys(request['snapshot'], request['profile'])
            elif operation == 'diagnose':
                from ..diagnostics import collect_report
                result = {'diagnostic': collect_report()}
            else:
                raise ValueError('Operação desconhecida.')
            self.completed.emit({'operation': operation, 'result': result})
        except Exception as error:
            self.completed.emit({'operation': request['operation'], 'error': str(error)})
