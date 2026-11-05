"""Reviewer sheets from a warp tour: qa_sheets.py [TOUR] -> TOUR/sheets/sheet_<family>[_N].png, native size, 16 frames a page, repeats dropped.
Beside each family, sheet_<family>.txt names its tiles in order. warp_all's own sheets are half size, too small to read text on.
"""
import glob
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SCRIPTS


def main():
    tour = sys.argv[1] if len(sys.argv) > 1 else "work/qa/tour"
    out = os.path.join(tour, "sheets")
    os.makedirs(out, exist_ok=True)
    families = {}
    for scene in sorted(os.listdir(tour)):
        pngs = sorted(glob.glob(os.path.join(tour, scene, "*.png")))
        if pngs and scene != "sheets":
            families.setdefault(scene if scene.startswith("full_") else scene.split("_")[0], []).extend(pngs)  # a whole chapter is a family of its own
    for fam, pngs in families.items():
        p = subprocess.run([sys.executable, "-X", "utf8", f"{SCRIPTS}/sheet.py", *pngs, "--cols", "4", "--div", "1", "--max", "16", "--changed", "0.01",
                            "--out", os.path.join(out, f"sheet_{fam}.png")], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode:
            sys.exit(p.stderr)
        Path(out, f"sheet_{fam}.txt").write_text(p.stdout, encoding="utf-8")
    print(len(glob.glob(os.path.join(out, "*.png"))), "sheets in", out)


main()
