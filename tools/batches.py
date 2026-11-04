"""Translation batches: split the script into work/tl/, check a batch's output, merge it back into script/.

  batches.py split            work/tl/bNNN.tsv (id, form, limit, jp) for every untranslated text entry; refuses to overwrite
  batches.py check [bNNN..]   exit 1 on id mismatch, bad characters, glossary miss or anything limits.check rejects; no args = all with output
  batches.py merge [bNNN..]   check, then write en into script/*.json (status done)
  batches.py fill bNNN..      bNNN.part.tsv (hand-written lines) + identical Japanese already translated -> bNNN.out.tsv; lists what is left
  batches.py patch FILE       id<TAB>English lines into their batches' .part files, then refill those batches
  batches.py fit "text" ID    width of each line in that entry's box
Output: work/tl/bNNN.out.tsv, id<TAB>English, one line per input id, same order.
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

TL = ROOT / "work/tl"
MAX_CHARS = 3500
MAX_ENTRIES = 150
ORDER = ["story", "ending", "units", "battle", "data", "menu"]
FORM = {"story": "narration", "ending": "narration", "units": "bio", "battle": "shout", "data": "data", "menu": "menu"}
GREEK = re.compile("[Α-Ωα-ω]")
RUNS = [re.compile("[ァ-ヺーｦ-ﾟ]+"), re.compile("[ぁ-ゖ]+"), re.compile("[一-鿿]+")]
# Families whose text carries full names: narrow menu labels are exempt from the glossary check.
TERM_GROUPS = {"story", "ending", "battle"}  # a bio's fields split sentences anywhere, so a JP term and its EN may land in different ids


def docs():
    for path in sorted(glob.glob(str(ROOT / "script/*/*.json"))):
        yield Path(path), json.loads(Path(path).read_text(encoding="utf-8"))


def entries():
    """{id: (group, entry)} for every text entry."""
    out = {}
    for _, doc in docs():
        for e in doc["entries"]:
            if e["kind"] == "text":
                out[e["id"]] = (doc["group"], e)
    return out


def limit_label(e):
    lim = limits.limit(e)
    rows = sorted(set(lim.px))
    label = f"{len(lim.px)}x{rows[-1]}px" + ("wrap" if lim.wrap else "")
    return label + (f"/{lim.bytes}b" if lim.bytes is not None else "")


def split():
    if list(TL.glob("b*.tsv")):
        sys.exit(f"{TL} already has batches; delete them first")
    TL.mkdir(parents=True, exist_ok=True)
    n, chars, rows = 0, 0, []

    def flush():
        nonlocal n, chars, rows
        if rows:
            n += 1
            (TL / f"b{n:03}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        chars, rows = 0, []

    all_docs = list(docs())
    for group in ORDER:
        flush()
        for _, doc in all_docs:
            if doc["group"] != group:
                continue
            todo = [e for e in doc["entries"] if e["kind"] == "text" and not e["en"]]
            size = sum(len(e["jp"]) for e in todo)
            if rows and chars + size > MAX_CHARS and group in ("story", "ending"):
                flush()  # a chapter stays whole when it can
            for e in todo:
                if chars + len(e["jp"]) > MAX_CHARS or len(rows) >= MAX_ENTRIES:
                    flush()
                rows.append(f"{e['id']}\t{FORM[group]}\t{limit_label(e)}\t{e['jp']}")
                chars += len(e["jp"])
    flush()
    print(f"{n} batches in {TL}")


def glossary():
    """[(jp forms, en forms)] from the tables of glossary.md."""
    rows = []
    for line in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("|") or len(cells) < 2 or cells[0] in ("JP", "---"):
            continue
        rows.append(([x.strip() for x in cells[0].split(" / ")], [x.strip() for x in cells[1].split(" / ")]))
    return rows


def has_term(jp, term):
    """term occurs as a whole kana or kanji run, so ミン doesn't match inside タイミング."""
    start = 0
    while (i := jp.find(term, start)) >= 0:
        start = i + 1
        for run in RUNS:
            if run.fullmatch(term[0]) and run.fullmatch(term[-1]):
                before = jp[i - 1] if i else " "
                after = jp[i + len(term)] if i + len(term) < len(jp) else " "
                if not run.fullmatch(before) and not run.fullmatch(after):
                    return True
                break
        else:
            return True
    return False


def problems(group, e, en, terms):
    out = []
    bad = sorted({c for c in en if not (0x20 <= ord(c) < 0x7F or c == "…" or c in e["jp"] and (GREEK.match(c) or "０" <= c <= "９"))})
    if bad:
        out.append(f"bad characters {bad}")
    if not en.strip() and group != "units" and not e["id"].startswith("DEMO/KABE4"):  # a flowed field past the paragraph's end is a deliberate single space
        out.append("empty")
    if e["id"] != "X_NYAN:19f4" and GREEK.search(e["jp"]) and "".join(GREEK.findall(e["jp"])) != "".join(GREEK.findall(en)):  # that line's υ stands in for the kanji 奸, not Koitsu's speech
        out.append("Greek must stay verbatim")
    if group in TERM_GROUPS:
        for jps, ens in terms:
            if any(has_term(e["jp"], j) for j in jps) and not any(x.lower() in en.lower() for x in ens):
                out.append(f"glossary: {jps[0]} -> {ens[0]}")
    if re.search(r"\d(st|nd|rd|th)\b", en) and not re.search(r"\d(st|nd|rd|th)\b", e["jp"]):
        pass  # literal ordinals are fine: no variable digits reach this text
    try:
        out += limits.check(e, en)
    except (ValueError, UnicodeEncodeError) as exc:
        out.append(str(exc))
    return out


def read_out(batch):
    path = TL / f"{batch}.out.tsv"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            eid, _, en = line.partition("\t")
            rows.append((eid, en))
    return rows


def check(batch, index, terms):
    want = [line.split("\t")[0] for line in (TL / f"{batch}.tsv").read_text(encoding="utf-8").splitlines() if line]
    rows = read_out(batch)
    bad = []
    if [r[0] for r in rows] != want:
        missing = sorted(set(want) - {r[0] for r in rows})
        extra = sorted({r[0] for r in rows} - set(want))
        bad.append(f"ids differ: missing {missing[:8]} extra {extra[:8]} (order must match too)")
    for eid, en in rows:
        if eid in index:
            group, e = index[eid]
            bad += [f"{eid}: {p}: {en!r}" for p in problems(group, e, en, terms)]
    return bad


def norm(jp):
    return jp.replace("　", "").rstrip("。」").rstrip("。")  # same words, whatever the closing punctuation


def memo_key(eid, jp):
    """Shouts repeat across characters with only their stretch marks changed, so those fold together."""
    key = norm(jp)
    if eid.startswith(("X_", "BAKU")):
        key = re.sub(r"\{br\}|[ー～！？ッっ、・。]", "", key)
    return key


def fill(batch, index):
    """Complete a partial bNNN.out.tsv: entries left out take the English of an identical Japanese line from any other batch's output."""
    def part(path):
        return dict(line.split("\t", 1) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

    memo = {}
    for path in sorted(TL.glob("b*.part.tsv")) + sorted(TL.glob("b*.out.tsv")):
        for eid, en in part(path).items():
            if eid in index and index[eid][0] != "units" and not eid.startswith("DEMO/KABE4"):  # flowed fields: a field's JP and EN are different words
                memo.setdefault(memo_key(eid, index[eid][1]["jp"]), en)
    have = part(TL / f"{batch}.out.tsv") if (TL / f"{batch}.out.tsv").exists() else {}
    if (TL / f"{batch}.part.tsv").exists():  # what was written by hand; wins over any earlier fill
        have.update(part(TL / f"{batch}.part.tsv"))
    want = [line.split("\t")[0] for line in (TL / f"{batch}.tsv").read_text(encoding="utf-8").splitlines() if line]
    rows, todo = [], []
    for eid in want:
        en = have.get(eid) or memo.get(memo_key(eid, index[eid][1]["jp"]))
        if en:
            rows.append(f"{eid}\t{en}")
        else:
            todo.append(eid)
    (TL / f"{batch}.out.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"{batch}: {len(rows)} filled, {len(todo)} to write")
    for eid in todo:
        print(f"{eid}\t{index[eid][1]['jp']}")


def patch(path, index):
    """Named lines only (id<TAB>English in path): each goes to its batch's .part, then that batch refills. Bios are fixed in bios.tsv instead."""
    new = dict(line.split("\t", 1) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip())
    home = {}
    for b in sorted(p for p in TL.glob("b*.tsv") if p.name.count(".") == 1):
        for line in b.read_text(encoding="utf-8").splitlines():
            home[line.split("\t")[0]] = b.stem
    if unknown := [eid for eid in new if eid not in home]:
        sys.exit(f"unknown ids: {unknown}")
    if bios := [eid for eid in new if index[eid][0] == "units"]:
        sys.exit(f"edit script/units/bios.tsv for: {bios}")
    for b in sorted({home[eid] for eid in new}):
        part = TL / f"{b}.part.tsv"
        rows = dict(line.split("\t", 1) for line in part.read_text(encoding="utf-8").splitlines() if line.strip()) if part.exists() else {}
        rows.update({eid: en for eid, en in new.items() if home[eid] == b})
        part.write_text("".join(f"{k}\t{v}\n" for k, v in rows.items()), encoding="utf-8", newline="\n")
        fill(b, index)


def batch_names(args):
    return args or sorted(p.name[:-8] for p in TL.glob("b*.out.tsv"))


def merge(batches, index):
    new = {}
    for b in batches:
        new.update(read_out(b))
    for path, doc in docs():
        touched = False
        for e in doc["entries"]:
            if e["id"] in new and e["en"] != new[e["id"]]:
                e["en"] = new[e["id"]]
                e["status"] = "done"
                touched = True
        if touched:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged {len(new)} entries")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "split":
        return split()
    index = entries()
    if cmd == "fit":
        group, e = index[args[1]]
        for line in limits.fit(e, args[0]).split("{br}"):
            print(en_text.line_width(line), line)
        print(limit_label(e), len(en_text.encode(limits.fit(e, args[0]))), "bytes", limits.check(e, args[0]))
        return
    if cmd == "fill":
        for b in args:
            fill(b, index)
        return
    if cmd == "patch":
        return patch(args[0], index)
    terms = glossary()
    failed = 0
    for b in batch_names(args):
        bad = check(b, index, terms)
        failed += bool(bad)
        print(f"{b}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
    if failed:
        sys.exit(1)
    if cmd == "merge":
        merge(batch_names(args), index)


if __name__ == "__main__":
    main()
