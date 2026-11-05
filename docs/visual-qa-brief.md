# Visual-QA reviewer brief - Paro Wars

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original ROM's sheets (`work/qa/tour_jp/`, same ids) and `glossary.md`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok` (the controller adds the game's own below):
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet.
- Koitsu's lines are Greek letters and symbols (`glossary.md`), in English as in Japanese.
- Abbreviations and name forms listed in `docs/tl-notes.md`: each has a measured reason.
- `Land50`, `Land23`: the code writes the number straight after the label, as it does in the Japanese.
- A short or one-word line in the middle of a nation plate's paragraph, where the Japanese row is short too: those rows are fixed fields.
- Options mixing `ON` and `Off`: so does the Japanese (ＯＮ and なし).
- A story map or banner frame half black, or the right part of the map black: the original's own.
- The title logo パロウォーズ stays Japanese by ruling D5; the art under it reads PARO WARS.
- Battle units carry no name plate; the "number + name" labels in `OP_*`/`PUP_*` never reach the screen.
- Screens past a story's last page (mission card, map) in a `full_*` sheet: the route's extra presses.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
