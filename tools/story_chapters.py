"""Story pass input: work/qa/story/chapters/<NATION>.txt, one nation's campaign in story order, `>> id | speaker | JP` then EN.

One file per campaign, not per TXT file: a chapter is 10-28 lines, and the point of the pass is continuity across them.
Chapter lists are MAP_DEMO's table (docs/re/flow.md): TAK has no chapter 6, and TAK 3 and PAN 4 play TXT_AIT4.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches

NATIONS = {
    "PEN": ["PEN0", "PEN1", "PEN2", "PEN3", "PEN4", "PEN5", "PEN6"],
    "BUT": ["BUT0", "BUT1", "BUT2", "BUT3", "BUT4", "BUT5", "BUT6"],
    "TAK": ["TAK0", "TAK1", "TAK2", "AIT4", "TAK4", "TAK5"],
    "LOV": ["LOV0", "LOV1", "LOV2", "LOV3", "LOV4", "LOV5", "LOV6"],
    "AIT": ["AIT0", "AIT1", "AIT2", "AIT3", "AIT4", "AIT5", "AIT6"],
    "MOA": ["MOA0", "MOA1", "MOA2", "MOA3", "MOA4", "MOA5", "MOA6"],
    "PAN": ["PAN0", "PAN1", "PAN2", "PAN3", "AIT4", "PAN5", "PAN6"],
    "BAU": ["BAU0", "BAU1", "BAU2", "BAU3", "BAU4", "BAU5", "BAU6"],
}
ENDING = {"AIT": "KOI"}  # the ending files name Koitsu & Aitsu by Koitsu


def speaker(jp):
    m = re.match(r"([^：　]{1,12})：", jp)
    return m[1] if m else "-"


def lines(index, file):
    for eid, (_, e) in index.items():
        if eid.rsplit(":", 1)[0] == file and e.get("kind", "text") == "text":
            yield f">> {eid} | {speaker(e['jp'])} | {e['jp']}\n{e['en']}\n"


def main():
    out = ROOT / "work/qa/story/chapters"
    out.mkdir(parents=True, exist_ok=True)
    index = batches.entries()
    for nation, chapters in NATIONS.items():
        text = []
        for n, ch in enumerate(chapters):
            text.append(f"\n## Chapter {n}: DEMO/TXT_{ch}\n")
            text.extend(lines(index, f"DEMO/TXT_{ch}"))
        text.append(f"\n## Ending: ENDING/{ENDING.get(nation, nation)}_TXT\n")
        text.extend(lines(index, f"ENDING/{ENDING.get(nation, nation)}_TXT"))
        assert sum(t.startswith(">>") for t in text) > 50, nation  # a wrong id scheme would otherwise give empty files
        (out / f"{nation}.txt").write_text("".join(text), encoding="utf-8")
        print(nation, sum(t.startswith(">>") for t in text))


main()
