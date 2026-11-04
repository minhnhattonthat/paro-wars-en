"""Print entries by id or regex on the id / jp / en: show.py [-e EN_REGEX] [-j JP_REGEX] [ID_REGEX ...]. One line each: id, slot, refs, jp, en."""
import argparse
import re

import batches


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("-e")
    ap.add_argument("-j")
    a = ap.parse_args()
    for eid, (group, e) in batches.entries().items():
        if a.ids and not any(re.fullmatch(p, eid) for p in a.ids):
            continue
        if (a.e and not re.search(a.e, e["en"])) or (a.j and not re.search(a.j, e["jp"])):
            continue
        print(f"{eid}\t{e['len']}\t{len(e.get('refs') or [])}\t{e['jp']}\t{e['en']}")


if __name__ == "__main__":
    main()
