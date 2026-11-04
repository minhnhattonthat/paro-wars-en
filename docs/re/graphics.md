# Graphics text survey

Ruling D5: translate all of it; the パロウォーズ logo may stay because the art already has the official PARO WARS subtitle.

Images are raw pixels inside LZ files: no TIM headers except `CNTRY_ST`. Typical shape: 256 px wide, 8bpp, or 4bpp at 128 bytes a row, palette elsewhere (`COL_*`, `BKAO_COL`) or in the file header. Re-import goes through `tools/lzkc.py` and must fit the sectors (`disc.md`). Pixel formats per row are read from the sheets: **guess** until a re-import is proven in phase 8.

## Elements
| # | Element | Where seen | Source | Text | Work |
|---|---|---|---|---|---|
| 1 | Mode select: シナリオモード, マップバトルモード | tour, level select VRAM | `DEMO/KABE3` | large logo lettering | redraw |
| 2 | Prompts モードを選んで下さい, レベルを選んで下さい, キャラクターを..., マップを..., レベル, エネルギー, 視界, Z.O.C., むずかしい, やさしい, あり, なし, マップステータス | tour | `DEMO/KABE0` (others likely in KABE1, KABE2) | menu labels | redraw |
| 3 | Button bar: ○決定, ×戻る, □ヘルプ | tour | not found yet, in VRAM on select screens | small labels | find via VRAM dump + `vramfind.py` |
| 4 | Country plates, large: ペン太郎王国, ミカエル帝国, アカシヤランド共和国, こいつ＆あいつ連邦共和国, ラブリー連邦合衆国, モアイ諸島首長国, パンダ茶釜..., ニャー帝国 and more, with 主力兵器 / データ / VS | sweep; VS card in tour | `KABE4`, `DEMO/{BUT,PEN,AIT,...}*_0n` with this strip, e.g. BUT4_03, BUT5_01, BUT5_02, BUT6_01, PEN0_03, PEN1_04, PEN2_03 | country names | redraw; **many copies**: every scenario file carrying a strip |
| 5 | Country plates, small, on the story map: プリンス王国, グレート=ペンタ連邦, フィンフィン諸島王国, ２月７日島, ニャー大島, グウェート公国... | tour, sweep | `DEMO/WMAP0` (two sizes, ~21 names) | place names | redraw |
| 6 | Country pick list | sweep | `DEMO/KABE2` lower half | 8 names | redraw |
| 7 | Mission title cards: 北方の金塊 もらったり〜や！ etc. with furigana | tour (f003000) | `MTIT/MTIT1-12` (4bpp, 12 cards, 2-3 lines) | mission titles | redraw; drop furigana |
| 8 | Win banner かったっ!! (reading **guess**) | sweep | `BTLEND/WIN00-08` (one per country) | battle result | redraw, 9 files |
| 9 | Lose banner まけナッ!! (reading **guess**) | sweep | `BTLEND/LOS00-07` | battle result | redraw, 8 files |
| 10 | Map HUD country name: ペン太郎王国 in bottom bar | tour (f005500) | **guess**: `CNTRY_ST` or the STAFF-like strips; `X:`, `Y:`, `TURN:` are already English | | find via VRAM dump |
| 11 | Unit name plates beside unit art in battle intros: `09 コロシア`, `05 ボンジュールミラージュ` (some English: `00 Mig-J1`, `55 F-14`, `82 TWINBEE`) | sweep | `OP_00-23`, `OP_55`, `OP_81`, `OP_82`; similar plates in `OPF*`, `PUP_24-73` (small tag blocks, reading not checked) | one per unit, ~100 files | redraw, or text if a runtime overlay: check in-game. **Largest item** |
| 12 | Credits font | sweep | `ENDING/STAFF` (4bpp kanji + kana sheet: glyphs drawn by run time from a layout, **guess**) | | rebuild as English; layout table probably in `ENDING.BIN` |
| 13 | Title screen | tour | `ROGO` logo stays; `NEW GAME`, `CONTINUE`, copyright already English | | none |
| 14 | Memory card screens | sweep | `MCWGRPH` shows `MEMORY CARD` in English; the text around it is strings in `MEMCARD.BIN` | | check in tour |
| 15 | Map compass N/E/S/W, `TV` on the cat's hat, FIX.BIN digits and letters | tour, sweep | `FIX` | already Latin | none; check `FIX` kana cells in tour |

## Coverage: what this list does and does not rest on
- **Static sweep:** `tools/sweep.py` rendered 776 unique files on 65 sheets in `work/recon/sweep/` (index in `index.tsv`, every skipped family printed). I read 19 of the sheets: 1, 3, 7, 10, 15, 18, 19, 22, 25, 27, 28, 29, 31, 32, 33, 43, 44, 47, 49, 50, 61, 62, 63. The rest are siblings of those families (more DEMO scenario files, NYANTV, OP/OPF, PUP, P_), so element types should repeat but **individual rows and copies can be missing**. Read them before redrawing a family.
- **Large families, sampled only:** BK_DT 3,349 and BTL 2,115 and ATAMA 353, from `work/recon/sweep_s/`: backdrops, terrain and battle frames, no text in the sample. Not proven text-free; the marker tour in phase 5 is the check.
- **Tour so far:** title, mode select, level select, story map, story dialogue, VS card, mission card, tactical map. Not yet seen in game: unit command menus, battle scenes, shop, NYANTV, memory card, unit info pages, win/lose, game over, ending, credits. Phase 2's debug tool must reach those, and each adds rows here if something new shows up.
- Sheets are greyscale without palettes at fixed widths, so low-contrast or odd-width text can hide.
