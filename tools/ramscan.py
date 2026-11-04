"""Recon: which disc files sit in a RAM dump right now? usage: ramscan.py RAM.bin TREE [--min 64]

Searches each file's first non-trivial 32 bytes; prints the RAM address, file and whether the whole file matches."""
import argparse
import os

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("ram")
ap.add_argument("tree")
a = ap.parse_args()
ram = open(a.ram, "rb").read()
for dp, _, names in os.walk(a.tree):
    if "SOUND" in dp or "STR" in dp:
        continue
    for name in names:
        path = os.path.join(dp, name)
        d = open(path, "rb").read()
        probe = d[8:40]
        if len(probe) < 32 or len(set(probe)) < 6:
            continue
        o = ram.find(probe)
        if o >= 0:
            start = o - 8
            full = ram[start:start + len(d)] == d
            print(f"{0x80000000 + start:08x} {len(d):7d} {'full' if full else 'part'} {os.path.relpath(path, a.tree)}")
