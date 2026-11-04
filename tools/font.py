"""PAW.EXE font: 12x12 1bpp cells of 18 bytes (MSB-first packed rows), reached by a code-range table.

usage: font.py sheet OUT.png [--start N] [--count N] [--cols 64] [--zoom 2]   render cells, row-major
       font.py table RAM.bin                                                  print the range table from a RAM dump
"""
import argparse
import struct

from PIL import Image

EXE = "work/disc/tree/PAW.EXE"
FONT_RAM = 0x800A36D0  # ctx+0x14EC, logged by tools/debug/glyphs.lua
EXE_BASE = 0x80010010  # PS-X EXE header t_addr; file data starts at 0x800
CELL = 18


def cell_pixels(b):
    """12 rows of 12 bits, MSB first, packed across bytes."""
    bits = int.from_bytes(b, "big")
    return [[bits >> (143 - (y * 12 + x)) & 1 for x in range(12)] for y in range(12)]


def font_offset():
    return FONT_RAM - EXE_BASE + 0x800


def sheet(out, start, count, cols, zoom):
    d = open(EXE, "rb").read()
    off = font_offset() + start * CELL
    rows = count // cols + (count % cols > 0)
    img = Image.new("L", (cols * 13, rows * 13), 90)
    for i in range(count):
        c = d[off + i * CELL:off + (i + 1) * CELL]
        for y, row in enumerate(cell_pixels(c)):
            for x, v in enumerate(row):
                img.putpixel((i % cols * 13 + x, i // cols * 13 + y), 255 if v else 0)
    if zoom > 1:
        img = img.resize((img.width * zoom, img.height * zoom), Image.NEAREST)
    img.save(out)
    print(out, img.size, f"cells {start}..{start + count - 1}, file offset {off:#x}")


def table(ram_path):
    ram = open(ram_path, "rb").read()
    ctx = 0xC44E0
    ptr = struct.unpack_from("<I", ram, ctx + 0x14E8)[0]
    print(f"table at {ptr:08x}, font at {struct.unpack_from('<I', ram, ctx + 0x14EC)[0]:08x}")
    o = ptr & 0x1FFFFF
    for i in range(0x34):
        lo, base = struct.unpack_from("<HH", ram, o + i * 4)
        print(i, f"{lo:04x} base={base}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sheet", "table"])
    ap.add_argument("path")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=1024)
    ap.add_argument("--cols", type=int, default=64)
    ap.add_argument("--zoom", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "sheet":
        sheet(a.path, a.start, a.count, a.cols, a.zoom)
    else:
        table(a.path)
