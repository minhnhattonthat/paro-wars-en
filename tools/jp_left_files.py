"""Japanese still in the code files of a built disc: runs of 2+ Shift-JIS kana/kanji ending in NUL, in PAW.EXE and every overlay.

usage: jp_left_files.py [build/paro_wars_marker.bin]   Prints file, offset, text. tools/notext.tsv doesn't apply: read the list.
Entries of kind num/data are skipped, so what's left is text the extractor missed or `data` it has wrongly set aside. The font block is skipped too."""
import glob
import json
import re
import sys
from pathlib import Path

import disc

ROOT = Path(__file__).resolve().parents[1]
RUN = re.compile(rb"(?:[\x81-\x84\x88-\x97][\x40-\xfc])+\x00")
KEEP = re.compile("[ぁ-ヶ一-龠々]")
FONT = (0x93EC0, 0xA3C00)  # PAW.EXE


def main():
    img = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "build/paro_wars_marker.bin")
    skip = {}
    for path in glob.glob(str(ROOT / "script/menu/*.json")):
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        skip[doc["file"]] = {e["off"] for e in doc["entries"] if e["kind"] != "text"}
    with open(img, "rb") as f:
        entries = {p[1:]: (lba, n, size) for p, lba, n, size in disc.walk(f)}
        total = 0
        for rel in sorted(skip):
            lba, n, size = entries[rel]
            d = disc.read_user(f, lba, n)[:size]
            if rel == "PAW.EXE":
                d = d[:0xBC000]
            for m in RUN.finditer(d):
                if m.start() in skip[rel] or (rel == "PAW.EXE" and FONT[0] <= m.start() < FONT[1]) or len(m.group()) < 5:
                    continue
                try:
                    s = m.group()[:-1].decode("cp932")
                except UnicodeDecodeError:
                    continue
                if KEEP.search(s):
                    print(f"{rel}\t{m.start():x}\t{s}")
                    total += 1
    print(f"{total} runs")


if __name__ == "__main__":
    main()
