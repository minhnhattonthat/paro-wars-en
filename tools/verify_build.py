"""verify_build.py [BUILT.bin] [--not-shipped]: nothing changed where it shouldn't, on a built disc. Exit 1 on any stray byte; build.py runs it.

Disc level: romdiff.py over the image with the build's write log (BUILT.writes), every write inside the sectors of the patched files and the spill gap.
File level, on decoded files: each changed byte must be in a text slot of that file, a word a moved string's ref names, a loader record, or
for PAW.EXE the hook spans and the font; graphics files only inside their declared rects (tools/gfx.py).
Shipped builds also: every text entry reads back as fit(en), in its slot, as a far string or through every ref; no code still names a vacated address."""
import glob
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

import disc
import en_text
import limits
import lzkc
import reloc
import romdiff

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "rom/Paro Wars (Japan).bin"
HOOK = [(0x800676F8, 0x800676FC), (0x80067734, 0x80067738), (0x800677A0, 0x80067CEC), (0x80068838, 0x800688CC), (0x8004FD78, 0x8004FD7C)]  # asm/vwf.asm
RECORD_OWNERS = {"DATA/ENDING.BIN"}  # may gain a spilled file's new {size, lba}: build.find_records
RECORD_RANGES = {"DATA/ENDING.BIN": (0x3AC8, 0x4F34)}
SPILL_GAP = (65172, 65172 + 1828)  # build.SPILL_GAP; that module imports this one


def docs_by_file():
    out = {}
    for path in glob.glob(str(ROOT / "script/*/*.json")):
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        out.setdefault(doc["file"], []).append(doc)
    return out


def rel_of(name):
    return "PAW.EXE" if name == "PAW" else f"DATA/{name}.BIN"


def name_of(rel):
    return "PAW" if rel == "PAW.EXE" else rel[5:-4]


def base_finder(f, entries, all_docs):
    """name -> RAM address of the file's offset 0, from the original disc."""
    import extract  # late: only the overlay base needs it

    bases = {"PAW": reloc.PAW_BASE}

    def base(name):
        if name not in bases:
            lba, n, size = entries["/" + rel_of(name)]
            bases[name] = extract.best_base(disc.read_user(f, lba, n)[:size], [x for d in all_docs[rel_of(name)] for x in d["entries"]])
        return bases[name]

    return base


def ref_bytes(all_docs, base):
    """{file: set of byte offsets a ref may rewrite}: refs live in any code, not only their string's own file."""
    allowed = {}
    for docs in all_docs.values():
        for doc in docs:
            for e in doc["entries"]:
                for ref in e.get("refs") or ():
                    name, at = ref.split(":")
                    word = at.startswith("w")
                    off = int(at[1:] if word else at, 16) - base(name)
                    span = 4 if word else (reloc.SEARCH + 1) * 4  # a lui and its low half, up to SEARCH words on
                    allowed.setdefault(rel_of(name), set()).update(range(off, off + span))
    return allowed


def ref_target(data, base, at):
    """The address one ref holds in a built file."""
    word = at.startswith("w")
    off = int(at[1:] if word else at, 16) - base
    if word:
        return struct.unpack_from("<I", data, off)[0]
    words = struct.unpack_from(f"<{reloc.SEARCH + 1}I", data, off)
    low = reloc.pair_low(words, 0)
    return None if low is None else reloc.resolves(words[0], words[low])


def read_back(all_docs, image, base):
    """(problems, {where: count}, {vacated RAM address: entry id}). image(rel) is a built file, decoded; base(name) its RAM address."""
    bad, counts, vacated = [], {"slot": 0, "far": 0, "moved": 0}, {}
    paw = image("PAW.EXE")

    def in_pool(addr, enc):
        off = addr - reloc.PAW_BASE
        return reloc.POOL_START <= off < reloc.POOL_END and paw[off:off + len(enc) + 1] == enc + b"\0"

    for rel, docs in all_docs.items():
        data = image(rel)
        for doc in docs:
            for e in doc["entries"]:
                if e["kind"] != "text":
                    continue
                if not e["en"]:
                    bad.append(f"{e['id']}: no English")
                    continue
                enc = en_text.encode(limits.fit(e, e["en"]))
                slot = bytes(data[e["off"]:e["off"] + e["len"]])
                if len(enc) <= limits.capacity(e):
                    counts["slot"] += 1
                    if slot != enc.ljust(e["len"], b"\0"):
                        bad.append(f"{e['id']}: slot holds {slot[:24].hex()}, not its English")
                elif e.get("refs") and not limits.far_only(e):
                    counts["moved"] += 1
                    vacated[base(name_of(rel)) + e["off"]] = e["id"]
                    if any(slot):
                        bad.append(f"{e['id']}: moved, but its slot still holds {slot[:24].hex()}")
                    for ref in e["refs"]:
                        name, at = ref.split(":")
                        addr = ref_target(image(rel_of(name)), base(name), at)
                        if addr is None or not in_pool(addr, enc):
                            bad.append(f"{e['id']}: ref {ref} doesn't reach its English")
                else:
                    counts["far"] += 1
                    addr = int.from_bytes(slot[2:6], "little")
                    if slot[:2] != bytes([limits.FAR_MARK, en_text.PAD]) or not in_pool(addr, enc):
                        bad.append(f"{e['id']}: far string doesn't reach its English")
    return bad, counts, vacated


def stale_readers(data, vacated):
    """Locations in a code file that still name a vacated address: aligned words, and lui with its low half."""
    words = np.frombuffer(data, "<u4", len(data) // 4)
    out = [(int(i) * 4, f"word {int(words[i]):08x}") for i in np.flatnonzero(np.isin(words, list(vacated)))]
    for i in map(int, np.flatnonzero(words >> 26 == 0x0F)):
        window = [int(w) for w in words[i:i + reloc.SEARCH + 1]]
        low = reloc.pair_low(window, 0)
        if low is not None and reloc.resolves(window[0], window[low]) in vacated:
            out.append((i * 4, f"lui to {reloc.resolves(window[0], window[low]):08x}"))
    return out


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


def main(path, shipped=True):
    import gfx  # declared rects per graphics file

    log = Path(path).with_suffix(".writes")
    if not log.is_file():
        sys.exit(f"{log}: no write log, rebuild")
    all_docs = docs_by_file()
    failures = []
    with open(ORIG, "rb") as fo, open(path, "rb") as fn:
        entries = {p: (lba, n, size) for p, lba, n, size in disc.walk(fo)}
        base = base_finder(fo, entries, all_docs)
        refs = ref_bytes(all_docs, base)
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
            ranges.append((lba * disc.SECTOR, (lba + n) * disc.SECTOR))
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
        report = ""
        if shipped:
            cache = {}

            def image(rel):
                if rel not in cache:
                    lba, n, size = entries["/" + rel]
                    raw = disc.read_user(fn, *moved[rel]) if rel in moved else disc.read_user(fn, lba, n)
                    lz = next((d["lz"] for d in all_docs.get(rel, []) if d["lz"] is not None), None)
                    # A spilled file's size grew: its stream knows its own length, and code files aren't spilled.
                    cache[rel] = lzkc.decompress(raw[lz:], strict=True) if lz is not None else raw[:size]
                return cache[rel]

            bad, counts, vacated = read_back(all_docs, image, base)
            failures += bad
            for p, (lba, n, size) in entries.items():
                if p == "/PAW.EXE" or p.startswith("/DATA/") and p.count("/") == 2 and p.endswith(".BIN") and 0 < n < 64:
                    # shortcut: an overlay's address means something else in another overlay of its slot, and PAW's overlay words are mostly entry points (tables at 0x93718, 0xa8680), so overlay strings are only looked for in their own file.
                    mine = {a: i for a, i in vacated.items() if i.startswith("PAW:") or i.split(":")[0] == name_of(p[1:])}
                    failures += [f"{p[1:]}+{at:x}: {what}: still names a moved string ({mine[int(what[-8:], 16)]})" for at, what in stale_readers(disc.read_user(fn, lba, n)[:size], mine)]
            report = f"; read back {counts['slot']} in place, {counts['moved']} moved, {counts['far']} far"
    ranges.append((SPILL_GAP[0] * disc.SECTOR, SPILL_GAP[1] * disc.SECTOR))
    for off, old, _, by in romdiff.load_writes(log):
        if not any(a <= off and off + len(old) <= b for a, b in ranges):
            failures.append(f"{by}: write at {off:x} outside every patched file and the gap")
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    rc = subprocess.call([sys.executable, str(ROOT / "tools/romdiff.py"), str(ORIG), str(path), "--writes", str(log)])
    if rc:
        sys.exit(rc)
    print(f"verify ok: {changed} files changed ({len(moved)} spilled), all inside their allowed ranges{report}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--not-shipped"]
    main(args[0] if args else ROOT / "build/paro_wars_en.bin", "--not-shipped" not in sys.argv)
