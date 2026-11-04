"""The English renderer: encoder, font cells, and the assembled loop stays inside the routine it replaces."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import en_text

TREE = ROOT / "work/disc/tree"
BASE = 0x80010010 - 0x800
SPAN = (0x800677A0, 0x80067CEC)  # asm/vwf.asm replaces this
SIZES = (0x800676F8, 0x80067734)  # and these two shifts
need = pytest.mark.skipif(not (TREE / "PAW.EXE").exists() or not (ROOT / "tools/armips/armips.exe").exists(), reason="needs work/disc/tree and armips")


def test_encoder():
    en_text._selftest()


def test_every_letter_fits_its_cell():
    for code, rows in en_text.FONT.items():
        assert len(rows[0]) <= 10, hex(code)


def test_letter_cells_stay_in_kana():
    """Fixed slots end at cell 378 (0x8396); the loader only fills cells of the code range 0x824F-0x839E."""
    last = en_text.cell_offset(en_text.FIRST + en_text.COUNT - 1)
    assert last < en_text.FONT_FILE + 378 * en_text.CELL


@need
def test_hook_writes_only_its_span():
    orig = (TREE / "PAW.EXE").read_bytes()
    new = build.assemble(orig)
    assert len(new) == len(orig)
    allowed = {a - BASE for a in SIZES}
    lo, hi = SPAN[0] - BASE, SPAN[1] - BASE
    for off in range(0, len(orig), 4):
        if orig[off:off + 4] != new[off:off + 4]:
            assert lo <= off < hi or off in allowed, hex(off + BASE)


@need
def test_nothing_outside_branches_into_the_span():
    """The whole routine body moved; a branch from outside would land mid-hook. The loop head is fine."""
    code = (TREE / "PAW.EXE").read_bytes()[0x800:0xBC000]
    words = struct.unpack_from(f"<{len(code) // 4}I", code)
    bad = []
    for i, w in enumerate(words):
        pc = 0x80010010 + i * 4
        if SPAN[0] <= pc < SPAN[1]:
            continue
        op = w >> 26
        if op in (2, 3):
            target = (pc & 0xF0000000) | (w & 0x3FFFFFF) << 2
        elif op in (1, 4, 5, 6, 7):
            target = pc + 4 + ((w & 0xFFFF) - (0x10000 if w & 0x8000 else 0)) * 4
        else:
            continue
        if SPAN[0] < target < SPAN[1]:
            bad.append((hex(pc), hex(target)))
    assert not bad, bad


def test_markers_fit_their_slots():
    n = 0
    for doc in build.script_docs():
        for e in doc["entries"]:
            if e["kind"] != "text":
                continue
            n += 1
            enc = en_text.encode(build.marker_text(n, e, doc["group"]))
            assert len(enc) % 2 == 0 and len(enc) <= build.capacity(e), e["id"]
    assert n > 4000
