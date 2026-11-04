"""Reviewer pairs from work/tl/*.out.tsv: work/tl/pairs/pNN.txt, `>> id | JP` then the English, in batch order.

A line already shown (same Japanese and English) is dropped, so a chapter repeated by each nation is read once;
each unit bio is one paragraph; a new file starts at about --size bytes, on a new id family.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches


def rows(index):
    """(family, id, jp, en) in batch order."""
    bios = {}
    for path in sorted(batches.TL.glob("b*.out.tsv")):
        for eid, en in batches.read_out(path.name[:-8]):
            group, e = index[eid]
            family = eid.split(":")[0]
            if group == "units":
                bios.setdefault(family, []).append((eid, e["jp"].replace("　", ""), en.strip()))
                continue
            yield family, eid, e["jp"], en
    for family, lines in bios.items():
        yield family, lines[0][0], "".join(x[1] for x in lines), " ".join(x[2] for x in lines if x[2])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--size", type=int, default=60000)
    args = ap.parse_args()
    out = batches.TL / "pairs"
    out.mkdir(exist_ok=True)
    for old in out.glob("p*.txt"):
        old.unlink()
    seen, chunk, size, n, last = set(), [], 0, 0, None

    def flush():
        nonlocal chunk, size, n
        if chunk:
            n += 1
            (out / f"p{n:02}.txt").write_text("\n".join(chunk) + "\n", encoding="utf-8", newline="\n")
        chunk, size = [], 0

    for family, eid, jp, en in rows(batches.entries()):
        if (jp, en) in seen:
            continue
        seen.add((jp, en))
        if size > args.size and family != last:
            flush()
        last = family
        text = f">> {eid} | {jp}\n{en}"
        chunk.append(text)
        size += len(text.encode("utf-8"))
    flush()
    print(f"{n} files, {len(seen)} pairs in {out}")


if __name__ == "__main__":
    main()
