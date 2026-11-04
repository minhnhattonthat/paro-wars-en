# Paro Wars (PS1, SLPM-86016) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Hook:     `git config core.hooksPath tools/hooks` (once per clone)
- Build:    `python -X utf8 tools/build.py`        -> build/paro_wars_en.cue/.bin (checks the dump against `rom.sha1` first; patches files in place with `tools/disc.py`, mkpsxiso can't rebuild this disc: `docs/re/disc.md`)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/paro_wars_en.cue --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py build/paro_wars_en.cue --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 60000` -> `work/qa/warp/<name>.png` (scenes: `tools/debug/scenes.tsv`, from a cold boot, so each takes about 1-6 minutes; never ask the user to play to a scene). All scenes: `python -X utf8 tools/debug/warp_all.py [--only REGEX] [--jobs 8]`. One-off RE runs with the state trace: `sh tools/debug/x.sh NAME SCENE "STEPS" [FRAMES]`. State variables: `docs/re/flow.md`
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish without the user; written in phase 9)
- Unpack:   `tools/mkpsxiso/mkpsxiso-2.30-win64/dumpsxiso.exe -x work/disc/tree -s work/disc/layout.xml "rom/Paro Wars (Japan).cue"`, then `python -X utf8 tools/unpack_all.py work/disc/tree work/unpacked work/recon/lz.tsv` (needed by the RE tools; both outputs are gitignored)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/Paro Wars (Japan).bin/.cue` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own copy in `tools/pcsx/` (PCSX-Redux nightly 30282.20261104.5, `python -X utf8 $SKILL/scripts/fetch_emu.py pcsx`; gitignored), BIOS `tools/bios/scph5500.bin` (`fetch_emu.py psx-bios`). Disc tools: `tools/mkpsxiso/` (v2.30, github.com/Lameguy64/mkpsxiso), `tools/armips/` (v0.11.0, github.com/Kingcom/armips). Savestates: `work/states/`.
- Text: `script/` (JSON, written in phase 4). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Never name a helper after a stdlib module: `tools/` is `sys.path[0]` for every script here, so a `tools/re.py` broke Python start-up (hence `tools/mipsre.py`).
- PS1 input: the title menu ignores presses until its animation ends; confirm is circle, back is cross. Script routes must wait for the cursor.
- Disc files are sector-padded with leftover dev-machine bytes (a DOS filer's Japanese strings): Shift-JIS hits past an LZ file's length field are not game text (`docs/re/text.md`).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
