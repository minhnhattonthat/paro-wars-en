# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool not started. Phases 0 and 1 done on 2026-11-05. No build yet (the first comes in phase 3).
- **Done:**
  - Step 0: dump pinned, emulator and BIOS in `tools/`, pre-commit hook proven to reject a failing test, guard hook proven with the canary, smoke boots the original with `tools/routes/boot.txt`.
  - Phase 1: `docs/re/` holds disc layout, LZ codec, text formats, font and graphics survey. No earlier patch exists.
- **Next:**
  1. Phase 2: `tools/debug/warp.lua` + `tools/debug/scenes.tsv`, reaching every scene from a cold boot with a shot as proof. Scenes needed: each of the 8 countries' story chapters 0-6, mission cards, tactical map, unit command menus, battle, shop, NYANTV, memory card, unit info, win, lose, game over, each ending, credits, map battle mode.
  2. Promote the loader guesses in `docs/re/disc.md` (BK_DT, DEMO and overlay loads) along the way; phase 3 needs them.
  3. Add a row to `docs/re/graphics.md` for anything new on those screens, and read the remaining sweep sheets it lists.
- **Route facts:** `work/` is not in git, so rebuild from `tools/routes/boot.txt`: title menu needs a press after about frame 2900; start, then circle on mode select, 4 x circle on level select (60-frame gaps), then story pages take circle (pages need ~30 frames each with mash). First tactical map arrives about 6,000 frames after page mashing starts.
- **Not checked:** the emulator GUI's keyboard input (Step 0 asks for it; all input so far is scripted and headless, so it needs a person or a window automation run before the owner plays in `tools/pcsx/`).
- **Open bugs:** none (no build yet).
- **Waiting on the user:** nothing blocking. Non-blocking: phase 5 proposes two-letters-per-code at 6 px (`docs/re/font.md`) because a story page holds only 150 bytes; a nicer VWF would cost engine work across at least two routines plus overlays.
