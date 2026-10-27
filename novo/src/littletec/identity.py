"""Experimento restrito de identificação, separado de perfis/configuração.

Pedido exato observado em identity-original-02.json; docs/USB_VALIDACAO.md.
Os bytes após o prefixo são dados de pilha do original, não formato especificado.
"""
import re

OBSERVED_REQUEST = bytes.fromhex(
    '03fbfbfb34097cd082002cd08200ccd25a0130d082007cd082000000dc00b41c4a00'
    '4cd08200983b390a88d0820070f51e6298da11620c800000888f3509ffffff')


def validate_capabilities(device):
    if device.get('error') or (device.get('vid'), device.get('pid'), device.get('interface')) != ('1189', '8842', 'MI_00'):
        raise ValueError('Identidade/interface HID não validada.')
    if not re.match(r'(?i)^\\\\\?\\hid#vid_1189&pid_8842&mi_00(?:#|&)', device.get('path', '')):
        raise ValueError('Caminho não corresponde à interface de configuração esperada.')
    caps = device.get('caps', {})
    expected = {'Usage': 1, 'UsagePage': 0xff00, 'InputReportByteLength': 65,
                'OutputReportByteLength': 65, 'FeatureReportByteLength': 0}
    if any(caps.get(key) != value for key, value in expected.items()):
        raise ValueError('Capacidades HID diferentes das observadas.')
    for kind in ('input', 'output'):
        entries = device.get('reports', {}).get(kind, [])
        if len(entries) != 1 or any(entries[0].get(key) != value for key, value in
                                    {'report_id': 3, 'bit_size': 8, 'report_count': 64}.items()):
            raise ValueError('Formato de relatório diferente do validado.')


def parse_response(response):
    if len(response) != 65:
        raise ValueError(f'Resposta incompleta: {len(response)} bytes, esperados 65.')
    if response[:2] != b'\x03\xfb':
        raise ValueError('Report ID ou prefixo de identificação inesperado.')
    # Interpretação estática agora confrontada com a identificação original.
    keys, encoders, variant = response[2:5]
    if not 1 <= keys + encoders * 3 <= 60 or encoders > 4:
        raise ValueError('Quantidades de identificação fora dos limites investigados.')
    return {'key_count': keys, 'encoder_count': encoders, 'variant': variant,
            'note': 'Identificação, não leitura da configuração das teclas.'}


def query(device, capabilities, request, timeout_ms=1000):
    """Usa handle HID já aberto/confirmado pelo chamador. Fecha em qualquer caso."""
    try:
        validate_capabilities(capabilities)
        if request != OBSERVED_REQUEST:
            raise ValueError('Pedido diferente da identificação completa documentada.')
        if type(timeout_ms) is not int or not 1 <= timeout_ms <= 2000:
            raise ValueError('Timeout deve estar entre 1 e 2000 ms.')
        written = device.write(request)
        if written != len(request):
            raise OSError(f'Escrita incompleta do pedido: {written}/{len(request)}.')
        response = bytes(device.read(65, timeout_ms))
        if not response:
            raise TimeoutError('Teclado não respondeu à identificação no prazo.')
        return response, parse_response(response)
    finally:
        device.close()
