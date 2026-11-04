"""Recon: map the {size, lba, ram} file records in PAW.EXE and SLPM_860.16 to ISO file names.

usage: disc_tables.py "rom/Paro Wars (Japan).bin" work/disc/tree [OUT.tsv]
A record is three u32s: size equal to the ISO size (or rounded up to a sector), lba of a known file, and a RAM address.
Prints a per-exe summary, and which ISO files no record names (those are found another way: computed LBAs or CdSearchFile)."""
import os
import struct
import sys


def sector(f, n):
    f.seek(n * 2352 + 24)
    return f.read(2048)


def walk(f, lba, size, prefix=""):
    out = {}
    data = b"".join(sector(f, lba + i) for i in range((size + 2047) // 2048))
    o = 0
    while o < len(data):
        n = data[o]
        if n == 0:
            o = (o // 2048 + 1) * 2048
            continue
        rec = data[o:o + n]
        name = rec[33:33 + rec[32]]
        if name not in (b"\0", b"\1"):
            la, sz = struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]
            nm = name.decode("ascii").split(";")[0]
            if rec[25] & 2:
                out.update(walk(f, la, sz, prefix + nm + "/"))
            else:
                out[la] = (prefix + nm, sz)
        o += n
    return out


def records(data, iso):
    found = []
    for o in range(0, len(data) - 11, 2):  # 2-aligned: some tables sit on halfword boundaries
        size, lba, ram = struct.unpack_from("<III", data, o)
        if lba in iso and ram >> 24 == 0x80:
            name, real = iso[lba]
            if size == real or (size + 2047) // 2048 == (real + 2047) // 2048:
                found.append((o, size, lba, ram, name, real))
    return found


def main():
    binpath, tree = sys.argv[1:3]
    with open(binpath, "rb") as f:
        pvd = sector(f, 16)
        root = pvd[156:190]
        iso = walk(f, struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0])
    print("iso files", len(iso))
    named = set()
    rows = []
    for exe in ("PAW.EXE", "SLPM_860.16"):
        data = open(os.path.join(tree, exe), "rb").read()
        recs = records(data, iso)
        print(exe, "records", len(recs), f"first {recs[0][0]:#x} last {recs[-1][0]:#x}" if recs else "")
        for o, size, lba, ram, name, real in recs:
            named.add(lba)
            rows.append(f"{exe}\t{o:#x}\t{size:#x}\t{lba}\t{ram:08x}\t{name}\t{real:#x}")
    if len(sys.argv) > 3:
        open(sys.argv[3], "w", encoding="utf-8").write("\n".join(rows) + "\n")
    missing = {}
    for lba, (name, _) in iso.items():
        if lba not in named:
            key = name.rsplit("/", 1)[0] if "/" in name else "."
            missing[key] = missing.get(key, 0) + 1
    print("not named by any record, per dir:", dict(sorted(missing.items())))


if __name__ == "__main__":
    main()
