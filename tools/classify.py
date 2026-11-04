"""Recon: classify every file in the unpacked disc tree. usage: classify.py TREE OUT.tsv

Columns: kind, size, first-u32, zero fraction, path. Kinds: tim (TIM magic), overlay (MIPS code by jr/addiu sp density),
pix (16-bit-ish image data), lz? (size field then high entropy), data."""
import math
import os
import struct
import sys
from collections import Counter


def entropy(d):
    if not d:
        return 0.0
    n = len(d)
    return -sum(c / n * math.log2(c / n) for c in Counter(d).values())


def mips_density(d):
    n = len(d) // 4
    if n < 16:
        return 0
    words = struct.unpack_from(f"<{n}I", d)
    hits = sum(1 for w in words if w == 0x03e00008 or w >> 16 == 0x27bd or w >> 16 == 0xafbf or w >> 16 == 0x8fbf)
    return hits / n


def kind(d):
    head = struct.unpack_from("<I", d)[0] if len(d) >= 4 else 0
    if head == 0x10 and len(d) > 20:
        return "tim"
    if mips_density(d) > 0.01:
        return "overlay"
    if len(d) < 8:
        return "tiny"
    if d[:4] == b"\x41\x00\x00\x00":
        return "tmd"
    return "lz?" if 0 < head < 0x400000 and head > len(d) and entropy(d[4:]) > 6.5 else "data"


def main(root, out):
    rows = []
    for dp, _, names in os.walk(root):
        for name in names:
            path = os.path.join(dp, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            if rel.startswith(("SOUND", "STR")):
                continue
            d = open(path, "rb").read()
            head = struct.unpack_from("<I", d)[0] if len(d) >= 4 else 0
            rows.append((kind(d), len(d), f"{head:08x}", f"{d.count(0) / max(1, len(d)):.2f}", f"{entropy(d):.2f}", rel))
    rows.sort(key=lambda r: r[5])
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(map(str, r)) + "\n")
    for k, c in Counter(r[0] for r in rows).most_common():
        print(k, c)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
