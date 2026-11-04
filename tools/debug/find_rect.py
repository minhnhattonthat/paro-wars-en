"""Where a VRAM rect comes from: find_rect.py DUMP.vram.bin X Y WBYTES H [--dir work/unpacked ...]. X in halfwords, WBYTES its width in bytes. Prints every decoded file holding the rect's rows, stride guessed from the match."""
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump")
    ap.add_argument("x", type=int)
    ap.add_argument("y", type=int)
    ap.add_argument("w", type=int)
    ap.add_argument("h", type=int)
    ap.add_argument("--dir", action="append", default=[])
    a = ap.parse_args()
    vram = Path(a.dump).read_bytes()
    rows = [vram[((a.y + i) * 1024 + a.x) * 2:((a.y + i) * 1024 + a.x) * 2 + a.w] for i in range(a.h)]
    pick = max(range(a.h), key=lambda i: len(set(rows[i])))  # the most varied row, so blank rows can't match everywhere
    other = max((i for i in range(a.h) if i != pick), key=lambda i: len(set(rows[i])), default=None)
    print(f"row {pick} has {len(set(rows[pick]))} distinct bytes")
    for base in a.dir or [ROOT / "work/unpacked", ROOT / "work/disc/tree"]:
        for dirpath, _, names in os.walk(base):
            if "STR" in dirpath or "SOUND" in dirpath:
                continue
            for name in names:
                data = (Path(dirpath) / name).read_bytes()
                at = data.find(rows[pick])
                hits = 0
                while at >= 0 and hits < 4:
                    for stride in (64, 128, 256, 512):
                        o = at + (other - pick) * stride
                        if other is not None and 0 <= o and data[o:o + a.w] == rows[other]:
                            top = at - pick * stride
                            print(f"{Path(dirpath, name).relative_to(base)}  file offset {top:#x} stride {stride}: x {top % stride} y {top // stride}")
                    hits += 1
                    at = data.find(rows[pick], at + 1)


if __name__ == "__main__":
    main()
