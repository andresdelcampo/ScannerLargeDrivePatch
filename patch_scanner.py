"""Patch the two signed cluster-to-angle conversions in Scanner 2.13.

Uses only the Python standard library. Leaves Scanner.exe unchanged.
The exact input SHA-256 is required; never apply this to another build.
"""
import argparse
import hashlib
from pathlib import Path
import struct

ORIGINAL_SHA256 = 'ed2231e8f5730ef5adcf80d2c37ab213b92c5bcebbbb1306eba5c6e0bc451620'
PATCH_VERSION = '1.0.0'
DISPLAY_VERSION = ' 2.13 (unofficial patch 1)'
VERSION_DATA_VA = 0x44F380
VERSION_POINTER_OFFSET = 0x47B90
IMAGE_BASE = 0x400000
CODE_RVA = 0x1000
CODE_OFFSET = 0x400
SITES = (0x4492B3, 0x449314)
HELPER_VA = 0x44F370
# push 0; push ecx; fild qword [esp]; add esp,8; ret
# Zero-extend the unsigned cluster count without changing general registers.
HELPER = bytes.fromhex('6a00 51 df2c24 83c408 c3')
OLD_CONVERSION = bytes.fromhex('894c2404 db442404')


def patch(original):
    digest = hashlib.sha256(original).hexdigest()
    if digest != ORIGINAL_SHA256:
        raise ValueError(f'Unsupported input SHA-256: {digest}')
    data = bytearray(original)
    pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
    optional = pe_offset + 24
    section = optional + struct.unpack_from('<H', data, pe_offset + 20)[0]
    assert data[section:section+8] == b'CODE\0\0\0\0'
    assert struct.unpack_from('<III', data, section+8) == (0x4E36C, CODE_RVA, 0x4E400)

    def offset(va):
        return va - IMAGE_BASE - CODE_RVA + CODE_OFFSET

    for va in SITES:
        off = offset(va)
        assert data[off:off+8] == OLD_CONVERSION
        data[off:off+8] = b'\xe8' + struct.pack('<i', HELPER_VA-va-5) + b'\x90'*3
    off = offset(HELPER_VA)
    assert data[off:off+len(HELPER)] == b'\0'*len(HELPER)
    data[off:off+len(HELPER)] = HELPER
    # A Delphi AnsiString constant has a signed reference count (-1), a
    # byte length, its characters, and a trailing NUL. Reuse CODE padding.
    label = DISPLAY_VERSION.encode('ascii')
    version_data = struct.pack('<iI', -1, len(label)) + label + b'\0'
    off = offset(VERSION_DATA_VA)
    assert data[off:off+len(version_data)] == b'\0'*len(version_data)
    data[off:off+len(version_data)] = version_data
    assert struct.unpack_from('<I', data, VERSION_POINTER_OFFSET)[0] == 0x448C94
    struct.pack_into('<I', data, VERSION_POINTER_OFFSET, VERSION_DATA_VA+8)
    # The existing relocation entry for this pointer stays in place.
    # Include the helper in CODE's virtual size. No added sections, imports,
    # relocations or absolute addresses; the existing relocation table is valid.
    struct.pack_into('<I', data, section+8, VERSION_DATA_VA-IMAGE_BASE-CODE_RVA+len(version_data))
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=f'%(prog)s {PATCH_VERSION}')
    parser.add_argument('--input', type=Path, default=Path('Scanner.exe'))
    parser.add_argument('--output', type=Path, default=Path('Scanner-2.13-unofficial1.exe'))
    args = parser.parse_args()
    try:
        output = patch(args.input.read_bytes())
        # Exclusive creation prevents accidentally replacing an existing executable.
        with args.output.open('xb') as stream:
            stream.write(output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'Created {args.output} ({len(output)} bytes)')
    print(f'SHA-256: {hashlib.sha256(output).hexdigest()}')
    print(f'Original preserved: {args.input}')


if __name__ == '__main__':
    main()
