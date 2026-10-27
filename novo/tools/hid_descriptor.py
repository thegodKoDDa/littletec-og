"""Resumo offline de tamanhos HID; não autoriza nem realiza comunicação."""
from collections import defaultdict


def summarize(data):
    """Conta bits por tipo/ID, incluindo padding e estado global Push/Pop.

    Itens longos e descritores inconsistentes são recusados para não produzir
    tamanhos aparentemente válidos a partir de um formato não interpretado.
    """
    state = {'size': 0, 'count': 0, 'id': 0, 'page': 0}
    stack = []
    totals = defaultdict(int)
    pages = set()
    offset = 0
    depth = 0
    while offset < len(data):
        start = offset
        prefix = data[offset]
        offset += 1
        if prefix == 0xfe:
            raise ValueError(f'Item longo não suportado no offset {start}')
        size = (0, 1, 2, 4)[prefix & 3]
        if offset + size > len(data):
            raise ValueError(f'Item truncado no offset {start}')
        value = int.from_bytes(data[offset:offset + size], 'little')
        offset += size
        kind, tag = (prefix >> 2) & 3, prefix >> 4
        if kind == 1:
            if tag in (0, 7, 8, 9):
                key = {0: 'page', 7: 'size', 8: 'id', 9: 'count'}[tag]
                if tag == 8 and not 1 <= value <= 255:
                    raise ValueError('Report ID fora do intervalo 1..255')
                state[key] = value
                if tag == 0:
                    pages.add(value)
            elif tag == 10:
                stack.append(state.copy())
            elif tag == 11:
                if not stack:
                    raise ValueError('Pop sem Push')
                state = stack.pop()
        elif kind == 0:
            if tag in (8, 9, 11):
                if not state['size'] or not state['count']:
                    raise ValueError('Relatório sem Report Size/Count positivo')
                name = {8: 'input', 9: 'output', 11: 'feature'}[tag]
                totals[(name, state['id'])] += state['size'] * state['count']
            elif tag == 10:
                depth += 1
            elif tag == 12:
                depth -= 1
                if depth < 0:
                    raise ValueError('End Collection sem Collection')
    if stack or depth:
        raise ValueError('Push ou Collection sem fechamento')
    ids = {report_id for _, report_id in totals}
    if 0 in ids and len(ids) > 1:
        raise ValueError('Mistura de relatórios com e sem ID')
    return {
        'usage_pages': [f'0x{p:04x}' for p in sorted(pages)],
        'reports': [
            {'type': kind, 'report_id': report_id, 'payload_bits': bits,
             'payload_bytes': (bits + 7) // 8,
             'wire_bytes': (bits + 7) // 8 + bool(report_id)}
            for (kind, report_id), bits in sorted(totals.items())],
        'note': 'Resumo de tamanhos; não valida identidade, semântica ou transporte.'}
