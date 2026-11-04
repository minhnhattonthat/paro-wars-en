# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike and marker build not started. Phases 0 to 4 done on 2026-11-05. The build is still the unedited disc.
- **Done:**
  - Phase 4: `tools/extract.py` wrote 197 files in `script/`, 5,482 entries, of which 4,683 are kind `text` (about 94,000 chars). `tests/test_script.py` (6 s, in the pre-commit check) proves every entry re-encodes to the disc's bytes and no kana run on the disc is outside an entry unless `tools/notext.tsv` names it; altering a `jp` and deleting an entry each made it fail. `--force` was checked to keep `en`. Formats, kinds and corrections: `docs/re/text.md`. Overlay load slots: `docs/re/flow.md`.
  - Step 0: dump pinned, emulator and BIOS in `tools/`, pre-commit hook proven to reject a failing test, guard hook proven with the canary, smoke boots the original with `tools/routes/boot.txt`.
  - Phase 1: `docs/re/` holds disc layout, LZ codec, text formats, font and graphics survey. No earlier patch found.
  - Phase 2: `tools/debug/warp.lua` + `scenes.tsv` reach 159 scenes from a cold boot on the original disc, each with a shot, 159/159 on the final run (`work/qa/warp/`, sheets viewed): all 55 story chapters, their mission cards, map, unit commands and info, pause menu, shop, NYANTV, memory card, battle on the map and animated, win, lose, 8 endings, credits, map battle. All 65 sweep sheets read. Loader guesses promoted in `docs/re/disc.md`. State variables and overlays per screen: `docs/re/flow.md`.
  - Phase 3: `tests/test_disc.py` rebuilds the disc from `work/disc/tree` into a blank image and matches `rom.sha1` (11 s, in the pre-commit check; broken EDC, P and Q tables each make it fail). `tools/build.py` writes `build/paro_wars_en.cue/.bin`, smoke passes. It doesn't use mkpsxiso, which can't reproduce this disc (`docs/re/disc.md`); `tools/disc.py` patches files in place at their LBAs. `dumpsxiso` is still the unpacker.
- **Next:**
  1. Phase 5: engine spike (font decision, `docs/re/font.md`) and marker build: every line replaced by its id, each box's width measured in-game. New files go into the disc through `disc.write_files`, which refuses a file larger than its sectors. Compressed families (`units`, `ending`, KABE4) must still fit their sectors after `lzkc.compress`.
  2. Phase 5 must also settle, from `docs/re/text.md`: Greek glyphs for Koitsu's gibberish, the built-up messages and sentence endings in PAW.EXE (read the callers), fixed-stride name tables. Only `lui`+low and word references are in `refs`, so check for strings copied by `lw`/`lh` when the marker tour shows Japanese.
- **Route facts:** `work/` is not in git. Scene routes are in `scenes.tsv`; regenerate the shots with `python -X utf8 tools/debug/warp_all.py --jobs 8` (about 40 minutes), and savestates with `--state-dir work/states` (22 MB each; one tested, saved and resumed; the library is not generated yet, so build it from the first patched disc).
- **Limits of the warp, for later phases:**
  - **Game over:** scenario play has none. A lost mission restarts after the banner (`BEND_OV`), so `lose` stands in. The search for `ゲームオーバー` covered uncompressed files only.
  - **`battle_anim` is forced:** step 1 of the attack state, poked inside the demo. The red portrait may come from that. No warp reaches a battle the player starts, because attack refuses a poked target.
  - **Story shots:** some land on a transition; each chapter is proven by the TXT file's LBA in its log.
  - **Not reached:** HELP_OV and `*HELP.BIN`, and the screens of HOKYU, GORYU, ITCHG, HASN, the special effects, JIRAI, HISS and LOCS. Not on the phase 2 list, but they hold text: phase 5's marker tour has to cover them (`flow.md`).
  - **Unit name plates** (`OP_*`, `PUP_*`, graphics row 11, the largest item) have not been seen on screen, so their display route is unknown.
- **Not checked:** the emulator GUI's keyboard input (Step 0 asks for it; all input so far is scripted and headless, so it needs a person or a window automation run before the owner plays in `tools/pcsx/`).
- **Open bugs:** none.
- **Waiting on the user:** nothing blocking. Non-blocking: phase 5 proposes two-letters-per-code at 6 px (`docs/re/font.md`) because a story page holds only 150 bytes; a nicer VWF would cost engine work across at least two routines plus overlays.
