"""Extraction: every script/ entry re-encodes to the original bytes, and no Japanese on the disc sits outside script/ unexplained.

Unexplained = a kana-bearing Shift-JIS run that no entry covers, in a file not listed in tools/notext.tsv."""
import glob
import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import lzkc
from tbl import Table

TREE = ROOT / "work/disc/tree"
SCRIPT = sorted(glob.glob(str(ROOT / "script/*/*.json")))
need = pytest.mark.skipif(not TREE.exists() or not SCRIPT, reason="needs work/disc/tree and script/")
RUN = re.compile(rb"(?:[\x81-\x83\x88-\x97][\x40-\xfc])+")
SKIP_DIRS = ("SOUND", "STR", "DATA/BK_DT", "DATA/BTL", "DATA/ATAMA", "DATA/NYANTV")  # audio, video and pixels; read as images in phase 1
JP = Table.load(ROOT / "tbl/jp.tbl")


def docs():
    for path in SCRIPT:
        yield path, json.loads(Path(path).read_text(encoding="utf-8"))


def decoded(doc):
    raw = (TREE / doc["file"]).read_bytes()
    return raw if doc["lz"] is None else lzkc.decompress(raw[doc["lz"]:], strict=True)


def kana_runs(d, mask=b""):
    """(offset, text) of kana-bearing runs followed by NUL or the end of the data, skipping masked bytes."""
    for m in RUN.finditer(d):
        if len(m.group()) < 4 or (m.end() < len(d) and d[m.end()]):
            continue
        if mask and any(mask[m.start():m.end()]):
            continue
        try:
            s = m.group().decode("cp932")
        except UnicodeDecodeError:
            continue
        kana = sum(1 for c in s if 0x3041 <= ord(c) <= 0x30FF)
        if kana >= 2 and kana * 3 >= len(s):
            yield m.start(), s


def explained():
    out = []
    for line in (ROOT / "tools/notext.tsv").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            pattern, _reason = line.split("\t")
            out.append(re.compile(pattern))
    return out


@need
def test_every_entry_roundtrips():
    for path, doc in docs():
        d = decoded(doc)
        for e in doc["entries"]:
            enc = JP.encode(e["jp"])
            assert d[e["off"]:e["off"] + len(enc)] == enc, e["id"]
            assert len(enc) <= e["len"] and not any(d[e["off"] + len(enc):e["off"] + e["len"]]), f"{e['id']}: slot tail is not NUL"


@need
def test_entries_do_not_overlap_and_ids_are_unique():
    seen = set()
    for path, doc in docs():
        end = 0
        for e in sorted(doc["entries"], key=lambda e: e["off"]):
            assert e["off"] >= end, e["id"]
            assert e["id"] not in seen, e["id"]
            seen.add(e["id"])
            end = e["off"] + e["len"]


@need
def test_no_unexplained_japanese():
    """Runs on the original files outside entries. Compressed files are checked in their decoded form too."""
    allow = explained()
    covered = {}
    for path, doc in docs():
        mask = bytearray(len(decoded(doc)))
        mask[:doc["text_from"]] = b"\1" * doc["text_from"]
        for e in doc["entries"]:
            mask[e["off"]:e["off"] + e["len"]] = b"\1" * e["len"]
        covered[doc["file"]] = (doc["lz"], mask)
    bad = []
    for dp, _, names in os.walk(TREE):
        rel0 = os.path.relpath(dp, TREE).replace("\\", "/")
        if rel0.startswith(SKIP_DIRS):
            continue
        for n in names:
            rel = f"{rel0}/{n}".removeprefix("./")
            raw = open(os.path.join(dp, n), "rb").read()
            lz, mask = covered.get(rel, (None, b""))
            if lz is not None:
                raw = lzkc.decompress(raw[lz:], strict=True)
            elif lzkc.header_ok(raw):  # a whole-file stream we did not extract: read what it decodes to as well
                try:
                    plain = lzkc.decompress(raw, strict=True)
                except (ValueError, IndexError):
                    plain = b""
                if len(plain) >= len(raw) // 2:
                    raw += b"\0" + plain
            for off, s in kana_runs(raw, mask):
                if not any(p.search(f"{rel}\t{off:x}\t{s}") for p in allow):
                    bad.append(f"{rel}\t{off:x}\t{s}")
    assert not bad, f"{len(bad)} runs, first 40:\n" + "\n".join(bad[:40])
