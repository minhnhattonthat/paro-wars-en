"""Every decoded file holding the bytes of a label: find_copies.py FILE OFFSET STRIDE BPP X Y W H [...more X Y W H]. Prints each hit once (file, page offset). Searches work/unpacked, then the plain files of work/disc/tree."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rows(data, off, stride, bpp, x, y, w, h):
    a = lambda r: off + (y + r) * stride + x * bpp // 8
    return [data[a(r):a(r) + (w * bpp + 7) // 8] for r in range(h)]


def main():
    rel, off, stride, bpp = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0), int(sys.argv[4])
    data = (ROOT / "work/unpacked" / rel).read_bytes() if (ROOT / "work/unpacked" / rel).is_file() else (ROOT / "work/disc/tree" / rel).read_bytes()
    rects = [tuple(map(int, sys.argv[5 + i:9 + i])) for i in range(0, len(sys.argv) - 5, 4)]
    seen = set()
    for base in ("work/unpacked", "work/disc/tree"):
        for dirpath, _, names in os.walk(ROOT / base):
            for name in names:
                p = Path(dirpath, name)
                r = p.relative_to(ROOT / base).as_posix()
                if r in seen or "SOUND" in r or "STR" in r or p.stat().st_size < 1024:
                    continue
                seen.add(r)
                blob = p.read_bytes()
                for rect in rects:
                    want = rows(data, off, stride, bpp, *rect)
                    pick = max(range(len(want)), key=lambda i: len(set(want[i])))
                    at = blob.find(want[pick])
                    while at >= 0:
                        top = at - pick * stride
                        if top >= 0 and all(blob[top + i * stride:top + i * stride + len(want[i])] == want[i] for i in range(len(want))):
                            print(r, hex(top), "rect", rect)
                            break
                        at = blob.find(want[pick], at + 1)


if __name__ == "__main__":
    main()
