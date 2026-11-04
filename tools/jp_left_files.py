"""Japanese still in the code files of a built disc: runs of 2+ Shift-JIS kana/kanji ending in NUL, in PAW.EXE and every overlay.

usage: jp_left_files.py [build/paro_wars_marker.bin]   Prints file, offset, text. tools/notext.tsv doesn't apply: read the list.
Entries of kind num/data are skipped, so what's left is text the extractor missed or `data` it has wrongly set aside. The font block is skipped too."""
import glob
import json
import re
import sys
from pathlib import Path

import disc
import lzkc

ROOT = Path(__file__).resolve().parents[1]
RUN = re.compile(rb"(?:[\x81-\x84\x88-\x97][\x40-\xfc])+\x00")
LOOSE = re.compile(rb"(?:[\x81-\x84\x88-\x97][\x40-\xfc])+")  # compressed files hold paged text, not always NUL-ended
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
        print(f"{total} runs in code files")
        # The script's compressed files, decoded: story pages, endings, shouts, bios, KABE4. Anything left there is text a build didn't write.
        total = 0
        for path in glob.glob(str(ROOT / "script/*/*.json")):
            doc = json.loads(Path(path).read_text(encoding="utf-8"))
            if doc["lz"] is None:
                continue
            lba, n, size = entries[doc["file"]]
            d = lzkc.decompress(disc.read_user(f, lba, n)[doc["lz"]:], strict=True)  # the directory's size is stale, a file may have grown inside its sectors
            data = [(e["off"], e["off"] + e["len"]) for e in doc["entries"] if e["kind"] != "text"]
            for m in LOOSE.finditer(d):
                if m.start() < doc["text_from"] or any(a <= m.start() < b for a, b in data):
                    continue
                try:
                    s = m.group().decode("cp932")
                except UnicodeDecodeError:
                    continue
                if len(s) >= 2 and KEEP.search(s):
                    print(f"{doc['file']}\t{m.start():x}\t{s}")
                    total += 1
    print(f"{total} runs in compressed script files")


if __name__ == "__main__":
    main()
