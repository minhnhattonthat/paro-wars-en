"""Graphics text: every Japanese label drawn into a disc image, redrawn in English (docs/re/graphics.md). The build calls apply(); verify_build allows spans().

A label is a list of rects in one file: the consecutive sprites of one line on screen, so English can run across them whatever the Japanese's split was.
Rects and pages come from tools/debug/prims.py and find_rect.py on a warp's RAM and VRAM dumps.
gfx.py sheet OUT.png [REGEX]: every label drawn, old beside new, without a build."""
import collections
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import credits
import en_text
import gfx_labels
import lzkc

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
LZ_NONE = re.compile(r"DATA/BTLEND/|DATA/MTIT/|DATA/FIX\.BIN|DATA/MCWGRPH\.BIN|DATA/OP|DATA/PUP")  # plain files; everything else here is one LZ stream from offset 0 (work/recon/lz.tsv)


def _font(name, size):
    file, _, variation = name.partition("#")  # "font.ttf#Regular" picks a weight; Archivo is Bold otherwise
    f = ImageFont.truetype(str(FONTS / file), size)
    if file == gfx_labels.TEXT:
        f.set_variation_by_name(variation or "Bold")
    return f


def _small(text):
    """fonts/en12.txt, the font of the game's own text, as rows of 0/1."""
    rows = [[] for _ in range(10)]
    for ch in text:
        glyph = en_text.FONT[ord(ch)]
        w = len(glyph[0])
        for y in range(10):
            rows[y] += [c == "#" for c in glyph[y]] if y < len(glyph) else [False] * w
            rows[y].append(False)
    rows = [r[:-1] for r in rows if r]
    while rows and not any(rows[-1]):
        rows.pop()
    while rows and not any(rows[0]):
        rows.pop(0)
    return rows or [[False]]


def mask(text, style, max_w, max_h):
    """Bitmap of the text with no smoothing: rows of 0/1. Shrinks the font, then squeezes it, until it fits."""
    margin = (style.stroke if style.edge != "none" else 0) + (1 if style.shadow is not None else 0)
    if style.font == gfx_labels.SMALL:
        rows = _small(text)
        if len(rows[0]) + 2 * margin > max_w:
            raise ValueError(f"{text!r} is {len(rows[0])} px, room for {max_w - 2 * margin}")
        return rows
    size = style.size
    while True:
        font = _font(style.font, size)
        x0, y0, x1, y1 = font.getbbox(text)
        if y1 - y0 + 2 * margin <= max_h or size <= 8:
            break
        size -= 1
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    target = int(w * style.wide)
    if target + 2 * margin > max_w:
        target = max_w - 2 * margin
    if target == w:
        img = Image.new("1", (w, h), 0)
        d = ImageDraw.Draw(img)
        d.fontmode = "1"
        d.text((-x0, -y0), text, font=font, fill=1)
    else:
        font4 = _font(style.font, size * 4)
        x0, y0, x1, y1 = font4.getbbox(text)
        big = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(big).text((-x0, -y0), text, font=font4, fill=255)
        img = big.resize((target, h), Image.BILINEAR).point(lambda v: 255 if v >= 110 else 0).convert("1")
    px = img.load()
    return [[bool(px[x, y]) for x in range(img.width)] for y in range(img.height)]


def letter(text, style, w, h, align, palette):
    """A w x h canvas of palette indices, None where the text doesn't touch. `palette(y)` is the ink at a row; edge and shadow come from the style or the sampled original."""
    canvas = [[None] * w for _ in range(h)]
    if not text:
        return canvas
    lines = text.split("|")  # two lines drawn in one rect
    masks = [mask(t, style, w, h // len(lines)) for t in lines]
    total = sum(len(m) for m in masks) + style.lead * (len(masks) - 1)
    top = max(0, (h - total) // 2) + style.down
    margin = style.stroke if style.edge != "none" else 0
    pts = []
    for rows in masks:
        tw = len(rows[0])
        left = {"l": margin, "c": (w - tw) // 2, "r": w - tw - margin}[align] if tw < w else 0
        pts += [(x + left, y + top) for y, r in enumerate(rows) for x, v in enumerate(r) if v]
        top += len(rows) + style.lead

    def put(x, y, v):
        if 0 <= x < w and 0 <= y < h:
            canvas[y][x] = v

    ink, edge, shadow = palette["ink"], palette["edge"], palette["shadow"]
    if shadow is not None:
        for x, y in pts:
            for dx in range(-style.stroke, style.stroke + 2):
                for dy in range(-style.stroke, style.stroke + 2):
                    put(x + dx, y + dy, shadow)
    if edge is not None:
        for x, y in pts:
            for dx in range(-style.stroke, style.stroke + 1):
                for dy in range(-style.stroke, style.stroke + 1):
                    put(x + dx, y + dy, edge)
    for x, y in pts:
        put(x, y, ink[y] if isinstance(ink, list) else ink)
    return canvas


def _get(data, page, x, y):
    _, off, stride, bpp = page
    a = off + y * stride + x * bpp // 8
    if bpp == 8:
        return data[a]
    return data[a] >> 4 if x & 1 else data[a] & 15


def _set(data, page, x, y, v):
    _, off, stride, bpp = page
    a = off + y * stride + x * bpp // 8
    if bpp == 8:
        data[a] = v
    elif x & 1:
        data[a] = data[a] & 0x0F | v << 4
    else:
        data[a] = data[a] & 0xF0 | v


def _under(row, background, data=None, page=None, y=0):
    """What each pixel of a row is without the text. background: "row" (a bar's colour, read at its ends, because Japanese ink can outnumber it in the middle), an index, or (x, y) of a clean column of the same art: the rect's row r takes that column's row y + r."""
    if background == "row":
        return [collections.Counter(row[:4] + row[-4:]).most_common(1)[0][0]] * len(row)
    if isinstance(background, int):
        return [background] * len(row)
    if background[0] == "clean":  # ("clean", x0, x1, y0, h): the art stays. Art is a run of 4+ pixels in that band's colours (shorter runs are highlights in the ink); the rest takes the last art colour to its left
        _, x0, x1, y0, h = background
        art = {_get(data, page, x, y0 + r) for x in range(x0, x1) for r in range(h)}
        keep = [False] * len(row)
        start = 0
        for c in range(len(row) + 1):
            if c == len(row) or row[c] not in art:
                if c - start >= 4:
                    keep[start:c] = [True] * (c - start)
                start = c + 1
        last = next((v for v, k in zip(row, keep) if k), row[0])
        out = []
        for v, k in zip(row, keep):
            last = v if k else last
            out.append(last)
        return out
    return [_get(data, page, background[0], background[1] + y)] * len(row)


def sampled(data, page, rects, style, h, background):
    """Inks from the Japanese it replaces: per canvas row the commonest ink there, so gradients stay. Edge is the commonest colour touching the background; explicit style values win."""
    per_row = [collections.Counter() for _ in range(h)]
    edges = collections.Counter()
    for rect in rects:
        x, y, w, rh, dy = (*rect, 0)[:5]
        for r in range(rh):
            row = [_get(data, page, x + c, y + r) for c in range(w)]
            under = _under(row, background, data, page, r + dy)
            for c, v in enumerate(row):
                if v == under[c] or r + dy >= h:
                    continue
                per_row[r + dy][v] += 1
                if any(0 <= c + dx < w and row[c + dx] == under[c + dx] for dx in (-1, 1)):
                    edges[v] += 1
    edge = style.edge
    if edge == "auto":
        edge = edges.most_common(1)[0][0] if edges else None
    elif edge == "none":
        edge = None
    if style.ink != "auto":
        ink = style.ink
    else:
        ink = [None] * h
        for r in range(h):
            per_row[r].pop(edge, None)
            if per_row[r]:
                ink[r] = per_row[r].most_common(1)[0][0]
        known = [r for r in range(h) if ink[r] is not None]
        for r in range(h):
            if ink[r] is None:
                ink[r] = ink[min(known, key=lambda k: abs(k - r))] if known else (edge or 1)
    return {"ink": ink, "edge": edge, "shadow": style.shadow}


def draw_label(data, page, rects, text, style, align, background):
    """Clear the rects and draw the text across them, left to right. A rect may name its row in the line: (x, y, w, h, dy)."""
    w = sum(r[2] for r in rects)
    h = max(r[3] + (r[4] if len(r) > 4 else 0) for r in rects)
    canvas = letter(text, style, w, h, align, sampled(data, page, rects, style, h, background))
    at = 0
    for rect in rects:
        x, y, rw, rh, dy = (*rect, 0)[:5]
        for r in range(rh):
            row = [_get(data, page, x + c, y + r) for c in range(rw)]
            under = _under(row, background, data, page, r + dy)
            for c in range(rw):
                v = canvas[r + dy][at + c] if r + dy < h else None
                if background == "row" and (c < 2 or c >= rw - 2) and v is None:
                    continue  # the bar's own frame
                _set(data, page, x + c, y + r, v if v is not None else under[c])
        at += rw


def _files():
    out = {credits.STAFF: {"lz": 0, "rects": []}, **{rel: {"lz": None, "rects": []} for rel in credits.SEQ}}
    for page, rects, *_ in gfx_labels.LABELS:
        rel, off, stride, bpp = page
        entry = out.setdefault(rel, {"lz": None if LZ_NONE.match(rel) else 0, "rects": []})
        for rect in rects:
            x, y, w, h = rect[:4]
            for row in range(h):
                a = off + (y + row) * stride + x * bpp // 8
                entry["rects"].append((a, a + (w * bpp + 7) // 8))
    for rel, patches in gfx_labels.PATCHES.items():
        out[rel]["rects"] += [(off, off + len(b)) for off, b in patches]
    out[gfx_labels.FLAG] = {"lz": None, "rects": [(0x20, 0x444A)]}  # the file's whole stream area
    return out


FILES = _files()
BY_FILE = collections.defaultdict(list)
for _label in gfx_labels.LABELS:
    BY_FILE[_label[0][0]].append(_label)


def lz_at(rel):
    return FILES[rel]["lz"] if rel in FILES else None


def spans(rel):
    if rel == credits.STAFF or rel in credits.SEQ:
        return credits.spans(rel, _source(rel))
    return FILES[rel]["rects"] if rel in FILES else []


def _flag(data):
    """FLAG.BIN with each stream's name redrawn, in that stream's own slot: moving one hangs the game, so its offsets are compiled in somewhere (not found in PAW.EXE)."""
    out, at = bytearray(data), 0x20
    for labels in gfx_labels.FLAG_STREAMS:
        end = at + 4 + int.from_bytes(data[at:at + 3], "little")
        column = bytearray(lzkc.decompress(data[at:end], strict=True))
        for page, rects, text, style, align, background in labels:
            draw_label(column, page, rects, text, style, align, background)
        stream = lzkc.compress(bytes(column))
        if len(stream) > end - at:
            raise ValueError(f"FLAG.BIN stream at {at:#x} is {len(stream)} bytes, has {end - at}")
        out[at:end] = stream + bytes(end - at - len(stream))
        at = end
    return bytes(out)


def apply(rel, data):
    """The decoded file with its labels redrawn."""
    if rel == credits.STAFF:
        return credits.sheet()
    if rel in credits.SEQ:
        return credits.patch(data)
    if rel == gfx_labels.FLAG:
        return _flag(data)
    data = bytearray(data)
    for page, rects, text, style, align, background in BY_FILE[rel]:
        draw_label(data, page, rects, text, style, align, background)
    for off, new in gfx_labels.PATCHES.get(rel, ()):
        data[off:off + len(new)] = new
    return bytes(data)


def _source(rel):
    p = ROOT / "work/unpacked" / rel
    return p.read_bytes() if p.is_file() else (ROOT / "work/disc/tree" / rel).read_bytes()


def sheet(out, pattern=None):
    """Old and new of every label: greys by index, enough to read them without a build."""
    rows = []
    for rel in sorted(FILES):
        if pattern and not re.search(pattern, rel):
            continue
        old = _source(rel)
        new = apply(rel, old)
        for page, rects, *_ in BY_FILE[rel]:
            w = sum(r[2] for r in rects)
            h = max(r[3] + (r[4] if len(r) > 4 else 0) for r in rects)
            img = Image.new("RGB", (w * 2 + 8, h), (0, 96, 96))
            for side, d in enumerate((old, new)):
                at = 0
                for rect in rects:
                    x, y, rw, rh, dy = (*rect, 0)[:5]
                    for r in range(rh):
                        for c in range(rw):
                            v = _get(d, page, x + c, y + r)
                            if v:
                                g = 60 + (v * 37) % 196
                                img.putpixel((side * (w + 8) + at + c, r + dy), (g, g, g))
                    at += rw
            rows.append(img)
    W, H = max(i.width for i in rows), sum(i.height + 2 for i in rows)
    S = Image.new("RGB", (W, H), (0, 0, 0))
    y = 0
    for i in rows:
        S.paste(i, (0, y))
        y += i.height + 2
    S.save(out)
    print(out, len(rows), "labels", W, H)


if __name__ == "__main__":
    if sys.argv[1:2] == ["sheet"]:
        sheet(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        sys.exit(__doc__)
