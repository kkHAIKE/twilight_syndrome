from ini import Ini
import mmap
import struct

dec2code = [
    0x00, 0x00, 0x81, 0x90, 0x1E, 0x00, 0x02, 0x24, 0x12, 0x00, 0x22, 0x10, 0x00, 0x00, 0x00, 0x00,
    0x7E, 0x00, 0x82, 0x24, 0x40, 0x00, 0x83, 0x24, 0x00, 0x00, 0x61, 0x90, 0x03, 0x00, 0x25, 0x30,
    0x80, 0x30, 0x01, 0x00, 0x30, 0x00, 0xC6, 0x30, 0x25, 0x28, 0xC5, 0x00, 0x00, 0x09, 0x26, 0x7C,
    0x82, 0x08, 0x01, 0x00, 0x30, 0x00, 0x21, 0x30, 0x25, 0x08, 0xC1, 0x00, 0x01, 0x00, 0x41, 0xA0,
    0x00, 0x00, 0x45, 0xA0, 0xFE, 0xFF, 0x42, 0x24, 0x2B, 0x08, 0x44, 0x00, 0xF2, 0xFF, 0x20, 0x10,
    0xFF, 0xFF, 0x63, 0x24, 0x08, 0x00, 0xE0, 0x03, 0x00, 0x00, 0x00, 0x00
]

# srl     $a0, 8
# li      $at, 0x8001A200
# addu    $a0, $at
# jal     rlcdecode
# move    $a0, $s0
codebegin = [
    0x02, 0x22, 0x04, 0x00, 0x01, 0x80, 0x01, 0x3C, 0x00, 0xA2, 0x21, 0x34, 0x21, 0x20, 0x81, 0x00,
]

def asm_la_s6(addr: int) -> bytes:
    if addr & (2**15) != 0:
        addr = addr + 2**16
    # 09 80 16 3C    lui   $s6, 0x8009
    # 24 C8 D6 26    addiu $s6, $s6, -0x37dc
    return struct.pack('<4H', addr >> 16, 0x3C16, addr & 0xFFFF, 0x26d6)

def asm_la_at(addr: int) -> bytes:
    if addr & (2**15) != 0:
        addr = addr + 2**16
    # 09 80 01 3C    lui   $at, 0x8009
    # 24 C8 21 24    addiu $at, $at, -0x37dc
    return struct.pack('<4H', addr >> 16, 0x3C01, addr & 0xFFFF, 0x2421)

def _patch(ini: Ini, mm: mmap.mmap):
    pos0 = mm.find(asm_la_s6(ini.fonttbl + 4))
    assert pos0 != -1
    mm.seek(pos0)
    mm.write(asm_la_s6(ini.fonttbl))

    # FF 0F 63 30    andi $v1, $v1, 0xfff
    # C0 10 03 00    sll  $v0, $v1, 3
    # 21 10 56 00    addu $v0, $v0, $s6
    # 00 00 42 8C    lw   $v0, ($v0)
    p = mm.find(b'\xFF\x0F\x63\x30\xc0\x10\x03\x00\x21\x10\x56\x00\x00\x00\x42\x8c')
    assert p != -1 and p < pos0 + 0x2000
    mm.seek(p)
    mm.write(b'\xFF\x0F\x63\x30\x80\x10\x03\x00\x21\x10\x56\x00\x00\x00\x42\x80')

    # FF FF E7 30    andi $a3, $a3, 0xffff
    # C0 38 07 00    sll  $a3, $a3, 3
    p = mm.find(b'\xFF\xFF\xE7\x30\xc0\x38\x07\x00')
    assert p != -1 and p < pos0 + 0x2000
    mm.seek(p)
    mm.write(b'\xFF\xFF\xE7\x30\x80\x38\x07\x00')

    # 21 08 27 00    addu  $at, $at, $a3
    # 00 00 22 8C    lw    $v0, ($at)
    p = mm.find(asm_la_at(ini.fonttbl + 4) + b'\x21\x08\x27\x00\x00\x00\x22\x8c')
    assert p != -1 and p < pos0 + 0x2000
    mm.seek(p)
    mm.write(asm_la_at(ini.fonttbl) + b'\x21\x08\x27\x00\x00\x00\x22\x80')

    # FF FF A2 30    andi $v0, $a1, 0xffff
    # C0 10 02 00    sll  $v0, $v0, 3
    p = mm.find(b'\xFF\xFF\xA2\x30\xc0\x10\x02\x00')
    assert p != -1 and p < pos0 + 0x2000
    mm.seek(p)
    mm.write(b'\xFF\xFF\xA2\x30\x80\x10\x02\x00')

    p += 0x14
    mm.seek(p)
    # lw      $a0, 0($at)
    assert mm.read(4) == b'\x00\x00\x24\x8C'
    jal_p = mm.tell()
    jal_rlcdecode = mm.read(4)

    tbl_p = ini.fonttbl - ini.base
    mm.seek(tbl_p)
    tbl_first = mm.read(16)
    mm.seek(0)
    p = mm.find(tbl_first)
    mm.seek(p)
    assert p != tbl_p and mm.read(16) == tbl_first
    mm.seek(-16, 1)
    mm.write(bytes(codebegin) + jal_rlcdecode + b'\x25\x28\x00\x02' + bytes(dec2code))

    code_addr = ini.base + p
    mm.seek(jal_p)
    mm.write(struct.pack('<I', 0x0c000000 | ((code_addr - 0x80000000) >> 2)))

def patch(ini: Ini):
    # ini.dstexe
    with open(ini.dstexe, 'rb+') as f:
        with mmap.mmap(f.fileno(), 0) as mm:
            _patch(ini, mm)
