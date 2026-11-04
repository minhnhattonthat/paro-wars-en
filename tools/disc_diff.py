"""disc_diff.py A.bin B.bin: classify every differing sector of two MODE2/2352 images by field.

Prints a count per field combination, then runs of differing sectors with their fields and the
ISO file (or gap) they fall in, per image A's directory tree."""
import sys
from collections import Counter

from disc import SECTOR, walk

FIELDS = (("sync+hdr", 0, 16), ("subhdr", 16, 24), ("data", 24, 2072), ("form1end", 2072, 2076), ("ecc", 2076, 2352))


def diff_fields(a, b):
    return tuple(name for name, lo, hi in FIELDS if a[lo:hi] != b[lo:hi])


def main(path_a, path_b):
    with open(path_a, "rb") as f:
        files = walk(f)
    starts = sorted((lba, n, name) for name, lba, n, _ in files)
    counts, runs = Counter(), []
    with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
        lba = 0
        while True:
            a, b = fa.read(SECTOR * 256), fb.read(SECTOR * 256)
            if not a and not b:
                break
            if a != b:
                for i in range(0, max(len(a), len(b)), SECTOR):
                    sa, sb = a[i : i + SECTOR], b[i : i + SECTOR]
                    if sa != sb:
                        kinds = diff_fields(sa, sb)
                        counts[kinds] += 1
                        s = lba + i // SECTOR
                        if runs and runs[-1][1] == s - 1 and runs[-1][2] == kinds:
                            runs[-1][1] = s
                        else:
                            runs.append([s, s, kinds])
            lba += len(a) // SECTOR
    for kinds, n in counts.most_common():
        print(f"{n:7} {'+'.join(kinds)}")

    def where(s):
        hit = "(gap)"
        for lo, n, name in starts:
            if lo > s:
                break
            if s < lo + max(n, 1):
                hit = name
        return hit

    print(f"{len(runs)} runs")
    for lo, hi, kinds in runs[:200]:
        print(f"{lo:7}-{hi:7} {'+'.join(kinds):28} {where(lo)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
