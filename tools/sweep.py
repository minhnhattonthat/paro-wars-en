"""Graphics-text static sweep: render every image-like disc file into numbered contact sheets with a printed index.

usage: sweep.py TREE UNPACKED OUTDIR [--page 15] [--only REGEX]
Uses the LZ-decoded copy when one exists. Each file becomes a 256 px wide tile: 8bpp and 4bpp views, greyscale by index (no CLUT),
capped at 192 rows per view, tall files cut to their first rows and noted. Identical contents render once. Prints every skipped
family with its reason; nothing drops silently. Output: OUTDIR/sheet_NNN.png and OUTDIR/index.tsv (sheet, cell, path, size, dup-of)."""
import argparse
import hashlib
import os
import re

from PIL import Image, ImageDraw

SKIP = [
    (r"^(SOUND|STR)/", "audio/video"),
    (r"^DATA/DEMO/(TXT|SEQ|COL)_", "text and scripts, palettes"),
    (r"^DATA/BTL/", "sampled separately: per-unit battle frames (2115), see --only"),
    (r"^DATA/BK_DT/", "sampled separately: battle backdrops (3349), see --only"),
    (r"^DATA/ATAMA/ATM", "sampled separately: unit head icons, see --only"),
    (r"(SYSTEM\.CNF|license_data\.dat|SLPM_860\.16|PAW\.EXE)$", "system files"),
    (r"^DATA/.*_OV\.BIN$", "code overlays"),
    (r"^DATA/(CSTDT|MAP_DEF|BUTA[LR]|TAMA)", "small data tables"),
    (r"\.TMD$", "3D models"),
]
W, H = 256, 192


def view(data, bpp):
    """Greyscale WxH image of data at bpp; pixels past the data are black."""
    img = Image.new("L", (W, H), 0)
    stride = W * bpp // 8
    px = img.load()
    for y in range(min(H, len(data) // stride)):
        row = data[y * stride:(y + 1) * stride]
        for x in range(W):
            if bpp == 8:
                px[x, y] = row[x]
            else:
                b = row[x // 2]
                px[x, y] = ((b >> 4) if x & 1 else (b & 15)) * 17
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree")
    ap.add_argument("unpacked")
    ap.add_argument("out")
    ap.add_argument("--page", type=int, default=12)
    ap.add_argument("--only", help="regex: render only these paths, ignoring the skip list")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    skipped = {}
    items = []
    for dp, _, names in os.walk(a.tree):
        for name in sorted(names):
            rel = os.path.relpath(os.path.join(dp, name), a.tree).replace("\\", "/")
            if a.only:
                if not re.search(a.only, rel):
                    continue
            else:
                hit = next((why for pat, why in SKIP if re.search(pat, rel)), None)
                if hit:
                    skipped[hit] = skipped.get(hit, 0) + 1
                    continue
            items.append(rel)
    items.sort()
    seen = {}
    cells = []
    index = open(os.path.join(a.out, "index.tsv"), "w", encoding="utf-8")
    for rel in items:
        up = os.path.join(a.unpacked, rel)
        path = up if os.path.exists(up) else os.path.join(a.tree, rel)
        data = open(path, "rb").read()
        h = hashlib.sha1(data).hexdigest()
        if h in seen:
            index.write(f"-\t-\t{rel}\t{len(data)}\tdup:{seen[h]}\n")
            continue
        seen[h] = rel
        cells.append((rel, data))
    cols = 4
    rows = a.page // cols
    for p in range(0, len(cells), a.page):
        sheet_no = p // a.page
        sheet = Image.new("L", (cols * (W + 2), rows * (H * 2 + 14)), 60)
        d = ImageDraw.Draw(sheet)
        for i, (rel, data) in enumerate(cells[p:p + a.page]):
            x, y = i % cols * (W + 2), i // cols * (H * 2 + 14)
            d.text((x + 1, y), f"{p + i} {rel[5:]} {len(data):#x}", fill=255)
            sheet.paste(view(data, 8), (x, y + 12))
            sheet.paste(view(data, 4), (x, y + 12 + H))
            index.write(f"{sheet_no}\t{i}\t{rel}\t{len(data)}\t\n")
        sheet.save(os.path.join(a.out, f"sheet_{sheet_no:03d}.png"))
    index.close()
    print(f"{len(items)} files, {len(cells)} unique, {(len(cells) + a.page - 1) // a.page} sheets")
    for why, n in skipped.items():
        print(f"skipped {n}: {why}")


if __name__ == "__main__":
    main()
