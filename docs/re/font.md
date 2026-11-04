# Font and glyph path

**verified**: draw log `tools/debug/glyphs.lua` and `tools/font.py sheet`.

- Context struct at `0x800C44E0`: `+0x14E4` texture buffer `0x800FC528`, `+0x14E8` range table `0x800A3604`, `+0x14EC` font `0x800A36D0` (PAW.EXE file 0x93EC0).
- Font: full JIS level 1, ~3,490 cells, **18 bytes per cell**. The loader reads 17 bytes of 12x12 MSB-first packed bits; the 18th byte is a hash used for the cache slot (`0x800671E0`). In `font.py` the last row looks noisy for that reason.
- Range table: 52 `{u16 first_code, u16 first_cell}` entries, binary-searched by `0x800681EC`, returns -1 when not found. Sample: `0x8140->0`, `0x824F->147` (０), `0x8260->157` (Ａ), `0x8281->183` (ａ), `0x829F->209` (ぁ), `0x8340->292` (ァ), `0x889F->492` (亜). Check: 0x8CBB (現) = 1213 + 59 = cell 1272, matches the log.
- Cache: codes 0x824F-0x839E (latin, kana, 0x150 codes) have fixed slots; all others use 252 dynamic slots, 0xE7-0x1E2 (`0x80067868`), compared against `+0x111C`. So a screen can show about 252 different kanji at once.
- Glyph build, `0x8006725C`: expands 1bpp to 4bpp and adds an outline/shadow in a 32-pixel-wide work buffer, then uploads to VRAM.

## On screen
Story box: 12 px per character, 3 lines of 25 in a 320 px wide screen. Characters advance by a fixed 12 in the loop at `0x800677A0`. Whether each glyph is its own sprite or the line is composed into a texture is not settled: read the rest of that loop in phase 5, it decides the VWF plan.

## English plan (proposal, phase 5 decides and proves it)
A page is 150 bytes, 75 fullwidth characters: too small for English at one letter per code. Options, best first:
1. **Two letters per code (hook, no table):** a 16-bit code holds two ASCII bytes; the glyph loader hook builds the 12x12 cell from two half-cells at run time. 150 letters a page, 25 cells x 2 = 50 letters a line, no change to file formats or page sizes, works in every fixed field. Fixed 6 px pitch. Needs: a 5-6 px font in the kanji area of the font block, code range outside real SJIS or the range test moved. Odd-length names and runtime-inserted names need a half-cell pad (`pipeline.md` §Marker).
2. **Single-byte text + VWF:** nicer, but the 2-byte scan, pair swap, and control checks all assume halfwords, in at least two routines plus overlays.
3. Bigger pages: the story files have a fixed 8192 bytes and pages are indexed, so this needs engine changes too. Combine with 1 only if English still overflows.

Option 1 also frees the kanji cells for hook code and strings (`disc.md`).
