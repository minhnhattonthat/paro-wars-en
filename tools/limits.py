"""Width and length limits of every text entry, from the width gate (docs/re/boxes.md).

limit(doc, entry) -> Limit(px, wrap, bytes): px per line (the last value repeats only if wrap is False and JP has more lines),
wrap True when the tool breaks lines itself, bytes None when the string can move (reloc.py). check() is the lint; fit() adds the {br}s.
"""
import collections
import re

import en_text
import menu_tables

Limit = collections.namedtuple("Limit", "px wrap bytes")

PAGE = [296, 296, 284]  # story and ending pages: 3 lines, the page arrow sits at the end of the third (ruler, work/qa/torture)
SHOUT = [168, 168]  # battle speech box, 14 columns of 12 px, two rows
DIALOG_MARGIN = 12
FAMILY_PX = {"P_*": 300, "SEL_HELP": 288, "DEMO/KABE4": 144, "UNITINFO": 144}  # one x for the whole family, so the widest Japanese line holds for all

WRAPPED = {"SELECT:54": [96] * 3, "SELECT:80": [156] * 2, "SELECT:134": [96] * 2}  # relied on the wrap column (8, 13, 8) the English renderer ignores; layout by {br}

_menus = None


def family(eid):
    name = eid.split(":")[0]
    for pat, to in ((r"DEMO/TXT_\w+", "DEMO/TXT"), (r"ENDING/\w+_TXT", "ENDING/x_TXT"), (r"ENDING/TXT_END", "ENDING/x_TXT"), (r"P_\w+", "P_*"), (r"X_\w+", "X_*")):
        name = re.sub("^" + pat + "$", to, name)
    return name


def jp_px(jp):
    return [len(line) * 12 for line in jp.split("{br}")]


def capacity(entry):
    """Bytes of text a slot holds: a NUL must follow at a halfword."""
    return (entry["len"] - 1) & ~1


def limit(entry):
    global _menus
    if _menus is None:
        _menus = menu_tables.index()
    fam = family(entry["id"])
    size = None if entry.get("refs") else capacity(entry)
    if entry["id"] in WRAPPED:
        return Limit(WRAPPED[entry["id"]], False, size)
    if fam in ("DEMO/TXT", "ENDING/x_TXT"):
        return Limit(PAGE, True, size)
    if fam in ("X_*", "BAKU", "LOCS_OV", "HELP_OV"):
        return Limit(SHOUT, True, size)
    if entry["id"] in _menus:
        x, w = _menus[entry["id"]]
        return Limit([(w + 1) * 16 - DIALOG_MARGIN - x], False, size)
    if fam in FAMILY_PX:
        return Limit([FAMILY_PX[fam]], False, size)
    return Limit(jp_px(entry["jp"]), False, size)


def fit(entry, text):
    """The text with line breaks: greedy on spaces for families that wrap, untouched otherwise. An explicit {br} stays."""
    lim = limit(entry)
    if not lim.wrap:
        return text
    out, row = [], 0
    for para in text.split("{br}"):
        line = ""
        for word in para.split(" "):
            trial = f"{line} {word}" if line else word
            if line and en_text.line_width(trial) > lim.px[min(row, len(lim.px) - 1)]:
                out.append(line)
                row += 1
                line = word
            else:
                line = trial
        out.append(line)
        row += 1
    return "{br}".join(out)


def check(entry, text):
    """Problems of an English text in its box: empty when it fits."""
    lim = limit(entry)
    problems = []
    lines = fit(entry, text).split("{br}")
    if lim.wrap and len(lines) > len(lim.px):
        problems.append(f"{len(lines)} lines, box holds {len(lim.px)}")
    if not lim.wrap and len(lines) > len(lim.px):
        problems.append(f"{len(lines)} lines, field holds {len(lim.px)}")
    for i, line in enumerate(lines):
        allowed = lim.px[min(i, len(lim.px) - 1)]
        if en_text.line_width(line) > allowed:
            problems.append(f"line {i + 1} is {en_text.line_width(line)} px, limit {allowed}")
    size = len(en_text.encode(fit(entry, text)))
    if lim.bytes is not None and size > lim.bytes:
        problems.append(f"{size} bytes, slot holds {lim.bytes}")
    return problems


def _selftest():
    page = {"id": "DEMO/TXT_PEN0:96", "jp": "あ", "len": 150}
    assert fit(page, "a b") == "a b"
    long = " ".join(["word"] * 28)
    assert fit(page, long).count("{br}") >= 1
    assert check(page, long) == []
    assert check(page, " ".join(["word"] * 200))
    label = {"id": "PAW:0", "jp": "移動", "len": 8, "refs": ["PAW:w80000000"]}
    assert limit(label).px == [24]
    assert check(label, "Mo") == []
    assert check(label, "Move it now") != []


if __name__ == "__main__":
    _selftest()
    print("ok")
