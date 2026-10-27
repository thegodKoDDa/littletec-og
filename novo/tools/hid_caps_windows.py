"""Consulta metadados HID no Windows com acesso zero e sem I/O de relatórios.

Origem das estruturas/APIs: docs/USB_VALIDACAO.md. Restrito a 1189:8842 MI_00.
"""
import argparse
import ctypes as C
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys


def target_path(path):
    return bool(re.search(r'(?i)^\\\\\?\\hid#vid_1189&pid_8842&mi_00(?:#|&)', path))


def collect():
    if sys.platform != 'win32':
        raise RuntimeError('Execute com Python do Windows.')
    from ctypes import wintypes as W
    class GUID(C.Structure):
        _fields_ = [('Data1', W.DWORD), ('Data2', W.WORD), ('Data3', W.WORD), ('Data4', W.BYTE * 8)]
    class Interface(C.Structure):
        _fields_ = [('cbSize', W.DWORD), ('guid', GUID), ('flags', W.DWORD), ('reserved', C.c_void_p)]
    class Attributes(C.Structure):
        _fields_ = [('Size', W.DWORD), ('VendorID', W.WORD), ('ProductID', W.WORD), ('VersionNumber', W.WORD)]
    class Caps(C.Structure):
        _fields_ = [(name, W.WORD) for name in ('Usage', 'UsagePage', 'InputReportByteLength',
                    'OutputReportByteLength', 'FeatureReportByteLength')] + [('Reserved', W.WORD * 17)] + [
                    (name, W.WORD) for name in ('NumberLinkCollectionNodes', 'NumberInputButtonCaps',
                    'NumberInputValueCaps', 'NumberInputDataIndices', 'NumberOutputButtonCaps',
                    'NumberOutputValueCaps', 'NumberOutputDataIndices', 'NumberFeatureButtonCaps',
                    'NumberFeatureValueCaps', 'NumberFeatureDataIndices')]
    assert C.sizeof(Caps) == 64
    hid = C.WinDLL('hid', use_last_error=True)
    setup = C.WinDLL('setupapi', use_last_error=True)
    kernel = C.WinDLL('kernel32', use_last_error=True)
    def api(dll, name, args, result):
        fn = getattr(dll, name)
        fn.argtypes, fn.restype = args, result
        return fn
    get_guid = api(hid, 'HidD_GetHidGuid', [C.POINTER(GUID)], None)
    get_set = api(setup, 'SetupDiGetClassDevsW', [C.POINTER(GUID), W.LPCWSTR, W.HWND, W.DWORD], W.HANDLE)
    enum = api(setup, 'SetupDiEnumDeviceInterfaces', [W.HANDLE, C.c_void_p, C.POINTER(GUID), W.DWORD, C.POINTER(Interface)], W.BOOL)
    detail = api(setup, 'SetupDiGetDeviceInterfaceDetailW', [W.HANDLE, C.POINTER(Interface), C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p], W.BOOL)
    destroy = api(setup, 'SetupDiDestroyDeviceInfoList', [W.HANDLE], W.BOOL)
    open_file = api(kernel, 'CreateFileW', [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE], W.HANDLE)
    close = api(kernel, 'CloseHandle', [W.HANDLE], W.BOOL)
    attributes = api(hid, 'HidD_GetAttributes', [W.HANDLE, C.POINTER(Attributes)], W.BOOLEAN)
    preparsed = api(hid, 'HidD_GetPreparsedData', [W.HANDLE, C.POINTER(C.c_void_p)], W.BOOLEAN)
    free = api(hid, 'HidD_FreePreparsedData', [C.c_void_p], W.BOOLEAN)
    caps_fn = api(hid, 'HidP_GetCaps', [C.c_void_p, C.POINTER(Caps)], W.LONG)
    guid = GUID()
    get_guid(C.byref(guid))
    info_set = get_set(C.byref(guid), None, None, 0x12)
    invalid = C.c_void_p(-1).value
    if info_set == invalid:
        raise C.WinError(C.get_last_error())
    found = []
    try:
        index = 0
        while True:
            interface = Interface()
            interface.cbSize = C.sizeof(interface)
            if not enum(info_set, None, C.byref(guid), index, C.byref(interface)):
                if C.get_last_error() == 259:
                    break
                raise C.WinError(C.get_last_error())
            index += 1
            size = W.DWORD()
            detail(info_set, C.byref(interface), None, 0, C.byref(size), None)
            if not 6 <= size.value <= 65536:
                raise RuntimeError('Tamanho de interface inválido.')
            buffer = C.create_string_buffer(size.value)
            C.cast(buffer, C.POINTER(W.DWORD))[0] = 8 if C.sizeof(C.c_void_p) == 8 else 6
            if not detail(info_set, C.byref(interface), buffer, size, None, None):
                raise C.WinError(C.get_last_error())
            path = C.wstring_at(C.addressof(buffer) + 4)
            if not target_path(path):
                continue
            item = {'path': path, 'desired_access': 0, 'interface': 'MI_00'}
            found.append(item)
            handle = open_file(path, 0, 3, None, 3, 0, None)
            if handle == invalid:
                item['error'] = str(C.WinError(C.get_last_error()))
                continue
            ppd = C.c_void_p()
            try:
                attrs = Attributes()
                attrs.Size = C.sizeof(attrs)
                if not attributes(handle, C.byref(attrs)):
                    raise C.WinError(C.get_last_error())
                if (attrs.VendorID, attrs.ProductID) != (0x1189, 0x8842):
                    raise RuntimeError('Identidade não corresponde ao caminho selecionado.')
                item.update(vid=f'{attrs.VendorID:04x}', pid=f'{attrs.ProductID:04x}', version=attrs.VersionNumber)
                if not preparsed(handle, C.byref(ppd)):
                    raise C.WinError(C.get_last_error())
                caps = Caps()
                status = caps_fn(ppd, C.byref(caps))
                if status != 0x110000:
                    raise RuntimeError(f'HidP_GetCaps: 0x{status & 0xffffffff:08x}')
                item['caps'] = {name: getattr(caps, name) for name, _ in caps._fields_ if name != 'Reserved'}
                item['reports'] = {}
                for kind, report_type in (('Input', 0), ('Output', 1), ('Feature', 2)):
                    entries = []
                    for category in ('Button', 'Value'):
                        count = getattr(caps, f'Number{kind}{category}Caps')
                        if not count:
                            continue
                        if count > 2048:
                            raise RuntimeError('Quantidade de capacidades excede o limite do diagnóstico.')
                        # HIDP_BUTTON_CAPS e HIDP_VALUE_CAPS: 72 bytes nas ABIs Windows.
                        raw = C.create_string_buffer(count * 72)
                        length = W.WORD(count)
                        fn = api(hid, f'HidP_Get{category}Caps', [C.c_int, C.c_void_p, C.POINTER(W.WORD), C.c_void_p], W.LONG)
                        status = fn(report_type, raw, C.byref(length), ppd)
                        if status != 0x110000 or length.value > count:
                            raise RuntimeError(f'HidP_Get{category}Caps: 0x{status & 0xffffffff:08x}')
                        for i in range(length.value):
                            chunk = raw.raw[i * 72:(i + 1) * 72]
                            entry = {'category': category, 'report_id': chunk[2],
                                     'usage_page': int.from_bytes(chunk[:2], 'little'), 'raw_hex': chunk.hex()}
                            if category == 'Value':
                                entry.update(bit_size=int.from_bytes(chunk[18:20], 'little'),
                                             report_count=int.from_bytes(chunk[20:22], 'little'))
                            entries.append(entry)
                    item['reports'][kind.lower()] = entries
            except (OSError, RuntimeError) as error:
                item['error'] = str(error)
            finally:
                if ppd.value:
                    free(ppd)
                close(handle)
    finally:
        destroy(info_set)
    return {'schema': 1, 'collected_at_utc': datetime.now(timezone.utc).isoformat(),
            'source': 'Windows SetupAPI + HidD metadata + HidP parser',
            'devices': found, 'report_io': False,
            'note': 'Acesso zero. Sem ReadFile/WriteFile/GetFeature/SetFeature ou comandos do fornecedor.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = collect()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['devices'] and not any('error' in d for d in report['devices']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
