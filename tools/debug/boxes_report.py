"""Join the BOX lines of a marker tour (tools/debug/boxes.lua) with build/marker.tsv.

usage: boxes_report.py [work/qa/marker] -> <dir>/boxes.tsv: one row per entry seen (id, family, x, y, wrap, gap, px, lines, right edge, scene), and a summary:
entries seen and not seen per script file, windows that still show fullwidth text, peak of the frame's primitive pool."""
import collections
import glob
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOX = re.compile(r"BOX f\d+ x=(-?\d+) y=(-?\d+) wrap=(\d+) gap=(\d+) count=(\d+) flags=(\w+) type=(\d+) px=(\d+) lines=(\d+) ptr=(\w+) codes=(\w*) head=(.*)$")
JAPANESE = re.compile("[ぁ-ヶ一-龠]")


def codes_text(hexes):
    """The fullwidth codes of a window as text; pairs of letters read as dots."""
    out = ""
    for i in range(0, len(hexes), 4):
        v = int(hexes[i:i + 4], 16)
        try:
            out += v.to_bytes(2, "big").decode("cp932") if v >= 0x8000 else "."
        except UnicodeDecodeError:
            out += "?"
    return out
POOL = re.compile(r"POOL f\d+ used=(\d+)")
MARK = re.compile(r"^#?([0-9A-Z]{3})\b")


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "work/qa/marker")
    marks = {}
    for line in (ROOT / "build/marker.tsv").read_text(encoding="utf-8").splitlines():
        mid, eid, slot, jp = line.split("\t", 3)
        marks[mid] = (eid, int(slot), jp)
    seen = {}
    fullwidth = collections.Counter()
    scenes = {}
    peak = (0, "")
    for log in glob.glob(str(out / "*/log.txt")):
        scene = os.path.basename(os.path.dirname(log))
        for line in open(log, encoding="utf-8", errors="replace"):
            m = POOL.search(line)
            if m and int(m[1]) > peak[0]:
                peak = (int(m[1]), scene)
            m = BOX.search(line)
            if not m:
                continue
            x, y, wrap, gap, count, flags, typ, px, lines, ptr, codes, head = m.groups()
            k = MARK.match(head)
            if not k or k[1] not in marks:
                text = codes_text(codes)
                if JAPANESE.search(text):
                    fullwidth[(text, ptr)] += 1
                    scenes.setdefault((text, ptr), scene)
                continue
            mid = k[1]
            row = (int(x), int(y), int(wrap), int(gap), int(px), int(lines), int(x) + int(px), scene, flags, typ)
            if mid not in seen or row[6] > seen[mid][6]:
                seen[mid] = row
    with open(out / "boxes.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("marker\tid\tslot\tx\ty\twrap\tgap\tpx\tlines\tright\tscene\tflags\ttype\tjp\n")
        for mid, r in sorted(seen.items(), key=lambda kv: marks[kv[0]][0]):
            eid, slot, jp = marks[mid]
            f.write("\t".join(map(str, (mid, eid, slot, *r, jp))) + "\n")
    per = collections.Counter(), collections.Counter()
    for mid, (eid, _, _) in marks.items():
        per[0 if mid in seen else 1][eid.split(":")[0]] += 1
    names = sorted(set(per[0]) | set(per[1]))
    print(f"{len(seen)} of {len(marks)} entries seen; pool peak {peak[0]} of 52800 in {peak[1]}")
    print("seen/unseen per family (with a seen entry):", " ".join(f"{n}:{per[0][n]}/{per[1][n]}" for n in names if per[0][n]))
    print("families with none seen:", " ".join(f"{n}:{per[1][n]}" for n in names if not per[0][n]))
    print(f"Japanese in windows, not a marker: {len(fullwidth)}")
    for (text, ptr), _ in sorted(fullwidth.items(), key=lambda kv: kv[0][1])[:80]:
        print(f"  {ptr} {scenes[(text, ptr)]} {text}")


if __name__ == "__main__":
    main()
