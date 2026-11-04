# Text

## Encoding
Shift-JIS, fullwidth, no table needed. **verified**: the story box in savestate `work/qa/p1/0010` shows the bytes of `DEMO/TXT_PEN0.BIN` +0x96, and the glyph log (`tools/debug/glyphs.lua`) lists 0x8CBB 現, 0x8DDD 在, 0x94C9 繁, 0x8968 栄 for the next page. Half-width ASCII is not handled by this renderer (see below). Other print routines exist: not all are traced.

## Story-box engine (PAW.EXE) **verified by read breakpoints on the page in RAM** (`work/qa/d3`)
| Address | What |
|---|---|
| `0x80074C1C`, `0x80074CA0` | Page handler: tests the first halfword for control codes, keeps the page pointer at `4($s3)` |
| `0x80068838` | Prepare string: scans 2 bytes at a time until a byte < 5, stores the character count, writes 1 at a 0 terminator, then **swaps each pair in place** so the text is little-endian halfwords. A page in RAM is therefore unreadable as SJIS once shown. |
| `0x800677A0` | Draw loop over halfwords at `$s5` |
| `0x800671E0` / `0x800681EC` | Code to font cell (`font.md`) |
| `0x8006725C` | Load glyph into the texture cache |

Control values seen: a byte below 5 ends a string (scan above); `0x8140` 　 is a blank advance with no glyph; `0x814F` ＾ and `0x8197` ＠ are specials gated by the flag at `0x800C2728` (＠ ends a line in `ITEM.BIN`, **guess** that it is the line break everywhere); `0x8162` … has its own branch in the page handler (a run of three stores a value 6 into the text, **guess**: a pause). Reading those branches is phase 5 work.

## Formats
Offsets are in the decoded file for LZ families. `max` is what the original field holds; the engine spike (phase 5) sets real limits.

| Family | Files | Format | Text | State |
|---|---|---|---|---|
| `DEMO/TXT_{PEN,LOV,BAU,TAK,AIT,MOA,PAN,BUT}{0-6}` (raw) | 53 | 8192-byte file of **150-byte pages**: 25 fullwidth chars x 3 lines, padded with 0x8140 or 0x00. Page 0 is blank. Indexed by page, no pointers. | 2,915 pages, the story | **verified** page size; which control codes appear: scan in phase 4 |
| `ENDING/TXT_END` (raw), `ENDING/{PEN,LOV,BAU,TAK,KOI,MOA,PAN,BUT}_TXT` (LZ) | 9 | Same 150-byte pages, `name：「line」` | Endings | **verified** by decode |
| `P_00`-`P_73`, `P_<name>` (LZ at an offset) | ~86 | After the pixels: `◆強さ５段階評価◆`, stat lines, then description lines 52 bytes wide | Unit encyclopedia | **verified** on P_08 |
| `DEMO/KABE4` +0x10000 (LZ) | 1 | Country and unit data pages, fixed 26-byte lines | Country info | **guess** on the record shape |
| `X_<character>` (raw) | 12 | Header offsets, then records with `u32` fields + text in 0x3C-byte slots (from about +0x4B0): attack and reaction shouts | ~9,000 chars by `scan_jp.py` | **guess** on record layout; fixed stride **verified** by hexdump |
| `BAKU.BIN` (raw) | 1 | Shouts, 0x32-byte slots | | **guess** |
| `UNITINFO.BIN` (raw) | 1 | 40-byte records: name 30 bytes, 10 stat bytes | Commander names | **verified** by hexdump |
| `ITEM.BIN` +0 (raw) | 1 | 96-byte records: `name：description`, ＠ line break, 16 entries | Items | **verified** |
| `SEL_HELP.BIN` (raw) | 1 | Options help, 750 bytes, seen at RAM 0x80156800 | | **verified** in RAM |
| `SELECT`, `MEMCARD`, `NSHOP_OV`, `LOCS_OV`, `LOCEX_OV`, `HELP_OV`, `PROD_OV`, `OPT_OV`, `BEND_OV`, `BUTAI_OV`, `INFO_OV`, `SPLD_OV`, `SPABL_OV`, `JIRAI_OV`, `SKSN_OV`, `GORYU_OV`, `CNTRY_ST`, others (overlays) | ~25 | MIPS code + strings. First word is a small number (TITLE 0x0C, SELECT 0x0A, MEMCARD 0x0E; **guess**: overlay id). Strings sit in fixed slots, e.g. LOCS_OV +0x600 16/24/32-byte slots | Menus, shop, memory card, map chatter | **guess**: reached by `lui/addiu` as in the EXE |
| `PAW.EXE` | 1 | Strings at file 0x8B0-0xA80; unit records at 0x8F404 (stride 0x46, name first); weapon names at about 0x90C22 (stride 0x0E or 0x1C) | System messages, unit names, weapons | see Pointers |

Not text, despite the scan: `all_runs.txt` hits in BK_DT, MAP*, OP*, MAPUNIT*, PUP*, NYANTV, BAKU1-8 (pixels), and the filer padding (`disc.md`). `MEMCARD` +0x138 digit strings (`００００００１１１`) are **guess: data**, as are `bu00:` and the `バウ`/`パンダ`/`モアイ` short names next to them.

## Pointers
- PAW.EXE short strings are reached both ways. **verified** with `tools/mipsre.py xref`: `作戦行動中` by code at `0x8004687C`, `本当っすか` at `0x8004F6A0`, `が、ひろえない` by a word at `0x800A2D3C`, `全回復した` by `0x800A2D38`. So a moved string needs both word-table and `lui/addiu` fixes.
- Unit records are a table with base `0x8009EC14` (used by `0x80024EA8`, `0x8002D178`, ...) and fixed stride, so names keep their field widths or need the table's readers changed.
- Fixed fields are the rule across this game: English must fit the field or the engine must change. `(see font.md)`

## Open for phase 4
Every family needs its record boundaries confirmed by the coverage test. The scan filter (`tools/scan_jp.py`) misses kanji-only and two-character strings, so the extractor walks records and fixed slots rather than scanning, and `jp_left.py` runs after insertion.
