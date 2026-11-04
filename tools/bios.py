"""Unit bios: author one paragraph per unit, flow it over the bio's fields (P_* lines are fixed fields, docs/re/boxes.md).

  bios.py show [FROM TO]   each unit's Japanese, joined per paragraph
  bios.py flow             script/units/bios.tsv (P_00<TAB>description<TAB>tip) -> script/units/*.json; tests/test_lint.py fails if they differ
Stat lines are generated from STAT_NOTES, so unknown notes stop the run. A paragraph that needs more fields than the Japanese used is an error.
"""
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import en_text
import limits

SRC = ROOT / "script/units/bios.tsv"
TL = ROOT / "work/tl"
HEADER = "{x:60}Strength, out of 5"
ADVICE = "{x:60}* One-Point Advice *"
# 全角 digits and layout spaces are normalised before lookup.
STAT_NOTES = {
    "地上攻撃力は弱い": "weak vs ground",
    "間接攻撃できない": "no ranged attack",
    "２．５くらいかな": "more like 2.5",
    "３に近い": "close to 3",
    "３．５くらいかな": "more like 3.5",
    "占領できます": "can capture",
    "占領ができます": "can capture",
    "陸への攻撃は激弱": "awful vs ground",
    "空に攻撃できない": "no air attack",
}
DIGITS = str.maketrans("０１２３４５６７８９？", "0123456789?")


def units():
    for path in sorted(glob.glob(str(ROOT / "script/units/P_*.json"))):
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        yield Path(path).stem, [e for e in doc["entries"] if e["kind"] == "text"]


def parts(entries):
    """(header, attack, defense, description lines, advice header, tip lines); the last four may be empty or None."""
    head, attack, defense, advice = None, None, None, None
    desc, tip = [], []
    for e in entries:
        jp = e["jp"].replace("　", "")
        if "段階評" in jp:  # one file drops the 価
            head = e
        elif re.match("攻撃力[０-９]", jp):  # other lines start with the same word (P_34, P_37)
            attack = e
        elif re.match("守備力[０-９]", jp):
            defense = e
        elif "★" in jp:
            advice = e
        else:
            (tip if advice else desc).append(e)
    return head, attack, defense, desc, advice, tip


def stat(word, e):
    m = re.fullmatch(r"(?:攻撃力|守備力)\s*(\S+?)(?:（(.*)）)?", e["jp"].replace("　", " ").strip())
    if not m:
        raise ValueError(f"{e['id']}: can't read {e['jp']!r}")
    text = f"{word} {m[1].translate(DIGITS)}"
    return f"{text} ({STAT_NOTES[m[2]]})" if m[2] else text


def flow(paragraph, entries, unit):
    """Greedy over the fields; returns [(id, line)]."""
    rows, words = [], paragraph.split(" ")
    line_i, line = 0, ""
    for word in words:
        trial = f"{line} {word}" if line else word
        if line_i < len(entries) and fits(entries[line_i], trial):
            line = trial
            continue
        if line_i >= len(entries):
            raise ValueError(f"{unit}: paragraph needs more than {len(entries)} fields: {paragraph!r}")
        rows.append((entries[line_i]["id"], line))
        line_i += 1
        line = word
    if line:
        if line_i >= len(entries) or not fits(entries[line_i], line):
            raise ValueError(f"{unit}: paragraph needs more than {len(entries)} fields, at {line!r}")
        rows.append((entries[line_i]["id"], line))
        line_i += 1
    # Fields the English doesn't reach still replace the Japanese.
    rows += [(e["id"], " ") for e in entries[line_i:]]
    return rows


def fits(entry, text):
    lim = limits.limit(entry)
    return en_text.line_width(text) <= lim.px[0] and (lim.bytes is None or len(en_text.encode(text)) <= lim.bytes)


def show(lo, hi):
    all_units = list(units())
    for name, entries in all_units[lo:hi]:
        _, a, d, desc, adv, tip = parts(entries)
        j = lambda es: "".join(e["jp"].replace("　", "") for e in es)
        print(f"{name}\t{a and j([a])}\t{d and j([d])}\t{len(desc)}f {j(desc)}\t{len(tip)}f {j(tip)}")


def flow_all():
    rows = {}
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if line.strip():
            name, desc, *tip = line.split("\t")
            rows[name] = (desc, tip[0] if tip else "")
    out, bad = {}, []
    for name, entries in units():
        if name not in rows:
            bad.append(f"{name}: not in {SRC.name}")
            continue
        desc_text, tip_text = rows.pop(name)
        head, attack, defense, desc, adv, tip = parts(entries)
        try:
            pairs = []
            if head:
                pairs.append((head["id"], HEADER))
            if attack:
                pairs.append((attack["id"], stat("Attack", attack)))
            if defense:
                pairs.append((defense["id"], stat("Defense", defense)))
            pairs += flow(desc_text, desc, name)
            if adv:
                pairs.append((adv["id"], ADVICE))
                pairs += flow(tip_text, tip, name)
            elif tip_text:
                raise ValueError(f"{name}: tip given, the Japanese has no advice header")
            out.update(pairs)
        except (ValueError, KeyError) as exc:
            bad.append(f"{name}: {exc}")
    bad += [f"{name}: no such unit" for name in rows]
    if bad:
        print("\n".join(bad))
        sys.exit(1)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "show":
        show(*(int(x) for x in sys.argv[2:4])) if len(sys.argv) > 2 else show(0, None)
    else:
        import batches
        print(f"{batches.write_en(flow_all())} lines changed in script/")
