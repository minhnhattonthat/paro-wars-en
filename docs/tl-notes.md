# Translation notes for phases 7 and 8

From the translators' reports. Nothing here has been seen in game: settle each one against a shot, then delete it.

## Abbreviations forced by cell width (D4: engine work first)
The limits are the Japanese cell widths, which may be conservative. Phase 7: measure the real room on screen and restore full forms where it allows, or widen.
- Ranks `PAW:9176e-91818`: Emper., Fuhrer, Pres., GenSec, PM, Gr.Emp., Def.Sec., Gen., Lt.Gen., Mj.Gen., Lt.Col., Capt.
- Classes `PAW:90b50-90d3a`: Interc., Attack, Fighter-Att., Tr. Bomber, Atk Heli, Air Inf., MainTank, LtTank, Inf. Tank, Mech Inf., Supply, B-ship, Destr., Transp., Sub, Cat Weapon, Secret.
- Terrain and buildings `PAW:91844-91a60`, `CNTRY_ST:5ac-5c0`, `LOCEX_OV:3688-36a0`: Refin., Fact., Pt, Airpt, Frst, Bamb., Mt(, Cst., Bch., Tmpl, Snw.
- Stat labels: `PAW:b30b0,b3110,b339c` Inst; `b30c0,b3120` Acc; `b328c-b329c,b33a4` Accur.; `b30d0-b30f0,b3130-b3150` Sea/Land/Air; `b3084,b3170` Def; `b32ec,b3358` Form; `a87b4` Cmd; `a9914` Land Cmd; `BUTAI_OV:2618-2638,2684-26a4` same words; `CNTRY_ST:5f0` Cmd, `5f8` Nat.
- Others: `PAW:89c` Move, `9d0-9d8` Df/At/Hgt, `90da0` MG, `90e2c` Guided, `b3168` Cash, `b3178` Arms, `b32dc,b3360` Name, `a92f4,a9424` Weapons/Weapon; `SELECT:24` Nation; `BUTAI_OV:23e8` Lovely Fed. States, `2418` Moai Emirate, `2430` Panda Tea Party, `27b0` Interc, `27c8` Captr, `2a40` Nm., `2c7c-2cb8` Screw/Rainbow/Engine/Bazooka; `BEND_OV:1d10,1d24`; `CNTRY_ST:978-9b4`; `MEMCARD:ec` Ch.; `NSHOP_OV:2d8-300` Cat Doza-emon, Cat Ship; `OPT_OV:1364,1374` Rotate Right/Left, `1584-15b8` (Res.); `ITEM:420` Foes.

## Order or context guessed from offsets, not seen
- `PAW:a723c,a7230,a7220`, `SPABL_OV:24,10,4`: assumed drawn in reverse address order.
- `PAW:b2f94,b2f98,b3388` (は = `: `), `a74a4,a74f4,a97f4` (` now`): assumed "A: B now!!". `a978c` ` hit final form`, `a98d4` Units, `8b0` `, can't pick up`, `8d0,8e8` ` found it!!` (を may mean ` found!!`).
- Chatter endings `PAW:91be0-91cd0`: short tags drawn after a phrase.
- `GORYU_OV:10,24`, `JIRAI_OV:4,14`, `LOCEX_OV:35e0,35f4,3628,3638,35a0,361c`, `NSHOP_OV:84,a4`: line order and glue.
- `BUTAI_OV:24ac`, `CNTRY_ST:9e4,9fc`, `MEMCARD:ec`: `{x:N}` moved from the Japanese column.
- `PAW:a9054` family: Instinct, Accuracy, Land Cmd may overlap a number drawn after the Japanese two columns. `PAW:a9530-a9570,a9658`: number follows `Left`.
- `OPT_OV:1384,1394`: 次部隊（後）/（前） as Unit Back/Forward; direction may be reversed. `OPT_OV:1584-15b8`: （予） read as reserved.
- `SEL_HELP`: あり/なし as On/Off must match the option labels on screen.
- `LOCS_OV` speakers inferred from their tics; the second `chu` block (`1578-1760`) has no known nation.
- `HELP_OV:1a4`, `LOCS_OV:c78,c98`: 15 Greek letters overflow 168 px, a space was added so the tool wraps.
- `DEMO/KABE4:10d82`: no indent, the title fills 24 bytes.
