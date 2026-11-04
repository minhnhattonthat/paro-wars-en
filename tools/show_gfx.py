"""show_gfx.py FILE OUT.png [--bpp 4] [--width 256] [--from Y] [--rows N] [--zoom Z] [--clut VRAM:X,Y] [--grid N]: a decoded graphics file as an image, grey by index or with a CLUT read from a VRAM dump.
FILE is a path under work/unpacked or work/disc/tree (LZ decoded when it starts with a known stream, else as is)."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    for base in ("work/unpacked", "work/disc/tree"):
        p = ROOT / base / name
        if p.is_file():
            return p.read_bytes()
    return Path(name).read_bytes()


def indices(data, bpp, width, y0, rows):
    stride = width * bpp // 8
    data = data[y0 * stride:(y0 + rows) * stride]
    if bpp == 8:
        return data
    out = bytearray(len(data) * 2)
    out[0::2] = bytes(b & 15 for b in data)
    out[1::2] = bytes(b >> 4 for b in data)
    return bytes(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file")
    ap.add_argument("out")
    ap.add_argument("--bpp", type=int, default=4)
    ap.add_argument("--width", type=int, default=256)
    ap.add_argument("--from", dest="y0", type=int, default=0)
    ap.add_argument("--rows", type=int, default=0)
    ap.add_argument("--zoom", type=int, default=1)
    ap.add_argument("--clut")
    ap.add_argument("--grid", type=int, default=0)
    a = ap.parse_args()
    data = load(a.file)
    stride = a.width * a.bpp // 8
    total = len(data) // stride
    rows = min(a.rows or total, total - a.y0)
    idx = indices(data, a.bpp, a.width, a.y0, rows)
    if a.clut:
        vram_path, at = a.clut.split(":")
        x, y = map(int, at.split(","))
        vram = Path(vram_path).read_bytes()
        pal = []
        for i in range(1 << a.bpp):
            v = int.from_bytes(vram[(y * 1024 + x + i) * 2:(y * 1024 + x + i) * 2 + 2], "little")
            pal += [(v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3]
    else:
        pal = [c for i in range(1 << a.bpp) for c in (i * 255 // ((1 << a.bpp) - 1),) * 3]
    img = Image.frombytes("P", (a.width, rows), idx)
    img.putpalette(pal + [0] * (768 - len(pal)))
    img = img.convert("RGB")
    if a.zoom > 1:
        img = img.resize((img.width * a.zoom, img.height * a.zoom), Image.NEAREST)
    if a.grid:
        draw = ImageDraw.Draw(img)
        for y in range(0, rows, a.grid):
            draw.line([(0, y * a.zoom), (img.width, y * a.zoom)], fill=(255, 0, 0))
            draw.text((1, y * a.zoom), str(a.y0 + y), fill=(255, 255, 0))
    img.save(a.out)
    print(f"{a.file}: {len(data)} bytes, {total} rows at {a.width}x{a.bpp}bpp; showing {rows} from {a.y0}")


if __name__ == "__main__":
    main()
