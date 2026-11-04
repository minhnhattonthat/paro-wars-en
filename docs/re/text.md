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
`tools/extract.py` dumps all of these to `script/<group>/<name>.json`. **verified** for every family by `tests/test_script.py`: each entry re-encodes to the disc's bytes, slots end in NUL only, and no kana run on the disc sits outside an entry unless `tools/notext.tsv` names it. Offsets are in the decoded file for LZ families. `len` is what the original field holds (NUL padding included; pages and fixed slots may fill it, strings need a NUL); the engine spike (phase 5) sets real limits.

| Group | Family | Files | Format | Entries of kind text |
|---|---|---|---|---|
| story | `DEMO/TXT_{PEN,LOV,BAU,TAK,AIT,MOA,PAN,BUT}{0-6}` (raw) | 53 | **150-byte pages**: 25 fullwidth chars x 3 lines, lines filled by 0x8140 runs, the page by 0x00. Page 0 is blank. Indexed by page, no pointers. The real pages stop well before the file's 8192 bytes; the rest is filer padding (the "2,915 pages" here before was file size / 150, wrong). | 867 pages, 43,605 chars |
| ending | `ENDING/TXT_END` (raw), `ENDING/{PEN,LOV,BAU,TAK,KOI,MOA,PAN,BUT}_TXT` (LZ at 0) | 9 | Same pages, `name：「line」` | 379 pages, 14,233 chars |
| units | `P_00`-`P_73`, `P_<name>` except P_BAKU, P_KEMU, P_MAP | 83 | LZ stream at the `u32` at +8. Text is the **last 0x234 bytes** decoded: 3 fields of 0x20 (`◆強さ５段階評価◆`, attack, defence), then 9 lines of 0x34 | 740 lines, 12,884 chars |
| data | `DEMO/KABE4` (LZ at 0) | 1 | Country pages after the pixels: from +0x10000, 26-byte lines, 8 countries x 33 lines; each block opens with the leader's title (`国王：`, `帝王：`, ...) | 212 lines |
| battle | `X_<character>` (raw) | 11 with text (X_AITU has none) | Shouts in 0x3C-byte slots from the first text (+0x390 to +0x508, differs per file) | 1,071 with BAKU, 10,828 chars |
| battle | `BAKU.BIN` (raw) | 1 | Shouts, 0x32-byte slots from +0x96C to +0x18DA | |
| data | `UNITINFO.BIN` (raw) | 1 | 40-byte records: name 26 bytes (flags at +26, stats at +30) | 288 names |
| data | `ITEM.BIN` +0 (raw) | 1 | 96-byte records: `name：description`, 16 entries | 16 |
| data | `SEL_HELP.BIN` (raw) | 1 | Options help, 50-byte lines (48 + 2 NUL), RAM 0x80156800 | 14 |
| menu | 34 overlays (ids in `flow.md`), 17 with text | | NUL-terminated strings in the data before the first prologue and after the last `jr ra`, NUL-padded to the next string | |
| menu | `PAW.EXE` | 1 | Three ranges: 0x89C-0xA90; 0x8F404-0x91E60 (tables, below); 0xA7160-0xB33B8 | 1,096 in the menu group, 7,784 chars |

`PAW.EXE` tables, read from the string offsets, all fixed stride, so the name fields can't grow without changing the readers: units 85 x 0x46 from 0x8F404 (name first, then stats); unit classes 37 x 0x0E from 0x90B50; weapons x 0x1C from 0x90DA0; ranks x 0x0A from 0x91764; personality types x 8 from 0x91824; buildings x 0x0A from 0x91844; terrain from 0x91932 (stride 6, then 0x0C from 0x919A0); **sentence endings** x 8 from 0x91BE0; battle complaints x 0x14 from 0x91CD8. What each table is called here is a **guess** from its contents; their readers aren't traced.

**Kinds in the JSON:** `text`; `blank` (spaces only); `num` (digits, Latin and symbols with no Japanese: templates such as `９９９`, and labels such as `ＳＭ－１`); `data` (bytes that only look like text, in the table areas listed in `extract.py` `DATA`, never translate). Translators get `text`; keep `num` until the font decision says otherwise.

**Things the translator and engine work have to know:**
- **Greek is text.** こいつ (Koitsu) speaks gibberish written in Greek letters (`κξαδμζθετρρ`) in story pages, KOI_TXT, LOCS_OV and HELP_OV, a joke. So phase 5 must keep Greek glyphs, and a rule for them is needed in the glossary. Whether it's a cipher wasn't checked.
- **Built-up messages, guess from the strings alone.** Fragments such as `は`, `を見つけた！！`, `になった！！`, `が、ひろえない` and `アップ！！` look glued to names at run time, and the table at 0x91BE0 (`です`, `だね`, `でポン`) looks like sentence endings for chatter. The English order may need the code changed: read the callers in phase 5.
- **Original typos** are kept in `jp`: a half-width `` ` `` in BAKU +0x17AE, half-width `ｨ` in the LOCS_OV strings at +0x12FC and +0x143C.
- ＠ (0x8197) decodes as `{br}`: seen only in the X_ files, ITEM and two PAW strings, and it is at a sensible line break in each one. ＾ and … never appear in text, so the page handler's branches for them don't matter.
- Runs of `　` inside a page are the original's line layout, not meaning; wrap tools must not copy them.

Not text, despite the scan (all in `tools/notext.tsv`): hits in OP*, OPF*, OB_SAB*, PUP*, BAKU0-8 and scenery (pixels), and the filer padding (`disc.md`). BK_DT, BTL, ATAMA and NYANTV are skipped by the coverage test as pixels. `MEMCARD` +0x138 digit strings (`００００００１１１`) are kind `num`.

## Pointers
- PAW.EXE short strings are reached both ways. **verified** with `tools/mipsre.py xref`: `作戦行動中` by code at `0x8004687C`, `本当っすか` at `0x8004F6A0`, `が、ひろえない` by a word at `0x800A2D3C`, `全回復した` by `0x800A2D38`. So a moved string needs both word-table and `lui/addiu` fixes.
- Unit records are a table with base `0x8009EC14` (used by `0x80024EA8`, `0x8002D178`, ...) and fixed stride, so names keep their field widths or need the table's readers changed.
- Fixed fields are the rule across this game: English must fit the field or the engine must change. `(see font.md)`
- **Every EXE and overlay entry has `refs`**: the `lui`+low pairs (`NAME:addr`) and aligned words (`NAME:waddr`) that reach it, across PAW.EXE and all overlays. **verified** as an extraction check: of the overlay `text` strings, all but 9 have a reference. The 9 are BUTAI_OV's country table (stride 0x18 from 0x23A0, first entry referenced) and LOCEX_OV +0x3608 (base plus offset). In PAW.EXE 231 of 508 have none, which is about what the tables above account for (not counted one by one). No check covers a string built some other way (`lw`/`lh` copies): the marker build shows those.

## Limits of the coverage test
It looks for kana. A kanji-only string in a file or range nothing extracts would pass it, so the marker build's tour and `jp_left.py` after insertion remain the check for those.
