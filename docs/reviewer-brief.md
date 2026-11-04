# Translation reviewer brief - Paro Wars

You review one part of a JP->English fan translation of a comedy war game. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, encodable characters, width) is already enforced by the check tool: judge translation quality.
Return the report as your final message: subagents cannot write files, so the controller saves it.

## Inputs (paths in your dispatch)
- Pairs file: every translated entry as `>> id | JP` then its English. Lines repeated elsewhere are shown once. `P_*` entries are one unit bio joined into a paragraph; `DEMO/KABE4` and `UNITINFO` are fixed fields, so a sentence spans several ids and the split doesn't matter. `{x:N}` positions a label next to a button icon, `{br}` is a line break. Read ALL of it, in passes if large.
- `glossary.md` (rulings at the top), `docs/style-reference.md`, `docs/synopsis.md`.

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say what it means.
- Consistency: glossary names and terms exactly (a one-letter slip is what players notice).
- Things players caught that reviewers missed: jokes and wordplay losing their punch; abbreviated names or terms beyond what the glossary allows; stock phrases that read awkwardly in English. Unit and commander names are puns on real hardware and people: check that the pun survives.
- Voice: each speaker against their row in the style reference. Speech tics (ニャン, ワン, アル, モ, ブヒ), register and comic intensity must come through in English, not be normalised into neutral prose. A flattened voice is Important, not Minor.
- Reveals: nothing hints at Nyanjiro's true identity before chapter 6.
- Naturalness: would a reader stumble?

## Report
### Issues
#### Critical (meaning reversed, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, a character's voice flattened, joke dead)
#### Minor (style: deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`. Keep suggested English short: the same limit as the current line.
### Assessment
Approved | Needs fixes - one sentence why.
