"""Reach every scene of tools/debug/scenes.tsv from a cold boot; each run leaves work/qa/warp/<scene>/<scene>.png, then one contact sheet per scene family.

usage: python -X utf8 tools/debug/warp_all.py [--rom CUE] [--only REGEX] [--jobs 4] [--out work/qa/warp] [--state-dir work/states]
Exit 0 only when every selected scene finished on its own (warp.lua logs "reached"). With --state-dir, also keeps a savestate per scene."""
import argparse
import concurrent.futures as cf
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from skill import SKILL  # noqa: E402

FRAMES = "60000"


def scenes():
    with open(os.path.join(HERE, "scenes.tsv"), encoding="utf8") as f:
        return [line.split("\t")[0] for line in f.read().splitlines() if line and not line.startswith("#")]


def run(name, a):
    out = os.path.join(a.out, name)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    cmd = [sys.executable, "-X", "utf8", f"{SKILL}/scripts/emu.py", a.rom, "--out", out, "--script", os.path.join(HERE, "warp.lua"),
           "--var", f"SCENE='{name}'", "--frames", FRAMES, "--timeout", "900"]
    if a.state_dir:
        cmd += ["--state-out", os.path.join(a.state_dir, name + ".sstate")]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf8", errors="replace")
    with open(os.path.join(out, "run.txt"), "w", encoding="utf8") as f:
        f.write(p.stdout + p.stderr)
    log = open(os.path.join(out, "log.txt"), encoding="utf8", errors="replace").read() if os.path.exists(os.path.join(out, "log.txt")) else ""
    png = os.path.join(out, name + ".png")
    ok = p.returncode == 0 and "reached " + name in log and os.path.exists(png)
    return name, ok, p.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", default="rom/Paro Wars (Japan).cue")
    ap.add_argument("--only")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default="work/qa/warp")
    ap.add_argument("--state-dir")
    a = ap.parse_args()
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)
    if a.state_dir:
        a.state_dir = os.path.abspath(a.state_dir)
        os.makedirs(a.state_dir, exist_ok=True)
    names = [n for n in scenes() if not a.only or re.search(a.only, n)]
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda n: run(n, a), names))
    bad = [r for r in results if not r[1]]
    with open(os.path.join(a.out, "results.tsv"), "a", encoding="utf8") as f:  # partial --only reruns add to the record
        for name, ok, code in results:
            f.write(f"{name}\t{'ok' if ok else 'FAIL'}\t{code}\n")
    families = {}
    for name, ok, _ in results:
        if ok:
            families.setdefault(name.split("_")[0], []).append(os.path.join(a.out, name, name + ".png"))
    for fam, pngs in families.items():
        subprocess.run([sys.executable, "-X", "utf8", f"{SKILL}/scripts/sheet.py", *pngs, "--cols", "6", "--div", "2", "--max", "36",
                        "--out", os.path.join(a.out, f"sheet_{fam}.png")], capture_output=True)
    print(f"{len(results) - len(bad)}/{len(results)} scenes reached; sheets in {a.out}")
    for name, _, code in bad:
        print(f"FAIL {name} exit {code}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
