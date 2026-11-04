"""room.py DIR [--pokes]: what the windows of a tour on the ORIGINAL disc (warp_all --script tools/debug/boxes.lua) say about the English's room.

Default: one row per window: scene, y, x, count, entry id, text, room px (distance to the next window on its row). -> DIR/room.tsv
--pokes: entries whose text in RAM differs from the disc: the code wrote digits into them, so the English must keep those halfwords (docs/re/boxes.md)."""
import collections
import glob
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import extract  # noqa: E402
import reloc  # noqa: E402

BOX = re.compile(r"BOX f(\d+) x=(-?\d+) y=(-?\d+) wrap=\d+ gap=\d+ count=(\d+) flags=\w+ type=\d+ px=\d+ lines=\d+ ptr=(\w+) codes=(\w*) head=")


def addresses():
    """{RAM address: entry} for every string of an EXE or overlay."""
    tree = ROOT / "work/disc/tree"
    out = {}
    for _, doc in batches.docs():
        if doc["group"] != "menu" and doc["file"] not in ("DATA/UNITINFO.BIN", "DATA/ITEM.BIN"):
            continue
        if doc["file"] == "PAW.EXE":
            base = reloc.PAW_BASE
        else:
            base = extract.best_base((tree / doc["file"]).read_bytes(), doc["entries"]) if doc["group"] == "menu" else None
        if base is None:
            continue
        for e in doc["entries"]:
            out[base + e["off"]] = e
    return out


def text_of(codes):
    s = ""
    for i in range(0, len(codes), 4):
        v = int(codes[i:i + 4], 16)
        try:
            s += v.to_bytes(2, "big").decode("cp932")
        except (UnicodeDecodeError, OverflowError):
            s += "?"
    return s


def main():
    d = Path(sys.argv[1])
    pokes = "--pokes" in sys.argv
    by_addr = addresses()
    rows = []
    poked = {}
    for log in sorted(glob.glob(str(d / "*/log.txt"))):
        scene = os.path.basename(os.path.dirname(log))
        wins = {}
        for line in open(log, encoding="utf-8", errors="replace"):
            m = BOX.search(line)
            if not m:
                continue
            f, x, y, count, ptr, codes = m.groups()
            key = (int(y), int(x), ptr)
            wins[key] = (int(count), text_of(codes), int(ptr, 16))
        rowmap = collections.defaultdict(list)
        for (y, x, ptr) in wins:
            rowmap[y].append(x)
        for (y, x, ptr), (count, text, addr) in sorted(wins.items()):
            e = by_addr.get(addr)
            nexts = [nx for nx in rowmap[y] if nx > x]
            room = min(nexts) - x if nexts else ""
            rows.append(f"{scene}\t{y}\t{x}\t{count}\t{e['id'] if e else ''}\t{text}\t{room}")
            if e and e["kind"] == "text" and text.split("{")[0] != e["jp"].replace("{br}", "＠").split("{")[0]:
                poked[e["id"]] = (e["jp"], text, scene)
    if pokes:
        for eid, (jp, text, scene) in sorted(poked.items()):
            print(f"{eid}\t{jp}\t{text}\t{scene}")
        return
    (d / "room.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(len(rows), "windows", d / "room.tsv")


if __name__ == "__main__":
    main()
