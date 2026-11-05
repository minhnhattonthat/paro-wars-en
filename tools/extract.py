"""Phase 4: dump every text family from work/disc/tree into script/<group>/<name>.json.

usage: extract.py [--force]   without --force only missing files are written; --force rewrites but keeps en/status/notes by id.

Each file: {"file", "lz" (stream offset or null), "group", "text_from", "entries": [...]}. Each entry: id, off (in the decoded file),
len (slot bytes), jp, en, status, kind, and refs (code/word addresses reaching it, EXE and overlays only).
kind: text = translate; blank = spaces only; num = digits or symbols only (runtime templates); data = not text, never translate.
Formats and how far they are proven: docs/re/text.md. tests/test_script.py checks roundtrip and coverage.
"""
import glob
import json
import os
import re
import struct
import sys
from pathlib import Path

import lzkc
from tbl import Table

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
OUT = ROOT / "script"
JP = Table.load(ROOT / "tbl" / "jp.tbl")

SLOTS = [0x8014B000, 0x80155800, 0x8015C800, 0x80160000, 0x80188000, 0x80154000]  # overlay load addresses, docs/re/flow.md
PAW_BASE = 0x80010010
PAW_LOADED = 0xBC000  # boot loads only this much of PAW.EXE (docs/re/disc.md)
PAW_TEXT = [(0x89C, 0xA94),(0x8F404, 0x91E60), (0xA7160, 0xB33B8)]  # read by hand; the rest is code, font and tables

OVERLAY_IDS = ["INIT", None, "SELECT", "MAP_DEMO", "GAME_OV", "ENDING", "OPT_OV", "CNTRY_ST", "PROD_OV", "ALLMP_OV", "LOCS_OV", "SUIM_OV",
               "HOKYU_OV", "MEMCARD", "SPLD_OV", "SPABL_OV", "GORYU_OV", "ITCHG_OV", "NSHOP_OV", "SP_WDBZK", "SP_RNBW", "SP_FRST", "SKSN_OV",
               "LOCEX_OV", "BEND_OV", "SP_ICBM", "ATDM_OV", "BUTAI_OV", "INFO_OV", "SPAUR_OV", "SPELK_OV", "JIRAI_OV", "HISS_OV", "HASN_OV", "HELP_OV"]

# Ranges inside overlays that hold bytes which only look like text. Checked by eye against the dump. (start, end, reason)
DATA = {
    "ENDING": [(0x3900, 0x10000, "tables after the code")],
    "INIT": [(0, 0x10000, "tables, no text in this overlay")],
    "MEMCARD": [(0xE6E4, 0x20000, "tables and a font map after the code")],
    "SELECT": [(0xA6AC, 0x10000, "tables after the code")],
    "SPABL_OV": [(0x1F10, 0x10000, "tables after the code")],
}
TEXT_FROM = {}  # name: decoded offset where pixels end; the coverage test ignores everything before it


def dbl(a, b):
    return (0x81 <= a <= 0x84 or 0x88 <= a <= 0x9F or 0xE0 <= a <= 0xEA) and 0x40 <= b <= 0xFC and b != 0x7F


def text_len(d, start, end, ascii_ok=True):
    """Length of the text run at start. BAKU +0x17AE has a stray half-width `, LOCS_OV +0x12FC a stray half-width ｨ between
    full-width characters; elsewhere ASCII next to text is table data."""
    i = start
    while i < end:
        if i + 1 < end and dbl(d[i], d[i + 1]):
            i += 2
        elif ascii_ok and 0x20 <= d[i] < 0x7F:
            i += 1
        elif i > start and 0xA1 <= d[i] <= 0xDF and i + 2 < end and dbl(d[i + 1], d[i + 2]):
            i += 1
        else:
            break
    return i - start


def classify(s):
    if not s.strip("　 "):
        return "blank"
    body = s.replace("{br}", "")
    if re.search(r"\[[0-9A-F]{2}\]", body):
        return "data"
    if not re.search(r"[ぁ-ヶー一-龠々α-ωΑ-Ω・！～…、。「」]", body):  # digits, Latin, symbols: templates and labels. Punctuation lines are text
        return "num"
    for c in body:
        o = ord(c)
        if 0x400 <= o <= 0x45F or 0x2500 <= o <= 0x257F:  # Cyrillic, box drawing: never in this script. Greek is Koitsu's joke language
            return "data"
        if 0x4E00 <= o <= 0x9FFF and c.encode("cp932") >= b"\x98\x9f" and not re.search(r"[ぁ-んァ-ヶ]", body):  # JIS level 2 alone
            return "data"
    return "text"


def entry(name, off, n, slot, d):
    jp = JP.decode(d, off, length=n)[0]
    return {"id": f"{name}:{off:x}", "off": off, "len": slot, "jp": jp, "en": "", "status": "todo", "kind": classify(jp)}


def slots(name, d, offs):
    """Fixed fields: (off, size). A field is text + NUL padding; one that is not stays out and the coverage test reports it."""
    out = []
    for off, size in offs:
        field = d[off:off + size]
        n = text_len(d, off, off + size)
        if n and not any(field[n:]):
            out.append(entry(name, off, n, size, d))
    return out


def walk(name, d, start, stride):
    """Slots from start until the first that is neither text + NUL nor all NUL."""
    offs = []
    off = start
    while off + stride <= len(d):
        field = d[off:off + stride]
        n = text_len(d, off, off + stride)
        if any(field[n:]):
            break
        offs.append((off, stride))
        off += stride
    return slots(name, d, offs)


def first_text(d, start=0):
    m = re.compile(rb"(?:[\x81-\x83\x88-\x97][\x40-\xfc]){3,}\x00").search(d, start)
    return m.start() if m else None


def nul_strings(name, d, ranges):
    """NUL-terminated strings, each with the NUL padding that follows as its slot. Fixed tables can hold them at 2-aligned starts."""
    out = []
    for lo, hi in ranges:
        i = lo
        while i < hi:
            if d[i] == 0:
                i += 1
                continue
            n = text_len(d, i, hi, ascii_ok=False)
            if n and (i + n >= len(d) or d[i + n] == 0):
                j = i + n
                while j < hi and d[j] == 0:
                    j += 1
                out.append(entry(name, i, n, j - i, d))
                i = j
            else:
                i += max(n, 1)
    return out


def data_regions(d):
    """An overlay's data: before the first prologue and after the last jr ra. tests/test_script.py scans the code between them."""
    words = struct.unpack_from(f"<{len(d) // 4}I", d)
    first = next((i * 4 for i, w in enumerate(words) if w >> 16 == 0x27BD and w & 0x8000), 0)
    last = max((i * 4 + 8 for i, w in enumerate(words) if w == 0x03E00008), default=0)
    return [(0, first), (last, len(d))]


def code_refs(data, base, tag, index):
    """Every lui+low pair and every aligned word that lands on an address in index: fills index[addr] with tag:location."""
    words = struct.unpack_from(f"<{len(data) // 4}I", data)
    for i, w in enumerate(words):
        if w in index:
            index[w].append(f"{tag}:w{base + i * 4:08x}")
        if w >> 26 == 0x0F:
            reg, hi = w >> 16 & 31, w & 0xFFFF
            for j in range(i + 1, min(len(words), i + 9)):
                x = words[j]
                if x >> 26 in (0, 0x0F) or x >> 21 & 31 != reg:
                    continue
                addr = ((hi << 16) + (x & 0xFFFF) - (0x10000 if x & 0x8000 else 0)) & 0xFFFFFFFF
                if addr in index:
                    index[addr].append(f"{tag}:{base + i * 4:08x}")
                break


def best_base(d, strings):
    """The overlay slot whose lui+low pairs reach the most strings. Loader records store no address (docs/re/flow.md slots)."""
    best, score = SLOTS[0], -1
    for slot in SLOTS:
        index = {slot + e["off"]: [] for e in strings}
        code_refs(d, slot, "", index)
        hits = sum(1 for v in index.values() if v)
        if hits > score:
            best, score = slot, hits
    return best


def read(rel):
    return open(TREE / rel, "rb").read()


def lz_at(d, off):
    return lzkc.decompress(d[off:], strict=True)


def families():
    """Yields (group, rel, lz, name, entries, base)."""
    for f in sorted(glob.glob(str(TREE / "DATA/DEMO/TXT_*.BIN"))):
        rel = "DATA/DEMO/" + os.path.basename(f)
        d = read(rel)
        name = rel[5:-4]
        yield "story", rel, None, name, walk(name, d, 0, 150), None
    raw = read("DATA/DEMO/KABE4.BIN")  # country info: 8 countries x 33 lines of 26 bytes, after the pixels
    d = lz_at(raw, 0)
    TEXT_FROM["DEMO/KABE4"] = 0x10000
    yield "data", "DATA/DEMO/KABE4.BIN", 0, "DEMO/KABE4", walk("DEMO/KABE4", d, 0x10000, 26), None
    for f in sorted(glob.glob(str(TREE / "DATA/ENDING/*.BIN"))):
        base = os.path.basename(f)
        if not (base == "TXT_END.BIN" or base.endswith("_TXT.BIN")):
            continue
        rel = "DATA/ENDING/" + base
        raw = read(rel)
        lz = None if base == "TXT_END.BIN" else 0
        d = raw if lz is None else lz_at(raw, 0)
        name = rel[5:-4]
        yield "ending", rel, lz, name, walk(name, d, 0, 150), None
    for f in sorted(glob.glob(str(TREE / "DATA/P_*.BIN"))):
        base = os.path.basename(f)
        rel = "DATA/" + base
        raw = read(rel)
        off = struct.unpack_from("<I", raw, 8)[0]
        if base in ("P_BAKU.BIN", "P_KEMU.BIN", "P_MAP.BIN"):  # effect graphics, no text page
            continue
        d = lz_at(raw, off)
        t = len(d) - 0x234  # last 0x234 bytes: 3 fields of 0x20, 9 lines of 0x34
        offs = [(t + i * 0x20, 0x20) for i in range(3)] + [(t + 0x60 + i * 0x34, 0x34) for i in range(9)]
        name = base[:-4]
        TEXT_FROM[name] = t
        yield "units", rel, off, name, slots(name, d, offs), None
    for f in sorted(glob.glob(str(TREE / "DATA/X_*.BIN"))):
        base = os.path.basename(f)
        rel = "DATA/" + base
        d = read(rel)
        name = base[:-4]
        start = first_text(d)  # X_AITU has no text
        yield "battle", rel, None, name, [] if start is None else walk(name, d, start, 0x3C), None
    d = read("DATA/BAKU.BIN")
    yield "battle", "DATA/BAKU.BIN", None, "BAKU", walk("BAKU", d, first_text(d), 0x32), None
    d = read("DATA/UNITINFO.BIN")
    yield "data", "DATA/UNITINFO.BIN", None, "UNITINFO", slots("UNITINFO", d, [(i, 26) for i in range(0, len(d), 40)]), None  # flags at +26, stats at +30
    d = read("DATA/ITEM.BIN")
    yield "data", "DATA/ITEM.BIN", None, "ITEM", slots("ITEM", d, [(i, 96) for i in range(0, 0x600, 96)]), None
    d = read("DATA/SEL_HELP.BIN")
    yield "data", "DATA/SEL_HELP.BIN", None, "SEL_HELP", slots("SEL_HELP", d, [(i, 50) for i in range(0, len(d), 50)]), None
    paw = read("PAW.EXE")
    yield "menu", "PAW.EXE", None, "PAW", nul_strings("PAW", paw, PAW_TEXT), PAW_BASE - 0x800
    for i, ov in enumerate(OVERLAY_IDS):
        if ov is None:
            continue
        rel = f"DATA/{ov}.BIN"
        d = read(rel)
        strings = nul_strings(ov, d, data_regions(d))
        yield "menu", rel, None, ov, strings, best_base(d, strings)


def add_refs(all_files):
    """Index EXE and overlay string addresses, then fill refs from the code that reaches them."""
    paw = read("PAW.EXE")
    overlays = [(rel, read(rel), base) for _, rel, _, _, _, base in all_files if base and rel != "PAW.EXE"]
    paw_index = {PAW_BASE - 0x800 + e["off"]: [] for g, rel, _, _, es, b in all_files if rel == "PAW.EXE" for e in es}
    code_refs(paw[0x800:PAW_LOADED], PAW_BASE, "PAW", paw_index)
    for rel, d, base in overlays:
        name = rel[5:-4]
        code_refs(d, base, name, paw_index)
        own = {base + e["off"]: [] for g, r, _, _, es, b in all_files if r == rel for e in es}
        code_refs(d, base, name, own)
        for g, r, _, _, es, b in all_files:
            if r == rel:
                for e in es:
                    e["refs"] = own[base + e["off"]]
    for g, rel, _, _, es, b in all_files:
        if rel == "PAW.EXE":
            for e in es:
                e["refs"] = paw_index[PAW_BASE - 0x800 + e["off"]]


def merge(old, entries):
    keep = {e["id"]: e for e in old["entries"]}
    for e in entries:
        o = keep.get(e["id"])
        if o:
            for k in ("en", "status", "notes", "kind"):  # kind too: a label classify() reads as num can be set to text by hand
                if k in o:
                    e[k] = o[k]


def main():
    force = "--force" in sys.argv
    all_files = list(families())
    add_refs(all_files)
    written = 0
    for group, rel, lz, name, entries, _ in all_files:
        for lo, hi, why in DATA.get(name, ()):
            for e in entries:
                if lo <= e["off"] < hi:
                    e["kind"] = "data"
                    e["notes"] = why
        path = OUT / group / f"{name.replace('/', '_')}.json"
        if path.exists():
            if not force:
                continue
            merge(json.loads(path.read_text(encoding="utf-8")), entries)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = {"file": rel, "lz": lz, "group": group, "text_from": TEXT_FROM.get(name, 0), "entries": entries}
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        written += 1
    total = sum(len(f[4]) for f in all_files)
    print(f"{len(all_files)} files, {total} entries, {written} written")


if __name__ == "__main__":
    main()
