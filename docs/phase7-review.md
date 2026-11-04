# Phase 7 independent review, 2026-11-05

`codex exec` was out of quota until Nov 11, so both passes were fresh read-only `reviewer` subagents with no view of the work. Neither edited anything.

## Code and script (over 6fc3a27): done-when met
Phase 6 review items 1-9: all fixed or with a recorded reason, read from `en` in `script/`. No Critical. Three Important, handled here:

| Finding | Outcome |
|---|---|
| Digit slots not in `TEMPLATES` (suspected: MEMCARD, `PAW:a7170,a71c0,a964c,a9658`, `LOCEX_OV:361c`, `PROD_OV:28d0,28ec`) | Real, except the `PROD_OV` two, which draw fine on the shots. `tools/debug/pokes.py` now checks every call to the digit writer statically and found `GORYU_OV:4` too. All fixed, in `TEMPLATES`, and tested. The digits in those screens are not seen in game. |
| MEMCARD | Worse than reported: these strings are the save file's title on the card, for the console's card manager. Rewritten in fullwidth, read back from a saved `.mcd`. New lint rule `SAVE_TITLE`. |
| Lint bite tests partial, typos in control codes passed | Malformed codes now always caught; bite cases added for count, centred, width, slot and templates. |
| `{x:N}` never compared with the Japanese gap | Not done: N is a judgement per screen; the sheets check it. |
| `verify_build.py` holes | Fixed: spilled files read at their gap (proved on `paro_wars_spill.bin`, `1 spilled`), bytes before an LZ stream, PAW font span split into drawn cells and pool, `stray()` tested. Left: bytes after an LZ stream (leftover padding, compression length varies); a text slot's bytes aren't compared with its `en`; every ref of every entry is allowed. |

Minors: glossary 36 px fixed. 4,686 against 4,683 entries is three `num` entries turned `text` (`OPT_OV:13d0,13e8`, `PAW:a8ac8`); the older counts in `status.md` stand for their phases.

## Visual (final build, `work/p7/h/`, 25 sheets, 50 scenes against the original): ok
An earlier pass read sheets older than the last build and reported Item, BGM and Counter rows; fresh sheets showed those fixed, so it was rerun on a new tour. No Critical or Important. Its Minors are in `docs/polish.md`. The `battle_anim` chatter it was unsure of is the game's alien font on both discs (`work/p7/ba.png`).

`work/` isn't in git: `tools/debug/warp_all.py --rom build/paro_wars_en.cue` and `tools/debug/compare.py` regenerate these.
