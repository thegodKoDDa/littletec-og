"""Leitor bruto experimental: somente os pedidos observados no original.

Origem completa e limites em docs/USB_VALIDACAO.md. Não escreve configuração.
"""
import time
from .identity import validate_capabilities

_TAIL = '0760cc820020cd82007cf20269000000004d00d40720cd82006d010000230100000000000010cd8200a0cd8200c884c80718ecd40740cd8200c7b66f'
OBSERVED_READ_REQUESTS = tuple(bytes.fromhex(f'03fa0f03{layer:02x}' + _TAIL) for layer in (1, 2, 3))


def read_configuration(device, capabilities, requests=OBSERVED_READ_REQUESTS, timeout_ms=1000, on_packet=None, allow_encoder_aliases=False):
    """Obtém os 72 relatórios do fluxo original e fecha o dispositivo em qualquer caso."""
    try:
        validate_capabilities(capabilities)
        requests = tuple(requests)
        if requests != OBSERVED_READ_REQUESTS:
            raise ValueError('Pedidos diferentes dos três pedidos de leitura documentados.')
        if type(timeout_ms) is not int or not 1 <= timeout_ms <= 2000:
            raise ValueError('Timeout deve estar entre 1 e 2000 ms.')
        deadline = time.monotonic() + 15
        layers = []
        for layer, request in enumerate(requests, 1):
            if time.monotonic() >= deadline:
                raise TimeoutError('Prazo total de leitura excedido.')
            written = device.write(request)
            if written != 65:
                raise OSError(f'Pedido da camada {layer} incompleto: {written}/65.')
            packets, indexes = [], set()
            for arrival in range(1, 25):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Prazo total de leitura excedido.')
                response = bytes(device.read(65, min(timeout_ms, max(1, int(remaining * 1000)))))
                # Registra também resposta inválida, para preservar evidência da falha.
                if on_packet:
                    on_packet(layer, arrival, response)
                if not response:
                    raise TimeoutError(f'Timeout na camada {layer}, relatório {arrival}.')
                if len(response) != 65 or response[:2] != b'\x03\xfa':
                    raise ValueError('Comprimento ou prefixo de configuração inválido.')
                encoder_alias = False
                if allow_encoder_aliases and arrival >= 16:
                    start = 16 + ((arrival - 16) // 3) * 3
                    factory = start + 2 - ((arrival - 16) % 3)
                    encoder_alias = response[2] in (arrival, factory)
                    if not encoder_alias:
                        raise ValueError('ID de encoder fora do slot do fluxo validado.')
                if (response[3] != layer or not 1 <= response[2] <= 24
                        or (response[2] in indexes and not encoder_alias)
                        or (allow_encoder_aliases and arrival <= 15 and response[2] > 15)):
                    raise ValueError('Camada/índice inválido ou relatório duplicado.')
                indexes.add(response[2])
                packets.append(response)
            if not allow_encoder_aliases and indexes != set(range(1, 25)):
                raise ValueError('Conjunto de registros incompleto.')
            layers.append(packets)
        return layers
    finally:
        device.close()
