"""Ensaio aprovado de uma tecla, com restauração obrigatória e releitura integral."""
from .protocol import COMMIT_PACKET, decode_record, encode_record, index_layers, packet_for_record

A = {'type': 'keyboard', 'steps': [{'key': 'A', 'modifiers': []}]}
F24 = {'type': 'keyboard', 'steps': [{'key': 'F24', 'modifiers': []}]}


def records(snapshot):
    return index_layers(snapshot['layers'])


def signature(snapshot):
    return tuple(tuple(sorted(layer.items())) for layer in records(snapshot))


def run_trial(backend, approved=False):
    if approved is not True:
        raise PermissionError('Ensaio físico requer aprovação explícita.')
    baseline = backend.read()
    before = records(baseline)[0][1]
    if decode_record(before) != A:
        raise ValueError('Tecla 1/camada 1 não é A; revisar o ensaio em vez de alterar outra configuração.')
    after = encode_record(F24, 1, 1)
    before_packet, after_packet = packet_for_record(before), packet_for_record(after)
    backend.allow_packets({before_packet, after_packet, COMMIT_PACKET})
    report = {'source_backup': baseline['folder'], 'noop_verified': False,
              'change_verified': False, 'restoration_verified': False, 'complete': False,
              'physical_keypress_verified': False, 'persistence_after_reconnect_verified': False,
              'before_packet_hex': before_packet.hex(), 'test_packet_hex': after_packet.hex(),
              'commit_packet_hex': COMMIT_PACKET.hex(), 'identity': baseline['identity'],
              'device_path': baseline['manifest']['capabilities']['devices'][0]['path']}
    attempted = False
    try:
        attempted = True
        backend.send([before_packet, COMMIT_PACKET])
        noop = backend.read()
        if signature(noop) != signature(baseline):
            raise RuntimeError('O reenvio do valor atual não preservou os registros; alteração temporária abortada.')
        report.update(noop_verified=True, noop_backup=noop['folder'])
        backend.send([after_packet, COMMIT_PACKET])
        changed = backend.read()
        expected = [dict(layer) for layer in records(baseline)]
        expected[0][1] = after
        if records(changed) != expected:
            raise RuntimeError('Releitura não corresponde exclusivamente a F24 na tecla 1/camada 1.')
        report.update(change_verified=True, changed_backup=changed['folder'])
    except Exception as error:
        report['error'] = str(error)
    finally:
        if attempted:
            try:
                backend.send([before_packet, COMMIT_PACKET])
                restored = backend.read()
                report['restored_backup'] = restored['folder']
                if signature(restored) != signature(baseline):
                    raise RuntimeError('A releitura final diverge da cópia inicial.')
                report['restoration_verified'] = True
            except Exception as error:
                report['restoration_error'] = str(error)
    report['complete'] = report['noop_verified'] and report['change_verified'] and report['restoration_verified']
    return report
