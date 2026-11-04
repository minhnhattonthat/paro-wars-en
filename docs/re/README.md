# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise. RAM address = PAW.EXE file offset - 0x800 + 0x80010010.

| File | Covers | State |
|---|---|---|
| [disc.md](disc.md) | Disc layout, the two EXEs, file-record tables, free space | records verified; loaders partly guessed |
| [compression.md](compression.md) | The LZ codec | verified (disassembly + roundtrip test) |
| [text.md](text.md) | Encoding, control codes, text families and their formats, pointers | engine verified on the story path; other paths guessed |
| [font.md](font.md) | The 12x12 font, glyph cache, options for English | font verified; English plan is a proposal for phase 5 |
| [graphics.md](graphics.md) | Survey of Japanese drawn as graphics | static sweep and first tour; see its coverage notes |

## Prior work
No earlier patch, tools or format notes found (two web searches, 2026-11-05): no romhacking.net entry turned up. A
[GameFAQs thread](https://gamefaqs.gamespot.com/boards/573351-paro-wars/79825811) links a "translation video", contents unknown,
not opened. The [Gradius wiki page](https://gradius.fandom.com/wiki/Paro_Wars) is a source to check for official name spellings
in phase 6. Later reissue: Konami the Best, SLPM-86392, not this dump.

## Tools
`tools/mipsre.py` (disassembly, xref, BIOS stubs), `tools/lzkc.py` (codec), `tools/unpack_all.py`, `tools/lz_embed.py`,
`tools/font.py`, `tools/disc_tables.py`, `tools/scan_jp.py`, `tools/sweep.py`, `tools/bitmap.py`, `tools/ramfind.py`, `tools/ramscan.py`,
`tools/classify.py`, `tools/debug/glyphs.lua`. Run the Unpack command in AGENTS.md first.
