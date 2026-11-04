# Font and glyph path

**verified**: draw log `tools/debug/glyphs.lua`, full disassembly of the routines below, and the English renderer built on them boots and draws in every toured scene (`boxes.md`).

- Context struct at `0x800C44E0`: `+0x14E4` texture buffer `0x800FC528`, `+0x14E8` range table `0x800A3604`, `+0x14EC` font `0x800A36D0` (PAW.EXE file 0x93EC0).
- Font: full JIS level 1, ~3,490 cells, **18 bytes per cell**: 17 bytes hold **12x11** packed bits MSB first (132 bits; the loader expands 17 bytes, the upload takes 11 rows), and byte 18 is the cell's slot in the texture. `font.py` draws 12 rows, so its last row looks noisy.
- Range table: 52 `{u16 first_code, u16 first_cell}` entries, binary-searched by `0x800681EC`, returns -1 when not found. Sample: `0x8140->0`, `0x824F->147` (０), `0x8260->157` (Ａ), `0x8281->183` (ａ), `0x829F->209` (ぁ), `0x8340->292` (ァ), `0x889F->492` (亜). Check: 0x8CBB (現) = 1213 + 59 = cell 1272, matches the log.
- Slots: VRAM x=640, y=0, 21 cells a row of 12x11 at 4bpp, tpage word 0x2A (shadow 0x0A). Slot n sits at u = (n%21)*12, v = (n/21)*11.
  - **0-0xE6, fixed:** INIT.BIN (0x800016E4) loads codes 0x824F-0x839E at startup and stores each slot in byte 18 of the cell: digits, A-Z, a-z (0-61), hiragana (62-144), katakana (145-230).
  - **0xE7-0x1E2, dynamic:** every other code, 252 at once. Byte 18 + 0xE7 is the slot to try; the slot's code at `ctx+0x111C` confirms it.
- Glyph build, `0x8006725C`: 1bpp to 4bpp plus a 4-way outline (body 1, outline 2-8 by neighbour count), then a queued LoadImage.

## The text system
All text goes through one routine. Nothing else draws from this font (`mipsre.py calls` over PAW.EXE and every overlay: `0x8006725C` only from the draw loop and INIT).

Windows: 0x60 slots of 28 bytes at `ctx+0x680`; `ctx+0x5BD` active count, `ctx+0x5BF..` order. +0 type (0 one frame, removed after drawing; 1; 2+ typewriter), +1 revealed codes, +2/+3 shadow offset, +4 x, +6 y, +8 wrap column, +0xA clut, +0xC shadow clut, +0xE codes, +0x14 text, +0x18 flags (bit 0 shadow, bit 1 reveal, high nibble transform), +0x19 extra line gap.

Created by `0x80068270`, `0x8006837C`, `0x800684xx`, `0x80068748` (ctx, x, y, text, ...), each calling `0x80068838`: scan 2 bytes at a time until a byte below 5, store the count, and if that byte is 0 write 1 there and swap every pair, once only. So all text in RAM is little-endian halfwords, and a string must end on a halfword.

Draw: `0x80067640` per window, from `0x80067ED4`. Takes `count * 40` bytes of the frame's prim pool (twice with a shadow), one POLY_FT4 per glyph, x = window + column * 12, y = window + line * (12 + gap). Transformed windows (battle speech) get their corners from `0x800763A0`.

Pool: `ctx+0x1660`, `0x800C64F8 + buffer * 0xCE40`, 52,800 bytes a frame shared with everything else; in the map state (mode 4 sub 8) text gets its own 40,960 at `0x801CA000 + buffer * 0xA000`.

## English: VWF, two letters per code (**decided, proven in game**)
Options were: fixed 6 px two-letter cells built at run time; single-byte strings (the scan, swap and page handler all assume halfwords); bigger pages. Each glyph already being its own quad made a true VWF the cheapest: `asm/vwf.asm` replaces the draw loop (0x800677A0-0x80067CEC, compiled bloat, so the new loop, table and all fit inside it, with no free space used).
- A halfword below 0x8000 holds **two letters**, each drawn as its own quad at its own advance. From 0x8000 up it is still one fullwidth code at 12 px, so Greek for Koitsu and fullwidth digits keep working in the same string. `$s6` counts pixels now.
- Bytes: 0x20-0x7F letters (0x7F is `…`), 0x0A line break, 0x1F pad (nothing, no advance; `en_text.encode` adds it so strings and fullwidth codes stay on halfwords). Halfword 0x1E,n moves the pen to 2n px: `{x:N}` in the script, for fields around button icons.
- Glyphs live in the kana cells (`en_text.cell_offset`): letter 0x20 at cell 209, so the game's own INIT loads them into the fixed slots 62-157 with their outline. **Hiragana and part of katakana are gone**, so Japanese left in a build shows as garbled English: a leftover is easy to see. Digits, Latin and Greek cells are untouched.
- Each letter costs one quad, so the routine's pool share doubled (`sll` at 0x800676F8, 0x80067734). Peak pool use over the tour: 36,792 of 52,800 (`boxes_report.py`).
- The window's wrap column (byte 8) is **ignored**: English breaks only at `{br}`, which `tools/limits.py` `fit()` adds where a family wraps. Reason: dialog windows carry wrap 7 (84 px) in a box that shows 116 px, and it broke English mid-word (`work/qa/reloc/map_opening`).
- Font: `fonts/en12.txt`, drawn for this project. Capitals 8 rows, x-height 6, descenders 2, most letters 5 wide, M/W 7. Mean advance 5.3 px on English text, so a 300 px line holds about 57 letters.

## Budgets that follow
A fullwidth code is 12 px and two letters average 10.5 px, so **a byte budget and the Japanese pixel budget roughly agree**: a slot of n bytes holds about what the Japanese string's n/2 characters took on screen. Code that centres or places things by `count * 12` stays close too. Box widths: `boxes.md`.

## Moved strings
The kanji cells (cell 492 up, 53,964 bytes, RAM 0x800A5968+) are free once no kanji text is left, so **any string with `refs` can outgrow its slot**: `tools/reloc.py` puts it there and repoints every word and `lui`+low pair, checking each one really resolves to the old address. Proven in game on PAW and NSHOP_OV strings (`work/qa/reloc`). A `lui` whose register feeds a second low half refuses to move and the build says so. A kanji drawn from a reused cell would write its byte 18 there, so leftover kanji shows as a wrong glyph *and* damages a moved string: `jp_left` must be clean at release.
