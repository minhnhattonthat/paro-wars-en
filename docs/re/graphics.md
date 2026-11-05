# Graphics text survey

Ruling D5: translate all of it; the パロウォーズ logo stays because no official English logo exists (Japan-only release). The art already carries a PARO WARS subtitle.

Images are raw pixels inside LZ files: no TIM headers except `CNTRY_ST`. Typical shape: 128 px wide 8bpp or 4bpp pages, palette elsewhere (`COL_*`, `BKAO_COL`) or in the file header. The tools: `tools/debug/vram_on.lua` dumps VRAM and RAM at a warp, `prims.py` lists the quads of a frame (walks the ordering table; misses some lists), `find_rect.py` finds a VRAM rect's file, `find_copies.py` the other files holding it. `tools/gfx_labels.py` is the table of redrawn labels, drawn by `tools/gfx.py` in the build; `gfx.py sheet OUT.png [REGEX]` shows old beside new without a build. `verify_build` only allows those files to change inside the declared rects.

## Elements
| # | Element | Source | State |
|---|---|---|---|
| 1 | Mode select: シナリオモード, マップバトルモード | `DEMO/KABE3` rows 0-103, 128-231 at VRAM 768,0 | redrawn, `select_mode` |
| 2 | Prompts, level and settings labels | `DEMO/KABE0` page at 896,0 | redrawn, `select_*`, `mb_*` |
| 3 | Button bar: 決定, 戻る, ヘルプ, 次, 前 | `DEMO/KABE0`, `KABE1` | redrawn |
| 4 | Nation plates with 主力兵器 / データ | `DEMO/KABE4` (8 columns), and 137 copies in 39 scenario files (`tools/gfx_copies.tsv`, from `find_copies.py`) | redrawn, `plate_*` |
| 5 | Place names on the story map | `DEMO/WMAP0`, 21 rows of 16 | redrawn to the Japanese field's width: the game places them so that field fits the map, and the map cuts anything longer |
| 6 | Map status: labels, 8 nation names | `DEMO/KABE2` row 128 and `KABE3` row 384 | redrawn, `mb_status` |
| 7 | Mission title cards | `MTIT/MTIT1-12`: atlas plus sprite table; the table is rewritten, the furigana are gone | redrawn, `card_*` |
| 8 | Win banner かちっ!! | `BTLEND/WIN00-08` | redrawn, `win` |
| 9 | Lose banner まけっ!! | `BTLEND/LOS00-07` | redrawn, `lose` |
| 10 | Map HUD nation name | `FIX` at 0xC000 | redrawn |
| 11 | "Number + name" labels beside unit art | `OP_*`, `PUP_*` | **not displayed: left alone.** The labels sit in empty atlas space beside the frames, like an artist's note. `battle_anim` has `OP_05` in VRAM at 768,256, and every quad on it samples only the frames (`prims.py`), never the label at x 56+, y 45+. `PUP_29`'s `戦車 SA-GO29` is the same kind of note. Inference from one battle plus the layout, not proven for all ~100 files |
| 12 | Staff roll | `ENDING/STAFF` (glyph sheet), `ENDING/SEQ_*` (16 files of sprite lists): `tools/credits.py` draws each English line as one strip and points each list at them, `tests/test_credits.py` | redrawn, `credits_roll`. The game keeps u + w in a byte, so a strip ending at u 256 draws backwards |
| 13 | Title screen | `ROGO` logo stays; the rest is already English | none |
| 14 | Saved game's row: シナリオ, nation, 第N章, ターン:, クリア | `MCWGRPH` at 0xC000, 4bpp, VRAM 928,0 | redrawn, `st_memsave` |
| 15 | Compass, `TV` on the cat's hat, FIX digits | `FIX` | already Latin |
| 16 | Signs on story backdrops: chess match, sing and dance contest, Panda's 茶会王様 | `DEMO/BACK10A`, `BACK11A`, `BACK13A` | redrawn over the art, `full_ait_4`, `full_moa_2` |
| 17 | `Thank you for playing this game!` | `ENDING/ENDKABE` | already English |
| 18 | Map bubbles: うすしおFC（警備中）, ごうか客船パロニャン子号 | `DEMO/PEN4_01` | redrawn, `full_pen_4` |
| 19 | Result lines beside the win banner | engine text | English, `win` |

## Coverage: what this list does and does not rest on
- **Static sweep:** `tools/sweep.py` rendered 776 unique files on 65 sheets in `work/recon/sweep/`, all read. No text in `P_*` or NYANTV. `DEMO/MOA3_01` has a "Bom" balloon, already English.
- **Large families, sampled only:** BK_DT 3,349 and BTL 2,115 and ATAMA 353 (backdrops, terrain, battle frames): no text in the sample. The tour is the check.
- **Tour:** every scene in `tools/debug/scenes.tsv` on the English build, including every story chapter page by page (`full_*`), read by visual QA (`qa_gate.py`). Screens no scene reaches: `flow.md`.
- Sheets are greyscale without palettes at fixed widths, so low-contrast or odd-width text can hide. The tour is what catches that.
