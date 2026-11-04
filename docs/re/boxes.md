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

**Not text, decided here.**
- Greek in battle boxes (`83bf-83d6`, `80149be0`): Koitsu's gibberish, stays as is, and Greek cells are kept.
- `tools/jp_left_files.py` after the marker build: 14 two-character hits (`ф恒`, `成博`, ...), none a string: `mipsre.py xref` finds no reference to any, and the two read as code disassemble to instructions.
- Windows whose `ptr` is `80170xxx`/`8014b004`: stale slots holding leftover bytes (`boxes_report` lists them), no quad drawn for them on any sheet.

**Not reached in game.** HELP_OV, LOCS_OV, GORYU, JIRAI, SPABL, SPLD, HOKYU, ITCHG, HASN, HISS: phase 8 should try again from a real battle, and these are listed for it in `docs/status.md`. Their limits above are safe by construction, not seen. `BAKU` was not seen either (same shout path as `X_*` by its 0x32 slots, **guess**).

**Marker tour.** Last full run on build `e0ae8b30`: 172/172 scenes reached, 737 of 4,683 entries seen, pool peak 36,792 of 52,800 (`ending_ait`), `work/qa/final`. Many entries of a family stay unseen because each scene shows a few of them; the width gate needs each *box*, not each line, and all entries of a family share it.
