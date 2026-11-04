"""build.py: build/paro_wars_en.cue/.bin from the pinned dump. No edits yet: the output is the original disc.

Patched files go through disc.write_files, which keeps every file at its LBA."""
import hashlib
import shutil
from pathlib import Path

import check_rom

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "rom" / "Paro Wars (Japan).bin"
OUT = ROOT / "build" / "paro_wars_en.bin"


def main():
    check_rom.check()
    OUT.parent.mkdir(exist_ok=True)
    shutil.copyfile(ORIG, OUT)
    cue = ORIG.with_suffix(".cue").read_text(encoding="ascii")
    OUT.with_suffix(".cue").write_text(cue.replace(ORIG.name, OUT.name), encoding="ascii", newline="\r\n")
    with open(OUT, "rb") as f:
        print(OUT, hashlib.file_digest(f, "sha1").hexdigest())


if __name__ == "__main__":
    main()
