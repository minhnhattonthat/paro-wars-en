"""Original pixels of every redrawn label that survive elsewhere on the disc: label_copies.py. Prints file, offset and the label's English.
A hit means a screen may load that copy and still show Japanese: KABE3's mode signs were redrawn while the select screen loads KABE0's.
tools/gfx_copies.tsv and other labels count as covered.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from gfx_labels import LABELS


def rows(data, off, stride, bpp, x, y, w, h):
    a = lambda r: off + (y + r) * stride + x * bpp // 8
    return [data[a(r):a(r) + (w * bpp + 7) // 8] for r in range(h)]


def main():
    blobs = {}
    for base in ("work/unpacked", "work/disc/tree"):
        for dirpath, _, names in os.walk(ROOT / base):
            for name in names:
                p = Path(dirpath, name)
                r = p.relative_to(ROOT / base).as_posix()
                if r not in blobs and "SOUND" not in r and "STR/" not in r and 1024 <= p.stat().st_size < 1 << 24:
                    blobs[r] = p.read_bytes()
    copies = {line.split("\t")[0] for line in (ROOT / "tools/gfx_copies.tsv").read_text().splitlines() if line}
    own = set()
    for (rel, off, stride, bpp), rects, *_ in LABELS:
        for x, y, *_ in rects:
            own.add((rel, off + y * stride + x * bpp // 8))
    seen = set()
    for (rel, off, stride, bpp), rects, text, *_ in LABELS:
        for rect in rects:
            data = blobs.get(rel)
            if data is None:
                print("no source", rel)
                continue
            want = rows(data, off, stride, bpp, *rect[:4])
            pick = max(range(len(want)), key=lambda i: len(set(want[i])))
            if len(set(want[pick])) < 3:
                continue
            for name, blob in blobs.items():
                at = blob.find(want[pick])
                while at >= 0:
                    top = at - pick * stride
                    if top >= 0 and all(blob[top + i * stride:top + i * stride + len(want[i])] == want[i] for i in range(len(want))):
                        if (name, top) not in own and name not in copies and (name, top) not in seen:
                            seen.add((name, top))
                            print(f"{name}\t{top:#x}\t{rel} {rect}\t{text}")
                    at = blob.find(want[pick], at + 1)
    print(len(seen), "uncovered copies")


main()
