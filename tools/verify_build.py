"""verify_build.py [BUILT.bin]: nothing changed where it shouldn't, on a built disc. Exit 1 on any stray byte; build.py runs it.

Disc level: romdiff.py over the image, allowed the sectors of the patched files and the spill gap.
File level, on decoded files: each changed byte must be in a text slot of that file, a word a moved string's ref names, a loader record, or
for PAW.EXE the hook spans and the font; graphics files only inside their declared rects (tools/gfx.py)."""
import glob
import json
import subprocess
import sys
from pathlib import Path

import disc
import en_text
import lzkc
import reloc

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "rom/Paro Wars (Japan).bin"
HOOK = [(0x800676F8, 0x800676FC), (0x80067734, 0x80067738), (0x800677A0, 0x80067CEC), (0x80068838, 0x800688CC)]  # asm/vwf.asm
RECORD_OWNERS = {"DATA/ENDING.BIN"}  # may gain a spilled file's new {size, lba}: build.find_records
RECORD_RANGES = {"DATA/ENDING.BIN": (0x3AC8, 0x4F34)}


def docs_by_file():
    out = {}
    for path in glob.glob(str(ROOT / "script/*/*.json")):
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        out.setdefault(doc["file"], []).append(doc)
    return out


def ref_bytes(all_docs):
    """{file: set of byte offsets a ref may rewrite}: refs live in any code, not only their string's own file."""
    import extract  # late: only the overlay base needs it

    bases = {"PAW": reloc.PAW_BASE}
    allowed = {}
    with open(ORIG, "rb") as f:
        entries = {p: (lba, n, size) for p, lba, n, size in disc.walk(f)}
        for docs in all_docs.values():
            for doc in docs:
                for e in doc["entries"]:
                    for ref in e.get("refs") or ():
                        name, at = ref.split(":")
                        rel = "PAW.EXE" if name == "PAW" else f"DATA/{name}.BIN"
                        if name not in bases:
                            lba, n, size = entries["/" + rel]
                            bases[name] = extract.best_base(disc.read_user(f, lba, n)[:size], [x for d in all_docs[rel] for x in d["entries"]])
                        word = at.startswith("w")
                        off = int(at[1:] if word else at, 16) - bases[name]
                        span = 4 if word else (reloc.SEARCH + 1) * 4  # a lui and its low half, up to SEARCH words on
                        allowed.setdefault(rel, set()).update(range(off, off + span))
    return allowed


def file_allowed(rel, docs, refs):
    """Sorted spans plus the ref bytes this file may change."""
    spans = [(e["off"], e["off"] + e["len"]) for doc in docs for e in doc["entries"] if e["kind"] == "text"]
    if rel == "PAW.EXE":
        spans += [(a - reloc.PAW_BASE, b - reloc.PAW_BASE) for a, b in HOOK]
        spans.append((en_text.FONT_FILE + en_text.HIRAGANA * en_text.CELL, en_text.FONT_FILE + 305 * en_text.CELL))  # the cells patch_font draws; Greek and kana past it stay
        spans.append((reloc.POOL_START, reloc.POOL_END))
    if rel in RECORD_RANGES:
        spans.append(RECORD_RANGES[rel])
    return spans, refs.get(rel, set())


def stray(old, new, spans, extra):
    """Offsets that differ outside spans and extra."""
    if len(old) != len(new):
        return [("size", len(old), len(new))]
    bad = []
    marks = bytearray(len(old))
    for a, b in spans:
        marks[a:b] = b"\1" * (b - a)
    for x in extra:
        if 0 <= x < len(marks):
            marks[x] = 1
    for i, (p, q) in enumerate(zip(old, new)):
        if p != q and not marks[i]:
            bad.append(i)
    return bad


def spilled(fo, fn, entries):
    """{rel: (lba, sectors)} of files build.spill moved to the gap, from the loader records that changed."""
    by_lba = {lba: (p[1:], n) for p, (lba, n, size) in entries.items() if n}
    out = {}
    for owner in RECORD_OWNERS:
        lba, n, size = entries["/" + owner]
        old, new = disc.read_user(fo, lba, n)[:size], disc.read_user(fn, lba, n)[:size]
        for at in range(4, size - 7, 4):
            was = int.from_bytes(old[at + 4 : at + 8], "little")
            now = int.from_bytes(new[at + 4 : at + 8], "little")
            # A record's old size must match the file too: a size word can equal some file's LBA.
            if was != now and was in by_lba and (int.from_bytes(old[at : at + 4], "little") + 2047) // 2048 == by_lba[was][1]:
                out[by_lba[was][0]] = (now, (int.from_bytes(new[at : at + 4], "little") + 2047) // 2048)
    return out


def main(path):
    import gfx  # declared rects per graphics file

    all_docs = docs_by_file()
    refs = ref_bytes(all_docs)
    failures = []
    with open(ORIG, "rb") as fo, open(path, "rb") as fn:
        entries = {p: (lba, n, size) for p, lba, n, size in disc.walk(fo)}
        moved = spilled(fo, fn, entries)
        ranges = []
        changed = 0
        for p, (lba, n, size) in entries.items():
            if p == "/" or not n or p.startswith(("/SOUND", "/STR")):
                continue
            old = disc.read_user(fo, lba, n)
            rel = p[1:]
            new = disc.read_user(fn, *moved[rel]) if rel in moved else disc.read_user(fn, lba, n)
            if old == new:
                continue
            if rel not in all_docs and rel not in refs and rel not in gfx.FILES and rel not in RECORD_OWNERS:
                failures.append(f"{rel}: changed, and nothing should write it")
                continue
            changed += 1
            ranges.append(f"{lba * disc.SECTOR:x}-{(lba + n) * disc.SECTOR - 1:x}")
            docs = all_docs.get(rel, [])
            lz = docs[0]["lz"] if docs else gfx.lz_at(rel)
            if lz is not None:
                if old[:lz] != new[:lz]:
                    failures.append(f"{rel}: bytes before the LZ stream changed")
                old_d, new_d = lzkc.decompress(old[lz:], strict=True), lzkc.decompress(new[lz:], strict=True)
            else:
                old_d, new_d = old[:size], new[:size]
            spans, extra = file_allowed(rel, docs, refs)
            spans += gfx.spans(rel)
            bad = stray(old_d, new_d, spans, extra)
            if bad:
                failures.append(f"{rel}: {len(bad)} stray bytes, first {[hex(x) if isinstance(x, int) else x for x in bad[:6]]}")
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    gap = [f"{a * disc.SECTOR:x}-{b * disc.SECTOR - 1:x}" for a, b in [(65172, 65172 + 1828)]]
    args = [str(ORIG), str(path)] + ranges + gap
    rc = subprocess.call([sys.executable, str(ROOT / "tools/romdiff.py")] + args)
    if rc:
        sys.exit(rc)
    print(f"verify ok: {changed} files changed ({len(moved)} spilled), all inside their allowed ranges")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "build/paro_wars_en.bin")
