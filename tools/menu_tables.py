"""Menu window tables: text entries reached by a word that sits in a {x,y} + pointer record of a window descriptor (docs/re/boxes.md).

usage: menu_tables.py [NAME]   Prints window address, its pos, size, and each line's x, y, id and Japanese.
Layout: {0}{pos x,y}{0}{size w,h}{0} then {x,y}{text*} repeated, ended by {0xFFFF}.
"""
import glob
import json
import struct
import sys
from pathlib import Path

import extract

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work/disc/tree"


def half(v):
    return v & 0xFFFF, v >> 16


def windows(data, base):
    """Yield (addr, pos, size, [(x, y, ptr)]) for every window descriptor in data."""
    words = struct.unpack_from(f"<{len(data) // 4}I", data)
    for i in range(len(words) - 7):
        if words[i] or words[i + 2] or words[i + 4]:
            continue
        pos, size = half(words[i + 1]), half(words[i + 3])
        if not (pos[0] < 40 and pos[1] < 30 and 0 < size[0] < 40 and 0 < size[1] < 30):
            continue
        lines, k = [], i + 5
        while k + 1 < len(words) and 0x80000000 <= words[k + 1] < 0x80200000:
            x, y = half(words[k])
            if x > 640 or y > 480:
                break
            lines.append((x, y, words[k + 1]))
            k += 2
        if lines and words[k] & 0xFFFF == 0xFFFF:
            yield base + i * 4, pos, size, lines


def load(doc):
    data = (TREE / doc["file"]).read_bytes()
    if doc["file"] == "PAW.EXE":
        return data[0x800:], struct.unpack_from("<I", data, 0x18)[0]
    return data, extract.best_base(data, doc["entries"])


def file_windows(doc):
    """(addr, pos, size, [(x, y, entry)]) of every window in a menu doc that shows at least one of its entries."""
    data, base = load(doc)
    shift = 0x800 if doc["file"] == "PAW.EXE" else 0
    by_addr = {base + e["off"] - shift: e for e in doc["entries"]}
    for addr, pos, size, lines in windows(data, base):
        known = [(x, y, by_addr[p]) for x, y, p in lines if p in by_addr]
        if known:
            yield addr, pos, size, known


def index():
    """entry id -> (x in the window, window width in tiles), for the width lint. A string in two windows keeps the tighter limit."""
    out = {}
    for doc_path in sorted(glob.glob(str(ROOT / "script/menu/*.json"))):
        doc = json.loads(Path(doc_path).read_text(encoding="utf-8"))
        for _, _, size, known in file_windows(doc):
            for x, _, e in known:
                prev = out.get(e["id"])
                if not prev or (size[0] + 1) * 16 - x < (prev[1] + 1) * 16 - prev[0]:
                    out[e["id"]] = (x, size[0])
    return out


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else None
    for doc_path in sorted(glob.glob(str(ROOT / "script/menu/*.json"))):
        name = Path(doc_path).stem
        if want and name != want:
            continue
        doc = json.loads(Path(doc_path).read_text(encoding="utf-8"))
        for addr, pos, size, known in file_windows(doc):
            print(f"{name} {addr:08x} pos={pos} size={size}")
            for x, y, e in known:
                print(f"  x={x} y={y} {e['id']} len={e['len']} {e['jp']}")


if __name__ == "__main__":
    main()
