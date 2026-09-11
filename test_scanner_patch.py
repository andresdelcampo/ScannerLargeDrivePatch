"""Execute the original and patched x86 chart routine with synthetic disk sizes.

Requires pefile and unicorn (available in the project's .tools directory).
No real disk files, drive settings, or running processes are modified.
"""
import math
import argparse
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).parent / '.tools'))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_EBX
from patch_scanner import patch, DISPLAY_VERSION, VERSION_DATA_VA, VERSION_POINTER_OFFSET


def angle(binary, count, root_count, total_count, free_count, cluster_bytes, focused, relocated=False):
    pe = pefile.PE(data=binary)
    base = 0x600000 if relocated else 0x400000
    if relocated:
        pe.relocate_image(base)
    delta = base - 0x400000
    emu = Uc(UC_ARCH_X86, UC_MODE_32)
    emu.mem_map(base, 0x80000)
    emu.mem_write(base, pe.get_memory_mapped_image())
    stack, objects, stub = 0x1000000, 0x1100000, 0x1200000
    for address in (stack, objects, stub):
        emu.mem_map(address, 0x10000)

    def u32(address, value):
        emu.mem_write(address, struct.pack('<I', value))

    u32(0x451D14+delta, objects if focused else 0)
    u32(objects+8, root_count)
    u32(0x45184C+delta, objects+0x100)
    u32(objects+0x140, objects)
    u32(0x451AA0+delta, total_count)
    u32(0x451A38+delta, free_count)
    u32(0x4518B4+delta, cluster_bytes)
    emu.mem_write(0x451A30+delta, struct.pack('<Q', total_count*cluster_bytes))
    esp = stack+0x8000
    u32(esp, stub)
    emu.reg_write(UC_X86_REG_ESP, esp)
    emu.reg_write(UC_X86_REG_ECX, count)
    emu.reg_write(UC_X86_REG_EDX, 0)
    emu.reg_write(UC_X86_REG_EBX, 0x12345678)
    # Pop the returned x87 result into a float for inspection.
    emu.mem_write(stub, b'\xd9\x1d'+struct.pack('<I', stub+0x100))
    emu.emu_start(0x449298+delta, stub+6, count=1000)
    assert emu.reg_read(UC_X86_REG_ESP) == esp+4
    assert emu.reg_read(UC_X86_REG_EBX) == 0x12345678
    return struct.unpack('<f', emu.mem_read(stub+0x100,4))[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('Scanner.exe'))
    args = parser.parse_args()
    ORIGINAL = args.input.read_bytes()
    PATCHED = patch(ORIGINAL)
    cases = 0
    for relocated in (False, True):
        for focused in (False, True):
            for cluster in (512, 1024, 4096, 65536):
                for count in (0, 1, 2**30, 2**31-1, 2**31, 2**31+1, 0xFFFFFFFF):
                    total, free, root = 0xFFFFFFFF, 1234567, 0xFFFFFFFF
                    before = angle(ORIGINAL,count,root,total,free,cluster,focused,relocated)
                    after = angle(PATCHED,count,root,total,free,cluster,focused,relocated)
                    expected = math.tau*count/root
                    if not focused:
                        expected *= (total-free)/total
                    assert math.isclose(after, expected, rel_tol=2e-7, abs_tol=1e-12), (count,after,expected)
                    if count < 2**31:
                        assert before == after, (count,before,after)
                    else:
                        assert before < 0 and after > 0, (count,before,after)
                    cases += 1
            # Zero-size roots / totals retain the original zero result.
            for root, total in ((0,0), (0,100), (100,0)):
                before = angle(ORIGINAL,0,root,total,0,4096,focused,relocated)
                after = angle(PATCHED,0,root,total,0,4096,focused,relocated)
                assert before == after == 0
                cases += 1
    # Fixed sample based on the attached 12 TB volume's Windows counters.
    total, free = 2929716735, 450182102
    used = total-free
    for focused in (False, True):
        before = angle(ORIGINAL,used,used,total,free,4096,focused)
        after = angle(PATCHED,used,used,total,free,4096,focused)
        print(f'12 TB sample, focused={focused}: original={before:.6f}, patched={after:.6f} radians')
    assert len(ORIGINAL) == len(PATCHED)
    pe = pefile.PE(data=PATCHED)
    assert pe.sections[0].Misc_VirtualSize == VERSION_DATA_VA-0x401000+9+len(DISPLAY_VERSION)
    pointer = struct.unpack_from('<I', PATCHED, VERSION_POINTER_OFFSET)[0]
    assert pe.get_string_at_rva(pointer-0x400000).decode('ascii') == DISPLAY_VERSION
    assert struct.unpack('<iI', pe.get_data(pointer-0x400000-8,8)) == (-1,len(DISPLAY_VERSION))
    assert any(e.rva == pe.get_rva_from_offset(VERSION_POINTER_OFFSET) and e.type == 3
               for block in pe.DIRECTORY_ENTRY_BASERELOC for e in block.entries)
    pe.relocate_image(0x600000)
    pointer_rva = pe.get_rva_from_offset(VERSION_POINTER_OFFSET)
    relocated_pointer = struct.unpack('<I', pe.get_data(pointer_rva,4))[0]
    assert relocated_pointer == pointer+0x200000
    assert pe.get_string_at_rva(relocated_pointer-0x600000).decode('ascii') == DISPLAY_VERSION
    for invalid in (b'', PATCHED, ORIGINAL[:-1], b'X'+ORIGINAL[1:]):
        try:
            patch(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Unsupported input accepted')
    print(f'PASS: {cases} emulated x86 regression cases, including relocated loading.')
    print('The 32-bit cluster storage limit still applies; this is not a 64-bit storage rewrite.')


if __name__ == '__main__':
    main()
