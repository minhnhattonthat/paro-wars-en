"""Recon: render a span of a binary as 1bpp/4bpp/8bpp/16bpp pixels, to spot fonts and images by eye.

usage: bitmap.py FILE OUT.png --bpp 1 --width 16 [--offset HEX] [--size HEX] [--cols N] [--cell-h H] [--msb] [--zoom Z] [--clut FILE:OFF]
With --cell-h, the data is split into cells WIDTH x H laid out --cols per row (font view); otherwise one image WIDTH wide."""
import argparse
import struct

from PIL import Image


def decode(data, width, bpp, msb, clut):
    """Return (pixels as RGB list, height) for one row-major span."""
    px = []
    if bpp == 1:
        stride = (width + 7) // 8
        for o in range(0, len(data) - stride + 1, stride):
            for x in range(width):
                b = data[o + x // 8]
                on = b >> (7 - x % 8) & 1 if msb else b >> (x % 8) & 1
                px.append((255, 255, 255) if on else (0, 0, 0))
        return px, len(px) // width
    if bpp == 16:
        for o in range(0, len(data) - 1, 2):
            v = struct.unpack_from("<H", data, o)[0]
            px.append(((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8))
        return px, len(px) // width
    vals = []
    if bpp == 4:
        for b in data:
            vals += [b & 15, b >> 4]
    else:
        vals = list(data)
    for v in vals:
        if clut:
            c = clut[v % len(clut)]
            px.append(((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8))
        else:
            g = v * 17 if bpp == 4 else v
            px.append((g, g, g))
    return px, len(px) // width


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("out")
    ap.add_argument("--bpp", type=int, default=1, choices=[1, 4, 8, 16])
    ap.add_argument("--width", type=int, default=16)
    ap.add_argument("--offset", type=lambda s: int(s, 16), default=0)
    ap.add_argument("--size", type=lambda s: int(s, 16))
    ap.add_argument("--cols", type=int, default=40)
    ap.add_argument("--cell-h", type=int)
    ap.add_argument("--msb", action="store_true")
    ap.add_argument("--zoom", type=int, default=1)
    ap.add_argument("--clut", help="FILE:HEXOFF, 256 15-bit entries (16 for 4bpp)")
    a = ap.parse_args()
    data = open(a.file, "rb").read()[a.offset:]
    if a.size:
        data = data[:a.size]
    clut = None
    if a.clut:
        path, off = a.clut.rsplit(":", 1)
        raw = open(path, "rb").read()[int(off, 16):]
        n = 16 if a.bpp == 4 else 256
        clut = list(struct.unpack_from(f"<{n}H", raw))
    if a.cell_h:
        stride = (a.width + 7) // 8 if a.bpp == 1 else a.width * a.bpp // 8
        cell = stride * a.cell_h
        n = len(data) // cell
        rows = n // a.cols + 1
        img = Image.new("RGB", (a.cols * (a.width + 1), rows * (a.cell_h + 1)), (70, 0, 70))
        for i in range(n):
            px, h = decode(data[i * cell:(i + 1) * cell], a.width, a.bpp, a.msb, clut)
            t = Image.new("RGB", (a.width, h))
            t.putdata(px)
            img.paste(t, (i % a.cols * (a.width + 1), i // a.cols * (a.cell_h + 1)))
    else:
        px, h = decode(data, a.width, a.bpp, a.msb, clut)
        img = Image.new("RGB", (a.width, h))
        img.putdata(px)
    if a.zoom > 1:
        img = img.resize((img.width * a.zoom, img.height * a.zoom), Image.NEAREST)
    img.save(a.out)
    print(a.out, img.size)


if __name__ == "__main__":
    main()
