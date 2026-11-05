# Translation notes for phases 7 and 8

Settle each one against a shot, then delete it.

## Abbreviations still on screen (D4: engine work first; for the owner)
Engine work done first: VWF, moved strings, far strings for table fields (`font.md`), digits at half width, labels past digits by tab (`boxes.md`). Each one left has a measured reason.
- Ranks in 50 px (commander panel): Gen. Sec., Gr. Emp., Def. Sec., Lt. Gen., Maj. Gen., Lt. Col.
- Unit classes in the unit list's 61 px Type column: Fighter-Atk., Tr. Bomber, Inf. Tank, Mech Inf., SP AA Gun, SP Gun, SP Rocket, AA Missile; `Secret` for Secret Weapon, `Cat Weapon` for Cat Super Weapon, `Supply` for Supply Truck.
- `CNTRY_ST:5ac` Refin.: 42 px against a column that shows 38 between two frames. `CNTRY_ST:5b4` Plant for 工場 (Factory touched both frames). `CNTRY_ST:9b4` Fed. States: 66 px column. `BUTAI_OV:2a40` CO for 名前: 25 px cell, Name's e went under the frame.
- Commander panel `PAW:a9054` family: Air, Land, Sea (for Air/Land/Sea Cmd), Inst, Acc. The code ends the string after its digits, so only 4 letters fit (`boxes.md`). Unit info has room and uses the full labels. `PAW:b3170` Def.: weapon info, a 30 px cell between two frames. `PAW:9d0,9d4` Df, At: 12 px before a number. `BUTAI_OV:27b0` Interc: 43 px column.
- `PROD_OV:2a5c-2a8c` and the 13 one-kanji headers (`glossary.md`): Bd, Rv, Rd, Br, Ic, Sn, Se, Cs, Rk, Sa, Dt, Fr, Gr: one column each.
- `PAW:b3188` DX (the unit class).
- Story map place names (`DEMO/WMAP0`; the game shows the Japanese field's width, the map cuts the rest; the game's font, since outline fonts closed every e at this size): Prince Realm, Pentaro, Lovely States, Koitsu & Aitsu Fed. Rep., Feb. 7 Isle, Nya Land, Akashiya Republic, Michael Emp., Moai Emirate, Nyanjiro's Land, Chinkoko-Kaan Realm, Fin-Fin Range Realm, Great Pen-Kuro Isle. Turn banner (`FLAG`): Akashiya Land Republic, Panda Beasts' Republic. Save row (`MCWGRPH`, 78 px in the game's font): Pentaro Realm. Map HUD, same reason: Bow-Wow in 70 px, Lovely States, Akashiya Republic, Panda Republic, Moai Emirate.
- `BEND_OV:1cc8` Koitsu&Aitsu heirloom: 24 bytes, the spaced form needs 25.
- Save file title (`limits.SAVE_TITLE`), 6 + 4 fullwidth cells by strncpy: `MEMCARD:ac` Ｐ．Ｗａｒｓ; nations Ｂｏｗ． Ｐａｎ． Ｋｏｉ． Ｌｏｖ． Ａｋａ． Ｍｉｃ． Ｐｅｎ．; `bc,ec` Ｃｈ.
- Not seen on any toured screen, so kept short until phase 8 can measure them: `PAW:b339c,b33a4` Inst, Accur.; `b32ec,b3358` Form; `BUTAI_OV:2618-2638,2684-26a4` Inst, Acc, Sea, Air; `BUTAI_OV:2c7c-2cb8` Screw, Rainbow, Engine, Bazooka; `OPT_OV:1584-15b8` (Res.); `BEND_OV:1d10,1d24`.

## Sector limits
None bind any more: `ENDING/*_TXT` may grow past their one sector, `build.spill` moves a file to a disc gap and rewrites its loader records (proven in game on LOV_TXT with incompressible pages: `tools/debug/spill_proof.sh`). The wordings picked by compressed size in phase 6 (`LOV_TXT:1194,1482,15ae`) are rewritten.

## Order or context guessed from offsets, not seen
- `PAW:a723c,a7230,a7220`, `SPABL_OV:24,10,4`: assumed drawn in reverse address order.
- `PAW:b2f94,b2f98,b3388` (は = `: `), `a74a4,a74f4,a97f4` (` now`): assumed "A: B now!!". `a978c` ` hit final form`, `a98d4` Units, `8b0` `, can't pick up`, `8d0` ` found it!`: settle when the caller of the word table at `0x800A2D2C` is read or the message is seen (`8e8` has を, so it reads ` found!!`).
- Chatter endings `PAW:91be0-91cd0`: short tags drawn after a phrase.
- `GORYU_OV:10,24`, `JIRAI_OV:4,14`, `LOCEX_OV:35e0,35f4,3628,3638,35a0,361c`, `NSHOP_OV:84,a4`: line order and glue.
- `BUTAI_OV:24ac`, `CNTRY_ST:9e4,9fc`: `{x:N}` moved from the Japanese column.
- `PAW:a7170,a71c0,a964c,a9658`, `LOCEX_OV:361c`, `GORYU_OV:4`: digit cells proven by `tools/debug/pokes.py`, wording not seen on screen (`3 in stack`, `3 aboard OK`, `3 aboard`, `Left:3`, ` 3 units`).
- `OPT_OV:1384,1394`: 次部隊（後）/（前） as Unit Back/Forward; direction may be reversed. `OPT_OV:1584-15b8`: （予） read as reserved.
- `SEL_HELP`: あり/なし as On/Off must match the option labels on screen.
- `LOCS_OV` speakers inferred from their tics; the second `chu` block (`1578-1760`) has no known nation.
- `HELP_OV:1a4`, `LOCS_OV:c78,c98`: 15 Greek letters overflow 168 px, a space in the middle wraps them evenly.
- `reinforce`: the HELP_OV speech stays open under the Auto-deploy prompt; the Japanese does the same (`work/qa/x/rj`).
- `DEMO/KABE4:10d82`: no indent, the title fills 24 bytes.
