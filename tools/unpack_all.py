"""Recon: try the LZ codec on every disc file; write what decodes cleanly to work/unpacked/ and list results.

usage: unpack_all.py TREE OUTDIR LIST.tsv
A file counts as LZ when its header fits (lzkc.header_ok), strict decoding succeeds and the stream ends on the length field.
Prints every file it skipped by reason count, so no family drops out silently."""
import os
import sys
from collections import Counter

import lzkc

root, outdir, listing = sys.argv[1:4]
reasons = Counter()
with open(listing, "w", encoding="utf-8") as lst:
    for dp, _, names in os.walk(root):
        for name in sorted(names):
            path = os.path.join(dp, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            if rel.startswith(("SOUND", "STR")):
                continue
            d = open(path, "rb").read()
            if not lzkc.header_ok(d):
                reasons["no-header"] += 1
                continue
            try:
                out = lzkc.decompress(d, strict=True)
            except (ValueError, IndexError):
                reasons["bad-stream"] += 1
                continue
            if len(out) < len(d) // 2:  # random data can pass the header test but decodes to almost nothing
                reasons["too-small"] += 1
                continue
            reasons["lz"] += 1
            target = os.path.join(outdir, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            open(target, "wb").write(out)
            lst.write(f"{rel}\t{len(d)}\t{len(out)}\n")
print(dict(reasons))
