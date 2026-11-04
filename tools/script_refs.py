"""Show script entries matching a Japanese regex, with what reaches them: script_refs.py REGEX [NAME]"""
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
pat = re.compile(sys.argv[1])
want = sys.argv[2] if len(sys.argv) > 2 else None
for path in sorted(glob.glob(str(ROOT / "script/*/*.json"))):
    if want and want not in path:
        continue
    for e in json.loads(Path(path).read_text(encoding="utf-8"))["entries"]:
        if pat.search(e["jp"]):
            print(e["id"], e["len"], e["kind"], repr(e["jp"]), " ".join(e.get("refs", [])))
