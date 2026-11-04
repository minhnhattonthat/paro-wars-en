# Translator brief - Paro Wars (PlayStation, 1997)

You translate part of the Japanese text of Paro Wars into English for a fan patch. It is Konami's turn-based war game with a Parodius cast: a comedy parody of the Cold War, full of puns on real weapons and people. Penguins, cats, pigs, octopuses, pandas and moai go to war over nothing.
Work only on the batches named in your dispatch, one at a time in the order given, each to a passing check before the next. Do all translation yourself; do not dispatch subagents. Never edit `tools/`, `glossary.md` or `script/`.

## Read first
1. `docs/style-reference.md` - character voices and approved pairs. Match this voice.
2. `glossary.md` - binding names and terms, and the rulings at the top.
3. `docs/synopsis.md` - plot and late reveals.
4. `script/units/bios.tsv` when you touch unit or weapon names: English already approved for the unit bios.

## Input: `work/tl/<batch>.tsv`
`id<TAB>form<TAB>limit<TAB>Japanese`. Limit: `1x72px/14b` = 1 line of 72 px in a slot of 14 bytes (1 byte a letter, plus padding); `2x168pxwrap` = the tool wraps to 2 lines of 168 px, so write no breaks. No `/Nb` = the string can move, only the pixels count. Average letter 5.3 px, M/W 8, i 2.
Forms:
- `shout`: a battle speech box, one short burst by the character the id names (`X_NYAN` Nyanjiro, `X_TAKO` Takosuke, `X_PENTA` Pentaro, `X_BUTA` Michael, `X_MOAI` Empress Yoshiko, `X_PANDA` Anna Pavlova, `X_BAU` Pochi-no-Arashi, `X_HIKARU`, `X_AKANE`, `X_HANAKO` Pen-Hanako, `X_BERIAL` Belial Boo-Boo, see the style reference). The file's lines run in groups: taunts, attacks, being hit, defeat. Keep the speech tic in most lines, but not as a mechanical tail on every one.
- `data`: fixed fields. `DEMO/KABE4` and `UNITINFO` are 144 px and 24 bytes a field; a sentence runs over several fields, so **write the paragraph, then break it across the fields in order**, keeping every field under the limit. A field the English doesn't reach is a single space (`id<TAB> `). Labels stay labels (`国王：` King:). `SEL_HELP` flows the same way at 288 px.
- `menu`: labels, messages and table cells. Short, plain, game-UI English.

## Workflow
1. `python -X utf8 tools/batches.py fill <batch>` lists the lines left to write. Lines it filled are identical Japanese already translated; read them in `work/tl/<batch>.out.tsv`.
2. Write the lines you translate to `work/tl/<batch>.part.tsv`, with your file-write tool, not a shell heredoc: `id<TAB>English`. A line in `.part` wins over a fill, so override any fill that is wrong for this character.
3. Run `fill` again, then `python -X utf8 tools/batches.py check <batch>`, and fix until it prints OK. `python -X utf8 tools/batches.py fit "text" ID` measures one line.
Plain ASCII: straight quotes, `...`. No tabs inside the English, no Japanese or fullwidth characters. Only your own batches' `.part` and `.out` files get written.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't state; don't summarise. Adapt wordplay so the joke still lands; no translator notes. Unit and weapon names are puns on real hardware: keep the real name's shape and the pun (`Ｆ－１５ラッキーイーグル` F-15 Lucky Eagle, `Ｔバック－５５` T-Back-55).
- Keep the speaker audible. JP register markers carry voice and must turn into English devices, not vanish. A line any speaker could have said is a mistake.
- Names and terms exactly as in the glossary. Honorifics kept and hyphenated (`-san`), given name first. Abbreviate only when no full form fits the pixels, and report it as `ABBREV: id`. Punctuation: 「」 -> "...", 『』 -> '...', ・・・ -> ..., ！？ -> !?, ！！ -> !!. ～ stretches the word.
- Strings starting with `　`: a button icon is drawn over the gap. Keep the gap with `{x:N}` where N = leading `　` x 12 (`　で決定` -> `{x:12}Confirm`), and do the same inside a line when an icon or number sits at a fixed place: `{x:N}` N = columns before it x 12. `○：次ページ　　　　×：戻る` has its own glyphs; write `O: Next page{x:120}X: Back`: `{x:N}` puts the second label at its Japanese column; use `O` and `X` for ○ and ×. A `　` run with a number drawn into it (`機　数　　　？／　　　`) is a template: keep labels at their columns with `{x:N}` and leave the numeric columns free.
- Number-only and mark-only strings are not in your batches. Keep Greek verbatim: Koitsu speaks it.
- Fragments glued to a name at run time (`は`, `を見つけた！！`, `になった！！`, `は変身した`): write what reads right after a unit name, with its leading space (` found it!!`, ` transformed`). The chatter-ending table `PAW:91be0` on is a separate 24 px window drawn after a phrase: write a short tag that reads after any sentence (`だよ` `!`, `らしい` `I hear`, `でポン` `-pon`). 24 px is about 4 letters, so choose tags that fit.

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently across your batches, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `ABBREV: id - en`, `LONG: id - note`.
