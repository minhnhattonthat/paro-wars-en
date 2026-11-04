"""RE helper for PAW.EXE and overlays: capstone disassembly, lui/addiu xrefs, syscall search.

usage: re.py dis FILE ADDR [COUNT] [--base HEX]    disassemble (base defaults to the PS-X EXE header's load address)
       re.py xref FILE ADDR [--base HEX]           lui+addiu/ori/lw/... pairs and raw 32-bit words that reach ADDR
       re.py calls FILE ADDR [--base HEX]          every jal/j to ADDR
       re.py bios FILE [--base HEX]                A0/B0/C0 BIOS call stubs, with the function number
"""
import argparse
import re
import struct

import capstone


def load(path, base):
    d = open(path, "rb").read()
    if d[:8] == b"PS-X EXE":
        return d[0x800:], struct.unpack_from("<I", d, 0x18)[0]
    return d, base or 0


def code(data, base):
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    return md.disasm(data, base)


def dis(data, base, addr, count):
    off = addr - base
    for i in code(data[off:off + count * 4], addr):
        print(f"{i.address:08x}  {i.mnemonic} {i.op_str}")


def xref(data, base, addr):
    """Every aligned word that is the address itself, and every lui hi / low-half pair within 8 instructions."""
    hi = (addr + 0x8000) >> 16 & 0xffff
    lo = addr & 0xffff
    n = len(data) // 4
    words = struct.unpack_from(f"<{n}I", data)
    for i, w in enumerate(words):
        if w == addr:
            print(f"{base + i * 4:08x}  .word {addr:08x}")
        if w >> 26 == 0x0f and w & 0xffff == hi:
            reg = w >> 16 & 31
            for j in range(i + 1, min(n, i + 9)):
                x = words[j]
                op = x >> 26
                if op and op != 0x0f and x >> 21 & 31 == reg and x & 0xffff == lo:
                    print(f"{base + i * 4:08x}  lui ${reg} .. {base + j * 4:08x} op={op:#x}")
                    break


def calls(data, base, addr):
    """Every jal/j to addr."""
    n = len(data) // 4
    for i, w in enumerate(struct.unpack_from(f"<{n}I", data)):
        if w >> 26 in (2, 3) and (w & 0x3FFFFFF) << 2 == addr & 0x0FFFFFFF:
            print(f"{base + i * 4:08x}  {'jal' if w >> 26 == 3 else 'j'} {addr:08x}")


def bios(data, base):
    """Stub form: addiu t2,r0,0xA0|B0|C0; jr t2; addiu t1,r0,N."""
    for m in re.finditer(rb"[\xa0\xb0\xc0]\x00\x0a\x24\x08\x00\x40\x01(.)\x00\x09\x24", data, re.S):
        if m.start() % 4 == 0:
            print(f"{base + m.start():08x}  {data[m.start()]:02X}:{m.group(1)[0]:02X}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["dis", "xref", "calls", "bios"])
    ap.add_argument("file")
    ap.add_argument("addr", nargs="?", type=lambda s: int(s, 16))
    ap.add_argument("count", nargs="?", type=int, default=40)
    ap.add_argument("--base", type=lambda s: int(s, 16))
    a = ap.parse_args()
    data, base = load(a.file, a.base)
    if a.cmd == "dis":
        dis(data, base, a.addr, a.count)
    elif a.cmd == "xref":
        xref(data, base, a.addr)
    elif a.cmd == "calls":
        calls(data, base, a.addr)
    else:
        bios(data, base)
