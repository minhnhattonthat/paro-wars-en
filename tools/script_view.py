"""Print script/ compactly, one file per block: hexoff[*][/kind]:jp joined by |. * = no code reference found.

usage: script_view.py [NAME_SUBSTRING [KIND]]   e.g. script_view.py menu/LOCS   script_view.py story data"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    a = sys.argv[1:]
    for f in sorted(glob.glob(str(ROOT / "script/*/*.json"))):
        if a and a[0] not in f.replace("\\", "/"):
            continue
        doc = json.loads(Path(f).read_text(encoding="utf-8"))
        items = []
        for e in doc["entries"]:
            if len(a) > 1 and e["kind"] != a[1]:
                continue
            mark = "*" if "refs" in e and not e["refs"] else ""
            kind = "" if e["kind"] == "text" else "/" + e["kind"]
            items.append(f"{e['off']:x}{mark}{kind}:{e['jp']}")
        print("##", doc["file"], len(doc["entries"]))
        print("|".join(items))


if __name__ == "__main__":
    main()
