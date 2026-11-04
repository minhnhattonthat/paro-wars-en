"""pokes.py [--all]: every call to the digit writers, with the strings it may write into, and whether the English keeps its cells. Static, so it covers unseen screens.

The writer PAW 0x80075ea4 counts back from the string's end: last digit at halfword len-1-a3, going left down to halfword a2. The string is often computed (a table,
or a RAM buffer copied from a literal), so the candidates are every string or table named in the 30 instructions before the call, kept if the JAPANESE has blanks or
digits in those cells: a candidate that fits is the target. BAD is such a candidate whose English doesn't keep the cells (docs/re/boxes.md).
MEMCARD's own writer 0x801512bc works on a row buffer: limits.TEMPLATES covers it by hand."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import capstone  # noqa: E402
import en_text  # noqa: E402
import extract  # noqa: E402
import reloc  # noqa: E402

WRITER = 0x80075EA4
COPY = 0x800988E0  # copy a2 bytes: a shorter string brings its terminator into the buffer, which cuts whatever comes after
CELL = re.compile(b"(\x81\x40|\x82[\x4f-\x58])")  # a blank or a fullwidth digit
BLANK = b"\x81\x40"
NOT_TARGET = {("PAW:a8794", 7, 4)}  # named just before the call, whose string is the fuel line PAW:a8ac8 (ok on the shots)
MD =capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
MD.skipdata = True


def scan(ins):
    """(addresses named by lui pairs, a2, a3) over a run of instructions, branches ignored."""
    hi, imm, named = {}, {"$zero": 0}, set()
    for i in ins:
        ops = [x.strip() for x in i.op_str.split(",")]
        m = i.mnemonic
        if m == "lui":
            hi[ops[0]] = int(ops[1], 0) << 16
            imm.pop(ops[0], None)
        elif m == "addiu" and len(ops) == 3 and ops[1] in hi:
            named.add(hi[ops[1]] + int(ops[2], 0))
            if ops[0] != ops[1]:
                imm.pop(ops[0], None)
            else:
                del hi[ops[1]]
        elif m == "addiu" and len(ops) == 3 and ops[1] == "$zero":
            imm[ops[0]] = int(ops[2], 0)
        elif m == "move" and ops[1] in imm:
            imm[ops[0]] = imm[ops[1]]
        elif m == "addu" and len(ops) == 3 and ops[0] == ops[1] and ops[0] in hi:
            pass  # lui at; addu at,at,index; lw x,table(at)
        elif m.startswith("l") and m not in ("lui", "li") and len(ops) == 2:
            at = re.fullmatch(r"(-?\w+)\((\$\w+)\)", ops[1])
            if at and at[2] in hi:
                named.add(hi[at[2]] + int(at[1], 0))
            imm.pop(ops[0], None)
        elif ops and ops[0].startswith("$") and not m.startswith(("s", "b", "j", "mult", "div")):
            imm.pop(ops[0], None)
            hi.pop(ops[0], None)
    return named, imm.get("$a2"), imm.get("$a3")


def disc_string(data, off):
    """The bytes of a string on the disc, up to the writer's own end test: a byte below 2 at a halfword."""
    end = off
    while end < len(data) and data[end] >= 2:
        end += 2
    return data[off:end]


def fits(enc, a2, a3, cell):
    """Do the writer's cells of this encoded string all match?"""
    last = len(enc) // 2 - 1 - a3
    return last >= a2 and all(cell(enc[c * 2 : c * 2 + 2]) for c in range(a2, last + 1))


def main():
    show_all = "--all" in sys.argv
    docs = list(batches.docs())
    files = {}
    for _, doc in docs:
        files.setdefault(doc["file"], []).append(doc)
    # A string is known by its address: literal offset in its own file, or through a word ref in any table.
    addr, table = {}, {}
    bases = {}
    for rel, ds in files.items():
        if ds[0]["lz"] is not None:
            continue
        data = (ROOT / "work/disc/tree" / rel).read_bytes()
        bases[rel] = reloc.PAW_BASE if rel == "PAW.EXE" else extract.best_base(data, [e for d in ds for e in d["entries"]])
        addr[rel] = {}
        for d in ds:
            for e in d["entries"]:
                addr[rel][bases[rel] + e["off"]] = e
                e["raw"] = disc_string(data, e["off"])
                for ref in e.get("refs") or ():
                    name, at = ref.split(":")
                    if at.startswith("w"):
                        table.setdefault(name, {})[int(at[1:], 16)] = e
    paw = addr["PAW.EXE"]
    fails = unresolved = good = 0
    done = set()
    for rel in bases:
        name = "PAW" if rel == "PAW.EXE" else Path(rel).stem
        data = (ROOT / "work/disc/tree" / rel).read_bytes()
        ins = list(MD.disasm(data, bases[rel]))
        for n, i in enumerate(ins):
            if i.mnemonic != "jal" or int(i.op_str, 0) != WRITER:
                continue
            named, a2, a3 = scan(ins[max(0, n - 30) : n] + ins[n + 1 : n + 2])
            where = f"{rel}:{i.address:08x}"
            if a2 is None or a3 is None:
                unresolved += 1
                if show_all:
                    print(f"args computed {where} a2={a2} a3={a3}")
                continue
            cands = []
            for a in named:
                e = addr[rel].get(a) or paw.get(a)
                if e:
                    cands.append(e)
                for t in (table.get(name, {}), table.get("PAW", {})):
                    k = a
                    while k in t:  # a table of strings, walk it
                        cands.append(t[k])
                        k += 4
            hit = False
            for e in {x["id"]: x for x in cands}.values():
                if not fits(e["raw"], a2, a3, lambda b: CELL.fullmatch(b)):
                    continue
                hit = True
                if e["kind"] != "text":
                    continue
                en = en_text.encode(e["en"].replace("{_}", "　"))
                # The last digit's cell must be a blank. Cells further left only matter for a number that long, and a label there still reads (Left:10).
                last = len(en) // 2 - 1 - a3
                ok = last >= a2 and en[last * 2 : last * 2 + 2] == BLANK
                key = (e["id"], a2, a3)
                if key in done or key in NOT_TARGET:
                    continue
                done.add(key)
                if ok:
                    good += 1
                else:
                    fails += 1
                if show_all or not ok:
                    print(f"{'ok' if ok else 'BAD'} {where} {e['id']} a2={a2} a3={a3} jp={e['jp']!r} en={e['en']!r}")
            if not hit:
                unresolved += 1
                if show_all:
                    print(f"no candidate {where} a2={a2} a3={a3} named={sorted(hex(a) for a in named)}")
    print(f"{good} ok, {fails} bad, {unresolved} calls without a text candidate")
    copies = 0
    for rel in bases:
        ins = list(MD.disasm((ROOT / "work/disc/tree" / rel).read_bytes(), bases[rel]))
        for n, i in enumerate(ins):
            if i.mnemonic != "jal" or int(i.op_str, 0) != COPY:
                continue
            named, a2, _ = scan(ins[max(0, n - 8) : n] + ins[n + 1 : n + 2])
            for a in named:
                e = addr[rel].get(a) or paw.get(a)
                if not e or e["kind"] != "text" or a2 is None:
                    continue
                size = len(en_text.encode(e["en"].replace("{_}", "　")))
                if size != a2 and e["id"] not in ("MEMCARD:80", "MEMCARD:94"):  # the Japanese is shorter than the copy too: the row ends there, and no digits follow
                    fails += 1
                    copies += 1
                    print(f"COPY {rel}:{i.address:08x} {e['id']} copies {a2} bytes, English is {size}: jp={e['jp']!r} en={e['en']!r}")
    print(f"{copies} fixed copies whose English isn't that long")
    return fails


if __name__ == "__main__":
    main()
