"""Disc occupancy: every ISO file by LBA, with what its sectors hold. disc_map.py [REGEX] lists files; --gaps lists unused LBA runs.
Files' LBAs are compiled in; a gap belongs to no file, so the game can only read it if a record is repointed there (docs/re/disc.md)."""
import argparse
import re

import disc
import build


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("regex", nargs="?")
    ap.add_argument("--gaps", action="store_true")
    a = ap.parse_args()
    with open(build.ORIG, "rb") as f:
        rows = sorted((lba, n, size, path) for path, lba, n, size in disc.walk(f))
    if a.regex:
        for lba, n, size, path in rows:
            if re.search(a.regex, path):
                print(f"{lba}\t{n}\t{size}\t{path}")
    if a.gaps:
        end = 0
        for lba, n, size, path in rows:
            if lba > end:
                print(f"gap {end} +{lba - end} before {path}")
            end = max(end, lba + n)
        print(f"last used sector {end}, image {build.ORIG.stat().st_size // disc.SECTOR}")


if __name__ == "__main__":
    main()
