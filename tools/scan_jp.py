"""Recon: list Shift-JIS text per file in the unpacked disc tree, filtered so image noise drops out.

usage: scan_jp.py TREE [--dump OUT.txt]   prints runs, chars, file, sample; --dump also writes every kept run with its offset.
Kept run: at least 3 chars with 40% or more kana/fullwidth/ASCII. shortcut: kanji-only names under 3 chars are missed,
the extractor (phase 4) must cover them through its pointer tables and leftover scan instead."""
import argparse
import os
import sys

from skill import SCRIPTS

sys.path.insert(0, SCRIPTS)
from jpscan import sjis_runs


def texty(s):
    good = sum(1 for c in s if 0x3040 <= ord(c) <= 0x30ff or 0xff00 <= ord(c) <= 0xffef or ord(c) < 0x7f or c in "　、。！？…「」～")
    kana = sum(1 for c in s if 0x3040 <= ord(c) <= 0x30ff or 0xff10 <= ord(c) <= 0xff5a)
    return kana >= 1 and good / len(s) >= 0.4


ap = argparse.ArgumentParser()
ap.add_argument("tree")
ap.add_argument("--dump")
a = ap.parse_args()
out = open(a.dump, "w", encoding="utf-8") if a.dump else None
for dp, _, names in os.walk(a.tree):
    if "SOUND" in dp or "STR" in dp:  # audio and video hold no script text
        continue
    for name in sorted(names):
        path = os.path.join(dp, name)
        rel = os.path.relpath(path, a.tree).replace("\\", "/")
        with open(path, "rb") as f:
            runs = [(o, s) for o, s in sjis_runs(f.read(), 3) if texty(s)]
        if runs:
            print(f"{len(runs)}\t{sum(len(s) for _, s in runs)}\t{rel}\t{runs[0][1][:30]!r}")
            if out:
                for o, s in runs:
                    out.write(f"{rel}\t{o:#x}\t{s!r}\n")
