"""Recon: alternate hex gaps and Shift-JIS runs of a file. usage: sjis_view.py FILE [START [END [LZ_OFFSET]]] (hex with 0x; LZ_OFFSET decodes first)"""
import sys

import lzkc


def dbl(x, y):
    return (0x81 <= x <= 0x84 or 0x88 <= x <= 0x9F or 0xE0 <= x <= 0xEA) and 0x40 <= y <= 0xFC and y != 0x7F


def main():
    a = sys.argv[1:]
    d = open(a[0], "rb").read()
    if len(a) > 3:
        d = lzkc.decompress(d[int(a[3], 0):], strict=True)
        print("decoded", hex(len(d)))
    i = gap = int(a[1], 0) if len(a) > 1 else 0
    end = min(int(a[2], 0), len(d)) if len(a) > 2 else len(d)
    while i < end:
        if i + 1 < end and dbl(d[i], d[i + 1]):
            j = i
            while j + 1 < end and dbl(d[j], d[j + 1]):
                j += 2
            if gap < i:
                print(f"  {gap:#x}: {d[gap:i][:48].hex(' ')}{' ..' if i - gap > 48 else ''}")
            print(f"{i:#x} {j - i}: {d[i:j].decode('cp932', 'backslashreplace')}")
            i = gap = j
        else:
            i += 1
    if gap < end:
        print(f"  {gap:#x}: {d[gap:end][:48].hex(' ')}")


if __name__ == "__main__":
    main()
