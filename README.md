# Paro Wars English translation

Unofficial English fan translation of **Paro Wars** (パロウォーズ, PlayStation, Konami, 1997, SLPM-86016): the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its `PATCHING.txt`. This repository holds no game data you can play; you need your own dump of the Japanese disc.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate helps most.

## Translation status

| Part | Status |
|---|---|
| Story, all 8 campaigns and endings | Translated |
| Menus, unit bios, shouts, system messages | Translated |
| Graphics with text: signs, title cards, banners, nation plates, map labels | Translated |
| Staff roll | Translated |
| Title logo パロウォーズ | Left in Japanese: no English logo exists, and the art already reads PARO WARS |
| Voices, songs | Left in Japanese |

Known issues:
- A few short prompts were checked for width but never seen in play, because no route reaches them without real game state: transport selection and the landmine message.
- See [Issues](../../issues) for anything newer.

Tested in PCSX-Redux with a Japanese BIOS (SCPH-5500), from a cold boot and by scripted input.

## Base disc

`Paro Wars (Japan).bin`, one track, 702,250,752 bytes:
- CRC32 `F02A3323`
- MD5 `3da69136f93ddb712ec4da138a35bc82`
- SHA-1 `8dc1ad0e6ab8d7f469efcdea8c94b849a3fdc18d`

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tools/gfx_labels.py`, `tools/credits.py` | The redrawn graphics text and the staff roll. |
| `asm/` | The variable-width font hook. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched disc

Needs Python 3.12+ with numpy and Pillow (pytest for the check) and your own dump of the Japanese disc.

```sh
git clone https://github.com/minhnhattonthat/paro-wars-en
cd paro-wars-en
# copy your dump to: rom/Paro Wars (Japan).bin and .cue
#   (702250752 bytes, SHA-1 above; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py    # -> build/paro_wars_en.cue/.bin
python -X utf8 tools/check.py    # tests + text lint
```

## Credits

Translated with AI assistance (Claude), directed by minhnhattonthat. Fonts: `docs/fonts.md`.

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Konami's and is included only so the translation can be checked against it. Paro Wars is (c) Konami; this project is not affiliated with them. No pre-patched images are distributed.
