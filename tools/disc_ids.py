"""Recon: PAW.EXE's file-id table, and any {ram, size, lba} table at a given address, named from the ISO directory.

usage: disc_ids.py BIN TREE                     the id table used by the loader 0x8002A13C (docs/re/flow.md)
       disc_ids.py BIN TREE FILE BASE ADDR N    N records at ADDR in FILE loaded at BASE (hex), e.g. an overlay's story tables
"""
import struct
import sys

from disc_tables import walk

ID_TABLE = 0x8009C34C


def rec(iso, data, base, addr):
    ram, size, lba = struct.unpack_from("<III", data, addr - base)
    name = iso.get(lba, ("?",))[0]
    return f"{addr:08x}\t{size:#x}\t{lba}\t{ram:08x}\t{name}"


def main():
    binp, tree = sys.argv[1:3]
    with open(binp, "rb") as f:
        f.seek(16 * 2352 + 24 + 156)
        root = f.read(34)
        iso = walk(f, struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0])
    if len(sys.argv) > 3:
        data = open(sys.argv[3], "rb").read()
        base, addr, n = int(sys.argv[4], 16), int(sys.argv[5], 16), int(sys.argv[6])
        for i in range(n):
            print(i, rec(iso, data, base, addr + i * 12), sep="\t")
        return
    exe = open(f"{tree}/PAW.EXE", "rb").read()[0x800:]
    base = 0x80010010
    for i in range(0x23):  # 0x23 words; id 1 is null, id 0xfff is a separate record in the loader
        p = struct.unpack_from("<I", exe, ID_TABLE - base + i * 4)[0]
        print(f"{i:#x}", rec(iso, exe, base, p) if p else "-", sep="\t")


if __name__ == "__main__":
    main()
