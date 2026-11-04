"""Recon: find LZ streams embedded at an offset in container files. usage: lz_embed.py [--max 0x800] FILE...

A hit: 4-aligned offset whose u24 length field reaches at or near end of file and strict decoding yields more than the stream.
Prints offset, stream length, decoded length, and a Shift-JIS sample when the decoded data holds text."""
import argparse
import re
import sys

import lzkc

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("files", nargs="+")
ap.add_argument("--max", type=lambda s: int(s, 0), default=0x800)
a = ap.parse_args()
sjis = re.compile(rb"(?:[\x82\x83][\x40-\xfc]|[\x88-\x97][\x40-\xfc]|\x81[\x40-\xac]){4,}")
for path in a.files:
    d = open(path, "rb").read()
    hits = []
    for o in range(0, min(a.max, len(d) - 8), 4):
        n = d[o] | d[o + 1] << 8 | d[o + 2] << 16
        if d[o + 3] or not 16 <= n <= len(d) - o - 4:
            continue
        try:
            out = lzkc.decompress(d[o:], strict=True)
        except (ValueError, IndexError):
            continue
        if len(out) > n:
            m = sjis.search(out)
            sample = m.group().decode("cp932", "replace")[:24] if m else ""
            hits.append(f"+{o:#x} stream {n:#x} -> {len(out):#x} {sample}")
    print(path.rsplit("/", 1)[-1], len(d), hits[:4])
sys.exit(0)
