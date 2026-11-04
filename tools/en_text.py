"""English text and font for the game's VWF (asm/vwf.asm, docs/re/font.md).

Text: two 7-bit letters per halfword. `{br}` is a line break, `{x:N}` moves the pen to N px (even) from the window's x, for fields around
button icons drawn at fixed places, `…` the ellipsis glyph; anything else non-ASCII (Greek for Koitsu, fullwidth digits)
stays one Shift-JIS code at 12 px and must start on a halfword, so a pad byte is inserted before it when needed. Strings end on a halfword too.
Font: each letter 0x20-0x7F takes a hiragana/katakana cell in PAW.EXE's font, so the game's own startup loads them into the fixed slots.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAD = 0x1F
BREAK = 0x0A
TAB = 0x1E  # a whole halfword: 0x1E, then the pen position / 2
TAB_RE = re.compile(r"\{x:(\d+)\}")
TAB_SPLIT = re.compile(r"\{x:(\d+)\}")
ELLIPSIS = 0x7F
FIRST = 0x20
COUNT = 96
FONT_FILE = 0x93EC0  # PAW.EXE file offset of cell 0
CELL = 18
HIRAGANA = 209  # first cell, code 0x829F; 83 cells, then katakana
KATAKANA = 292  # first cell, code 0x8340
ROWS = 11
COLS = 12


def load_font(path=ROOT / "fonts/en12.txt"):
    """{byte: rows}, each row a string of # and ., 10 rows at most. Comments start with # only before the first block."""
    glyphs, cur = {}, None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("="):
            name = line[1:]
            code = {"SP": 0x20, "ELL": ELLIPSIS}[name] if len(name) > 1 else ord(name)
            cur = glyphs.setdefault(code, [])
        elif cur is not None and line:
            cur.append(line)
    missing = [hex(c) for c in range(FIRST, FIRST + COUNT) if c not in glyphs]
    if missing:
        raise ValueError(f"no glyph for {missing}")
    for code, rows in glyphs.items():
        w = len(rows[0])
        if len(rows) > 10 or w > 10 or any(len(r) != w for r in rows):
            raise ValueError(f"glyph {code:#x}: {len(rows)} rows of {w}")
    return glyphs


FONT = load_font()
WIDTHS = bytes(len(FONT[c][0]) + 1 for c in range(FIRST, FIRST + COUNT))  # advance; asm reads it as width + 1


def cell_bytes(rows):
    """The first 17 bytes of a font cell, MSB first: 11 rows of 12 bits, glyph at column 1 and from row 1. Byte 18 stays 0 (the slot, set at startup)."""
    bits = 0
    for y in range(ROWS):
        row = rows[y - 1] if 1 <= y <= len(rows) else ""
        for x in range(COLS):
            on = 1 <= x <= len(row) and row[x - 1] == "#"
            bits = bits << 1 | on
    return (bits << (136 - ROWS * COLS)).to_bytes(17, "big")


def cell_offset(code):
    i = code - FIRST
    return FONT_FILE + (HIRAGANA + i if i < 83 else KATAKANA + i - 83) * CELL


def patch_font(exe):
    """Write every letter's cell into a PAW.EXE bytearray."""
    for code in range(FIRST, FIRST + COUNT):
        off = cell_offset(code)
        exe[off:off + 17] = cell_bytes(FONT[code])
        exe[off + 17] = 0


def encode(text):
    """Bytes for the game, even length, without the terminator."""
    out = bytearray()
    i = 0
    while i < len(text):
        c = text[i]
        if text.startswith("{br}", i):
            out.append(BREAK)
            i += 4
            continue
        tab = TAB_RE.match(text, i)
        if tab:
            px = int(tab[1])
            if px % 2 or px > 510:
                raise ValueError(f"{tab[0]}: even pixels, 510 at most")
            if len(out) & 1:
                out.append(PAD)
            out += bytes([TAB, px // 2])
            i = tab.end()
            continue
        i += 1
        if c == "…":
            out.append(ELLIPSIS)
        elif 0x20 <= ord(c) < 0x7F:
            out.append(ord(c))
        else:
            sjis = c.encode("cp932")
            if len(sjis) != 2:
                raise ValueError(f"{c!r} has no fullwidth code")
            if len(out) & 1:
                out.append(PAD)
            out += sjis
    if len(out) & 1:
        out.append(PAD)
    return bytes(out)


def line_width(text):
    """Pixels from pen start to the furthest the line reaches (a tab can go back). Fullwidth codes count 12, fullwidth digits and blanks 6 (asm/vwf.asm)."""
    w = widest = 0
    for i, part in enumerate(TAB_SPLIT.split(text)):  # odd parts are tab positions
        if i % 2:
            w = int(part)
            continue
        for c in part:
            o = ELLIPSIS if c == "…" else ord(c)
            w += WIDTHS[o - FIRST] if FIRST <= o < FIRST + COUNT else 6 if c == "　" or "０" <= c <= "９" else 12
        widest = max(widest, w)
    return widest


def _selftest():
    assert encode("ab") == b"ab"
    assert encode("abc") == b"abc\x1f"
    assert encode("a{br}b") == b"a\nb\x1f"
    assert encode("aκ") == b"a\x1f" + "κ".encode("cp932")
    assert encode("κa") == "κ".encode("cp932") + b"a\x1f"
    assert encode("…") == b"\x7f\x1f"
    assert encode("a{x:96}b") == b"a\x1f\x1e\x30b\x1f"
    assert line_width("ab{x:96}i") == 98
    assert line_width("{x:44}　　{x:0}a") == 56
    assert encode("a　") == b"a\x1f\x81\x40"
    assert len(WIDTHS) == COUNT and WIDTHS[0] == 4 and WIDTHS[ord("i") - FIRST] == 2
    c = cell_bytes(FONT[ord("|")])
    assert c[0] == 0 and c[1] >> 4 == 0 and len(c) == 17  # row 0 empty; row 1 starts at bit 12, its first pixel is column 1
    assert c[1] & 0x0F == 0b0100


if __name__ == "__main__":
    _selftest()
    print("ok; mean letter advance", sum(line_width(c) for c in "the quick brown fox jumps over the lazy dog ") / 44)
