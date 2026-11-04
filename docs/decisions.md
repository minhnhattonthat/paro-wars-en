# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-05 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing answer for one-shot runs. |
| D2 | 2026-11-05 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. Recon found no earlier patch (`docs/re/README.md`), so official Konami spellings, then Hepburn. |
| D3 | 2026-11-05 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-05 | Abbreviations | engine work first (default), abbreviate | Engine work first; skill default, not overridden. |
| D5 | 2026-11-05 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards); leave the Japanese logo only if it has no official English version. Applied here: the パロウォーズ logo stays, since the game shipped only in Japan and no official English logo exists (the art already carries a PARO WARS subtitle). That reading is the worker's, noted for the owner. |
| D6 | 2026-11-05 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through every checkpoint without asking. |
| D7 | 2026-11-05 | Saves or memory cards to start from | owner's, none | None provided; build the debug tool as usual. |
