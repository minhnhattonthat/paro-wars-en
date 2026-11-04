"""Render a PS1 VRAM dump (L.dump_ppu; 1024x512 16-bit): vram.py DUMP.vram.bin OUT.png [--bpp 16|8|4] [--clut X,Y] [--rect X,Y,W,H] [--zoom N]
x and w are in VRAM halfwords, as the GPU counts them. A pixel-format view needs --clut, or shows grey by index. Find where text sits on a 16 bpp view, then read the page at 4 or 8."""
import argparse

from PIL import Image


def pixels(vram, bpp, clut, rect):
    x0, y0, w, h = rect
    out = Image.new("RGB", (w * 16 // bpp, h))
    px = out.load()
    pal = None
    if clut:
        pal = [int.from_bytes(vram[(clut[1] * 1024 + clut[0] + i) * 2:(clut[1] * 1024 + clut[0] + i) * 2 + 2], "little") for i in range(1 << bpp)]

    def rgb(v):
        return (v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3

    for y in range(h):
        row = vram[((y0 + y) * 1024 + x0) * 2:((y0 + y) * 1024 + x0 + w) * 2]
        for x in range(w * 16 // bpp):
            if bpp == 16:
                px[x, y] = rgb(int.from_bytes(row[x * 2:x * 2 + 2], "little"))
                continue
            i = row[x] if bpp == 8 else (row[x // 2] >> 4 if x & 1 else row[x // 2] & 15)
            px[x, y] = rgb(pal[i]) if pal else (i if bpp == 8 else i * 17,) * 3
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump")
    ap.add_argument("out")
    ap.add_argument("--bpp", type=int, default=16)
    ap.add_argument("--clut")
    ap.add_argument("--rect", default="0,0,1024,512")
    ap.add_argument("--zoom", type=int, default=1)
    a = ap.parse_args()
    img = pixels(open(a.dump, "rb").read(), a.bpp, tuple(map(int, a.clut.split(","))) if a.clut else None, tuple(map(int, a.rect.split(","))))
    if a.zoom > 1:
        img = img.resize((img.width * a.zoom, img.height * a.zoom), Image.NEAREST)
    img.save(a.out)


if __name__ == "__main__":
    main()
