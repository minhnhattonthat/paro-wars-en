"""Recon: find a Shift-JIS string, hex bytes or a file span in a PS1 RAM dump. usage: ramfind.py RAM (--sjis S | --hex H | --file F [--at HEX --len HEX])..."""
import argparse

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("ram")
ap.add_argument("--sjis", action="append", default=[])
ap.add_argument("--hex", action="append", default=[])
ap.add_argument("--file")
ap.add_argument("--at", type=lambda s: int(s, 16), default=0)
ap.add_argument("--len", type=lambda s: int(s, 16), default=0x100)
a = ap.parse_args()
ram = open(a.ram, "rb").read()


def report(label, pat):
    hits, o = [], ram.find(pat)
    while o >= 0 and len(hits) < 20:
        hits.append(f"{0x80000000 + o:08x}")
        o = ram.find(pat, o + 1)
    print(label, hits or "not found")


for s in a.sjis:
    report(s, s.encode("cp932"))
for h in a.hex:
    report(h, bytes.fromhex(h))
if a.file:
    span = open(a.file, "rb").read()[a.at:a.at + a.len]
    report(f"{a.file}@{a.at:#x}", span)
