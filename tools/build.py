"""build.py: the patched disc from the pinned dump, every file kept at its LBA (docs/re/disc.md).

usage: build.py                     build/paro_wars_en.cue/.bin: `en` of every script entry that has one
       build.py --marker            build/paro_wars_marker.cue/.bin: every `text` entry shows its marker id (map in build/marker.tsv)
       build.py --qa ID=TEXT ...    override single entries, on either build
Formats of the families: docs/re/text.md. Font and renderer: docs/re/font.md, asm/vwf.asm."""
import argparse
import glob
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import check_rom
import disc
import en_text
import lzkc

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "rom" / "Paro Wars (Japan).bin"
BUILD = ROOT / "build"
FILLER = "The quick brown fox jumps over the lazy dog. "
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PAGE_PX = 290  # marker lines on a story page; the real limit is measured in docs/re/boxes.md


def marker_id(n):
    return DIGITS[n // 1296] + DIGITS[n // 36 % 36] + DIGITS[n % 36]


def capacity(entry):
    """Bytes of text a slot holds: a NUL must follow at a halfword."""
    return (entry["len"] - 1) & ~1


def fill_lines(head, cap, breaks):
    """head + filler up to cap bytes, wrapped at PAGE_PX, or with `breaks` line breaks spread evenly for shouts."""
    if breaks is None:
        out, line = "", head
        for ch in FILLER * 5:
            if en_text.line_width(line + ch) > PAGE_PX:
                out += line + "{br}"
                line = ""
            if len(en_text.encode(out + line + ch)) > cap:
                break
            line += ch
        return out + line
    out = head
    body = FILLER * 3
    per = max(1, (cap - len(head) - breaks) // (breaks + 1))
    for b in range(breaks + 1):
        out += body[b * per:(b + 1) * per]
        if b < breaks:
            out += "{br}"
    return out


def marker_text(n, entry, group):
    """The id and filler up to the slot's capacity. A tiny slot shows what it can of the id, so it can still be found in the map."""
    cap = capacity(entry)
    mid = marker_id(n)
    if cap < 4:
        return mid[-2:]
    if cap < 6:
        return mid
    head = "#" + mid
    if group in ("story", "ending"):
        return fill_lines(head + " ", cap, None)
    breaks = entry["jp"].count("{br}")
    if breaks:
        return fill_lines(head + " ", cap, breaks)
    return (head + " " + FILLER * 3)[:cap]


def script_docs():
    for path in sorted(glob.glob(str(ROOT / "script/*/*.json"))):
        yield json.loads(Path(path).read_text(encoding="utf-8"))


def splice(data, entry, text):
    enc = en_text.encode(text)
    if len(enc) > capacity(entry):
        raise ValueError(f"{entry['id']}: {len(enc)} bytes in a slot of {entry['len']}: {text!r}")
    data[entry["off"]:entry["off"] + entry["len"]] = enc.ljust(entry["len"], b"\0")


def assemble(exe):
    """asm/vwf.asm over a PAW.EXE image, in build/tmp."""
    tmp = BUILD / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "paw_in.exe").write_bytes(exe)
    (tmp / "widths.bin").write_bytes(en_text.WIDTHS)
    shutil.copy(ROOT / "asm/vwf.asm", tmp / "vwf.asm")
    subprocess.run([str(ROOT / "tools/armips/armips.exe"), "vwf.asm"], cwd=tmp, check=True)
    return bytearray((tmp / "paw_out.exe").read_bytes())


def build(marker, qa, out):
    with open(ORIG, "rb") as f:
        entries = {path: (lba, n, size) for path, lba, n, size in disc.walk(f)}

        def read(rel):
            lba, n, size = entries["/" + rel]
            return disc.read_user(f, lba, n)[:size]

        paw = assemble(read("PAW.EXE"))
        en_text.patch_font(paw)
        changed = {"PAW.EXE": paw}
        n = 0
        rows = []
        for doc in script_docs():
            lz = doc["lz"]
            rel = doc["file"]
            raw = changed.get(rel) or bytearray(read(rel))
            data = bytearray(lzkc.decompress(raw[lz:], strict=True)) if lz is not None else raw
            touched = False
            for e in doc["entries"]:
                if e["kind"] != "text":
                    continue
                n += 1
                text = e["en"]
                if marker:
                    text = marker_text(n, e, doc["group"])
                    rows.append(f"{marker_id(n)}\t{e['id']}\t{e['len']}\t{e['jp']}")
                if e["id"] in qa:
                    text = qa.pop(e["id"])
                if text:
                    splice(data, e, text)
                    touched = True
            if not touched:
                continue
            if lz is not None:
                stream = lzkc.compress(bytes(data))
                old_end = lz + 4 + int.from_bytes(raw[lz:lz + 3], "little")
                if any(raw[old_end:]) and len(stream) + lz > old_end:
                    raise ValueError(f"{rel}: data follows the stream and the stream grew by {len(stream) + lz - old_end}")
                raw = raw[:lz] + stream + raw[max(old_end, lz + len(stream)):]
            changed[rel] = raw
        if qa:
            raise ValueError(f"--qa ids not in the script: {sorted(qa)}")
    OUTBIN = BUILD / (out + ".bin")
    shutil.copyfile(ORIG, OUTBIN)
    with open(OUTBIN, "r+b") as f:
        files = []
        for rel, data in changed.items():
            lba, sectors, size = entries["/" + rel]
            if len(data) > sectors * 2048:
                raise ValueError(f"{rel}: {len(data)} bytes don't fit in {sectors} sectors")
            files.append(((lba, sectors, size), bytes(data)))
        disc.write_files(f, files)
    cue = ORIG.with_suffix(".cue").read_text(encoding="ascii")
    OUTBIN.with_suffix(".cue").write_text(cue.replace(ORIG.name, OUTBIN.name), encoding="ascii", newline="\r\n")
    if marker:
        (BUILD / "marker.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    with open(OUTBIN, "rb") as f:
        print(OUTBIN, hashlib.file_digest(f, "sha1").hexdigest(), f"{len(changed)} files patched")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marker", action="store_true")
    ap.add_argument("--qa", action="append", default=[])
    ap.add_argument("--out")
    a = ap.parse_args()
    check_rom.check()
    BUILD.mkdir(exist_ok=True)
    qa = dict(x.split("=", 1) for x in a.qa)
    build(a.marker, qa, a.out or ("paro_wars_marker" if a.marker else "paro_wars_en"))


if __name__ == "__main__":
    main()
