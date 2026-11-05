# Game flow and state variables

All **verified** with `tools/debug/trace.lua` plus warps that land where the table says, unless marked otherwise. Blocks: `CTX` = 0x800C44E0, `G` = 0x800E0178.

## Boot
`SLPM_860.16` (logos, intro STR, title) writes a byte at 0x80010000, then loads PAW.EXE:
- 0: NEW GAME. 2: CONTINUE. 1: attract demo.
- Start skips the intro and enables the menu; start again confirms. Any other button mashed at the title starts the demo instead (0x800D3BA4 path, flag at `CTX`-style boot block +0x1544).
- PAW sets `CTX+0x157C` (demo) or `CTX+0x1584` (continue) from that byte (0x80012304).

## Modes
`CTX+0x1548` = mode, `CTX+0x1550` = its sub-state; `CTX+0x1558` is the step inside a sub-state. Table 0x800A2F04. A mode's sub 0 loads its overlay by file id (mode number = id, loader 0x8002A13C, ids below).
| Mode | Overlay | What | Sub-states |
|---|---|---|---|
| 0 | INIT.BIN (0x8014B000) | Startup | then 1 (demo), 4 (continue) or 2 |
| 1 | ATDM_OV | Demo setup | then 4 |
| 2 | SELECT.BIN | Mode, level and country select, map battle setup | table 0x800A2F34 |
| 3 | MAP_DEMO.BIN (0x80188000) | World map and story pages | 1 map, 3 pages, 4 leaves; start at sub 3 skips pages |
| 4 | GAME_OV.BIN | A mission | sub 1-7 setup, 7 title card, **8 the map game**, 9-11 end of battle (BEND_OV, id 0x18) |
| 5 | ENDING.BIN (overlay no. 0x24) | Ending | 2 text and credits. All countries open with similar scenes; the country's hero is on screen about 36 presses in (`ending_*`), the staff roll about 58 (`credits`) |
| 6 | - | Back to the boot EXE (0x8002522C, demo end) | |

## Scenario state in `G`
| Offset | What |
|---|---|
| +1 | 0 scenario, non-zero map battle |
| +6 | Map id of the current mission (from the mission table). After a won battle: 9 sends scenario play to mode 5 |
| +0x150 | Players on the map |
| +0x151 | Current player |
| +0x154.. | Country per player. +0x154 is the player's country in scenario play, and MAP_DEMO's row: 0 PEN, 1 BUT, 2 TAK, 3 LOV, 4 AIT, 5 MOA, 6 PAN, 7 BAU |
| +0x170.. | Saved copy of +0x154.. |
| +0x18 (16-bit) | Map sub-state: table 0x800A2FC8, see below |
| +0x1C, +0x20 (16-bit) | Inner steps of the current map sub-state |
| +0x798 | Battle result, non-zero ends the mission (0x80022460): 1 + winner's player index; rewritten to 3 (won) or 5 (lost) before BEND_OV reads it |
| +0x7A4, +0x7A8 | Attacker, target unit |
| +0xD02 | Chapter, MAP_DEMO's column: 0-6 |
| +0x968.. | Cursor: x at 0x800E098C, y at 0x800E098E (16-bit, copy at +4) |
| +0x7F7 | NYANTV number: `TV_nnn` shown in the map's top-right window. 0 none. Seen on its own in `win`/`lose` runs, and forced by the `nyantv` scene, which also sets 0x800E096F, +0x852 and 0x800E0973 |

## Map sub-states
`G+0x18` indexes the handler table 0x800A2FC8. Writing it (the warp's `state=N`, which also clears +0x1C and +0x20) loads that state's overlay and opens its screen. **Verified** by matching the first word traced at each overlay slot (`tools/debug/trace.lua`) against the files' first words:
| N | Overlay | Slot | Screen |
|---|---|---|---|
| 0, 1, 2 | GAME_OV | | Cursor, move, attack |
| 4 | SKSN | 0x8014B000 | Small command box |
| 5 | HOKYU | 0x8014B000 | Overlay loads; nothing drawn without a real target |
| 6 | GORYU | 0x80155800 | Same |
| 7 | ITCHG | 0x8015C800 | Same |
| 8 | GAME_OV | | バトルアニメ / 反撃行動 box (the unit's 機能 command) |
| 9 | SPLD | 0x80155800 | Special, list with checkboxes |
| 10 | NSHOP | 0x80155800 | **Shop**, the cat's greeting and a menu |
| 12 | HASN | 0x8015C800 | Overlay loads; nothing drawn without a real target |
| 14 | LOCEX | 0x8014B000 | Roster with portraits |
| 15 | PROD | 0x8014B000 | Production list |
| 16 | BUTAI | 0x8015C800 | Force list |
| 17 | CNTRY_ST | 0x8014B000 | Country stats table |
| 18 | MEMCARD | 0x8014B000 | Memory card |
| 19 | ALLMP | 0x8014B000 | Whole map |
| 20 | GAME_OV | | 大きめ / 小さめ zoom box |
| 21 | OPT | 0x8014B000 | Options |
| 28 | SUIM | 0x8014B000 | Dive or surface menu (**guess** from the name) |
| 0x19 | GAME_OV | | End of turn: the enemy plays |
| 0x1B | GAME_OV | | Opening "explain?" prompt |

Reached differently:
- **Unit commands:** circle on a unit gives 移動, 作戦, 機能, スペシャル, 情報 (`unit_cmd`, `unit_tactics`, `unit_func`, `unit_special`).
- **Unit info** is INFO_OV (overlay word 0x1E): triangle on a unit.
- **Select-screen help** is square on the level select (`mb_help`, `SEL_HELP.BIN`).
- **Win and lose banners** are `BTLEND/WIN*`, `LOS*`, shown by BEND_OV.

- **Reinforcement speeches** are HELP_OV (id 0x22): 0x80024298 loads it on the map's opening when `G+1` is 0 and `G+6` is 9, the last chapter of a scenario. Allies arrive with portraits and a line each (`help_*`).
- **Sortie shouts** are LOCS_OV (id 0xA): LOCEX steps to `G+0x1C` = 0x10 when a deployment ends, picks a commander with 0x80059FF8, and loads LOCS: portrait, name, one random line (`locs_*`). A real deploy needs owned weapons, so the scenes poke the pick (`jal` at 0x8014C664 to `li v0,1`) and step 0x10.

**Not reached by any scene:** the `*HELP.BIN` files, and the screens of HOKYU, GORYU, ITCHG, HASN, the `SP*`/`SP_*` special effects, JIRAI, HISS. HOKYU, ITCHG, HASN, HISS and the `SP_*` files hold no text. GORYU (5 strings), JIRAI (2) and SPABL (3) use the standard window, whose width is `menu_tables.py`'s formula: state pokes showed the range overlay but no prompt, since they need a real transport, a mine or the item.

**Warp proof:** story shots can land on a transition. What proves the chapter is the TXT file's LBA in each scene's log, read from MAP_DEMO's table. 55 scenes read 53 files, the only sharing being TXT_AIT4.

**No game-over screen exists in scenario play.** BEND_OV 0x8014BA00: result 2 or 5 restarts the same mission with mode unchanged (the `lose` scene shows the banner, then the mission card). `ゲームオーバー` is not in any uncompressed file. The `lose` scene stands in for "game over" in scenes.tsv.

Scenario tables in MAP_DEMO, 8 x 8 entries of `{ram, size, lba}`: COL 0x8018D85C, SEQ 0x8018DB5C, TXT 0x8018DE5C, unknown 0x8018D55C. **TXT_AIT4 is shared:** TAK chapter 3 and PAN chapter 4 point at it, so one translation serves three stories. TAK has no chapter 6.

## Units
Linked list from 0x80133304, stride 0x4C: +0 prev, +4 next, +8 commander, +0xC type record in the table at 0x8009EC14, +0x14 x, +0x15 y. Commander blocks at 0x800F9620, 0x400 per player, stride 0x20, +0x18 is that commander's unit. A player's forces can start empty; the first enemy turn fills the list.

Poking x, y moves the sprite, but **attack refuses a poked target** (weapon window stays, circle does nothing); the target check was not read. Battle is reached through the attract demo instead:
- `battle`: the demo's own battle, drawn on the map (the demo skips the animation).
- `battle_anim`: the full animation with pilot portraits and speech boxes. `G+0x1C` is the step in table 0x800A3070 while `G+0x18` is 2; forcing step 1 (0x8004D700, which loads the `BATTLE*` backdrop by `G+0x830`) as the attack starts plays it for the demo's real attacker and target.

## Overlay slots
Loader records hold 0 for the address, so the slot comes from the caller. **Verified** by counting which slot makes an overlay's `lui`+low pairs land on its own strings (`extract.best_base`), every overlay with text scoring on one slot only, or nearly so (SELECT 16 vs 1, MEMCARD 92 vs 3): 0x8014B000 SELECT, OPT, CNTRY_ST, PROD, MEMCARD, SPABL, SKSN, LOCEX, BEND, INFO, JIRAI, HELP; 0x80155800 SPLD, GORYU, NSHOP; 0x8015C800 LOCS, BUTAI.

## File ids
`tools/disc_ids.py` prints the loader's table (0x8009C34C): 0 INIT, 2 SELECT, 3 MAP_DEMO, 4 GAME_OV, 5 ENDING, 6 OPT, 7 CNTRY_ST, 8 PROD, 9 ALLMP, 0xA LOCS, 0xB SUIM, 0xC HOKYU, 0xD MEMCARD, 0xE SPLD, 0xF SPABL, 0x10 GORYU, 0x11 ITCHG, 0x12 NSHOP, 0x13 SP_WDBZK, 0x14 SP_RNBW, 0x15 SP_FRST, 0x16 SKSN, 0x17 LOCEX, 0x18 BEND, 0x19 SP_ICBM, 0x1A ATDM, 0x1B BUTAI, 0x1C INFO, 0x1D SPAUR, 0x1E SPELK, 0x1F JIRAI, 0x20 HISS, 0x21 HASN, 0x22 HELP. The word at the start of an overlay is **not** this id (ENDING's is 0x24). Records are `{ram, size, lba}`; `disc.md`'s `{size, lba, ram}` reading of the 201 PAW.EXE records was off by one word, which is why it reported odd RAM values such as 0x80186000 as sizes.
