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
SIZES = (0x800676F8, 0x80067734, 0x8004FD78)  # and these two shifts, and the unit box's ？ offset
PREP = (0x80068838, 0x800688CC)  # and the string prepare, for far strings
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
    for off in range(0, len(orig), 4):
        if orig[off:off + 4] != new[off:off + 4]:
            assert any(lo - BASE <= off < hi - BASE for lo, hi in (SPAN, PREP)) or off in allowed, hex(off + BASE)


@need
def test_prepare_routine():
    """The rewritten prepare under an interpreter small enough to trust: near string, far string, already prepared."""
    code = build.assemble((TREE / "PAW.EXE").read_bytes())[PREP[0] - BASE:PREP[1] - BASE]
    uc = pytest.importorskip("unicorn")
    mips = uc.Uc(uc.UC_ARCH_MIPS, uc.UC_MODE_MIPS32 | uc.UC_MODE_LITTLE_ENDIAN)
    from unicorn import mips_const as r

    def run(text_at, memory):
        mips.mem_map(0, 0x10000)
        mips.mem_write(0x1000, bytes(code))
        for at, data in memory.items():
            mips.mem_write(at, data)
        mips.reg_write(r.UC_MIPS_REG_A0, 0x8000)
        mips.reg_write(r.UC_MIPS_REG_A1, text_at)
        mips.reg_write(r.UC_MIPS_REG_RA, 0x2000)
        mips.emu_start(0x1000, 0x2000, count=4000)
        window = bytes(mips.mem_read(0x8000, 0x18))
        result = (struct.unpack_from("<H", window, 0xE)[0], struct.unpack_from("<I", window, 0x14)[0])
        out = {at: bytes(mips.mem_read(at, len(data))) for at, data in memory.items()}
        mips.mem_unmap(0, 0x10000)
        return result, out

    assert run(0x3000, {0x3000: b"AbCd\0\0"}) == ((2, 0x3000), {0x3000: b"bAdC\1\0"})
    far = bytes([0x1C, 0x1F]) + struct.pack("<I", 0x4000)
    assert run(0x3000, {0x3000: far, 0x4000: b"AbCd\0\0"}) == ((2, 0x4000), {0x3000: far, 0x4000: b"bAdC\1\0"})
    assert run(0x3000, {0x3000: b"bAdC\1\0"}) == ((2, 0x3000), {0x3000: b"bAdC\1\0"})  # shown before: no second swap
    assert run(0x3000, {0x3000: b"\0\0"}) == ((0, 0x3000), {0x3000: b"\1\0"})


@need
def test_nothing_outside_branches_into_the_span():
    """The whole routine body moved; a branch from outside would land mid-hook. The loop head is fine."""
    code = (TREE / "PAW.EXE").read_bytes()[0x800:0xBC000]
    words = struct.unpack_from(f"<{len(code) // 4}I", code)
    bad = []
    for i, w in enumerate(words):
        pc = 0x80010010 + i * 4
        if SPAN[0] <= pc < SPAN[1] or PREP[0] <= pc < PREP[1]:
            continue
        op = w >> 26
        if op in (2, 3):
            target = (pc & 0xF0000000) | (w & 0x3FFFFFF) << 2
        elif op in (1, 4, 5, 6, 7):
            target = pc + 4 + ((w & 0xFFFF) - (0x10000 if w & 0x8000 else 0)) * 4
        else:
            continue
        if SPAN[0] < target < SPAN[1] or PREP[0] < target < PREP[1]:
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
