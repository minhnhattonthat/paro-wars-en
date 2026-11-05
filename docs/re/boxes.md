# Text boxes: the width gate

**verified** in game on the marker build (`tools/build.py --marker`) unless a row says otherwise. Every window drawn on the tour is logged by `tools/debug/boxes.lua`; `tools/debug/boxes_report.py DIR...` joins the log to `build/marker.tsv`. Limits live in code, `tools/limits.py`, and `tests/test_limits.py` fails on any `en` that breaks one.

Screen 320x224. Pixels are from the window's own x. Advance: 5.3 px a letter on average, M/W 8, i 2. A fullwidth code (Greek) is 12.

| Family | Entries | Limit per line | Lines | Breaks | How it was measured |
|---|---|---|---|---|---|
| Story and ending pages (`DEMO/TXT_*`, `ENDING/*`) | 1,246 | 296; third line 284 (the page arrow) | 3 | tool | ruler page, `tools/debug/torture.sh`, zoomed shot: the frame's inner edge is x=308, the arrow starts at x=296 |
| Battle speech (`X_*`, `BAKU`) | 1,071 | 168 | 2 | tool | `battle_anim`, x=8 y=8 in a transformed window, 14 columns. Box beside the portrait |
| `LOCS_OV`, `HELP_OV` | 175 | 168 | 2 | tool | **guess**: shouts in the same voice, their screens not reached. 2 x 168 is safe in any box the Japanese fits, since those strings ran 22-24 columns |
| Dialog windows (`menu_tables.py`) | 41 ids | (w+1) x 16 - 12 - x | as the table | hand | formula from the `(7,3)` box at `map_opening`: 118 px outer, text x=14 ends by 116. `GORYU`, `JIRAI`, `SPABL`, `SPLD` use the same box from their tables but weren't reached: **formula, not seen** |
| Unit bios `P_*` | 740 | 300 | 1 per field | hand | `info_pages`, x=8, widest Japanese line. The text flows across fields: wrap by hand |
| `SEL_HELP` | 14 | 288 | 1 | hand | `mb_help`, x=16 |
| `DEMO/KABE4`, `UNITINFO` | 500 | 144 | 1 | hand | x=8 labels; commander names also float above units on the map, where the screen edge may crop them as the original does |
| `SELECT:54`, `:80`, `:134` | 3 | 96, 156, 96 | 3, 2, 2 | hand | they relied on the wrap column; lay them out with `{br}` and `{x:N}` |
| Everything else (labels, menus, tables) | ~1,000 | the Japanese string's own width | as JP | hand | conservative: what the original fits, the English fits. Loosen per string from a shot if a label truly can't fit |

**Bytes.** A string with `refs` can move (`tools/reloc.py`, `font.md`), so only its pixels bind. Without refs it must fit its slot: story pages 148, `X_*` 58, `BAKU` 48, `P_*` 50 or 30, `UNITINFO`/`KABE4` 24, and 240 PAW/BUTAI/LOCEX table strings.

**Button icons.** Strings starting with `　` (`　で決定`, `　で発射`) have a button drawn over the gap by the caller. English keeps the gap with `{x:N}`, in px from the window's x. Each one's gap is the number of leading `　` x 12.

**Strings the code changes or positions** (**verified** on shots and RAM dumps, `work/qa/p7g`, plus the static scan below). Enforced in `limits.py`: `TEMPLATES`, `HALFWORDS`, `CENTRED`.
- **Digit cells:** the code writes digits into fixed halfwords (`room.py --pokes`). Fullwidth digits and blanks draw at 6 px, so a field that relied on blanks for position needs a tab (fuel, `PAW:a8ac8`).
- **Counted from the end:** the writer at `0x80075ea4` (string, value, a2, a3) finds the string's end, puts the last digit at halfword `len-1-a3`, and goes left no further than `a2`. So the text after a digit is exactly `a3` halfwords, and a short string gets no digit at all: `３４０ウッキー` must stay 7 halfwords, or the hundreds digit is lost (340 showed as 40). `tools/debug/pokes.py` (in `tests/test_limits.py`) checks every call statically, so screens no tour reached count too: it found `３機スタック`, `３機輸送ＯＫ`, `３機輸送中`, `あと３機`, `（３部隊）` with no digit. Its candidates are the strings named just before each call whose Japanese has blanks or digits in those cells; a string computed elsewhere is covered only if it's in `TEMPLATES`.
- **The save file's title** (`limits.SAVE_TITLE`): MEMCARD `0x801510f0` builds the 32 Shift-JIS cells of the card's directory title from `MEMCARD:ac`, a nation, and `bc` or `ec` by `strncpy`, then writes digits back from cell 32. This game never draws it; the console's card manager does, so it takes real fullwidth letters and no tabs, and each piece must be exactly its copy's length, or its terminator cuts the title. Read from `tools/pcsx/memcard1.mcd` after saving in game: `Ｐ．Ｗａｒｓ　Ｐｅｎ．Ｃｈ１　　　　１Ｔｕｒｎ　００：００：３７`. The manager's own display is not seen. The row the game draws on its save screen is a separate thing, Japanese art (`graphics.md` row 14).
- **Cut after the digits:** the commander panel (`PAW:a9054` family) ends the string after halfword 4, so a label past the digits is never drawn, and only the 2 halfwords before them hold text: 4 letters. A tab can't help.
- **All but the first halfword blanked:** the unit list's defense cells (`BUTAI_OV:2594-25a4`): the labels live in `Defense:` (`25ac`) with tabs, and the cell's one safe halfword is a tab past them.
- **Centred by count:** many labels are drawn at `centre - 6 * halfwords` (`CNTRY_ST:5xx`, unit info's first column). At 4 halfwords the first letter goes under the frame. A leading `{x:12}` costs one halfword (6 px left) and gains 12. Right-aligned by count: `BUTAI_OV:2500` Move, the cost column.

**Not text, decided here.**
- Greek in battle boxes (`83bf-83d6`, `80149be0`): Koitsu's gibberish, stays as is, and Greek cells are kept.
- `tools/jp_left_files.py` after the marker build: 14 two-character hits (`ф恒`, `成博`, ...), none a string: `mipsre.py xref` finds no reference to any, and the two read as code disassemble to instructions.
- Windows whose `ptr` is `80170xxx`/`8014b004`: stale slots holding leftover bytes (`boxes_report` lists them), no quad drawn for them on any sheet.

**Seen in phase 8:** HELP_OV and LOCS_OV (`help_*`, `locs_*`): the shout box has about 250 px beside the portrait and 2 lines, so 168 is safe. **Not reached in game:** GORYU, JIRAI, SPABL, HOKYU, ITCHG, HASN, HISS (`flow.md`). Their limits above are safe by construction, not seen. `BAKU` was not seen either (same shout path as `X_*` by its 0x32 slots, **guess**).

**Marker tour.** Last full run on build `e0ae8b30`: 172/172 scenes reached, 737 of 4,683 entries seen, pool peak 36,792 of 52,800 (`ending_ait`), `work/qa/final`. Many entries of a family stay unseen because each scene shows a few of them; the width gate needs each *box*, not each line, and all entries of a family share it.
