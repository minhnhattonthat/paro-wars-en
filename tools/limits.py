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
STUB = 6  # a wrapped paragraph's last line needs this many characters
FAMILY_PX = {"P_*": 300, "SEL_HELP": 288, "DEMO/KABE4": 144, "UNITINFO": 144}  # one x for the whole family, so the widest Japanese line holds for all

FAR_MARK = 0x1C  # first byte of a far string: asm/vwf.asm, for table fields nothing points at
NO_FAR = {"DEMO/TXT", "ENDING/x_TXT", "X_*", "BAKU", "P_*", "DEMO/KABE4"}  # pages and fields read by more than the window code, and they fit anyway
PAW_TABLES = (0x8F404, 0x91E60)  # fixed-stride tables (text.md): a ref may be the table's base, so a long entry goes far and is never repointed

# Number templates: halfword indices the code writes digits into, read from RAM on the original (tools/debug/room.py --pokes). The English keeps
# a fullwidth blank at each; pen order is free, so a tab can put the digits past a long label, and those strings move (their refs are one pointer each).
_stat = [2, 3, 4]  # 命中　　　 and its row: two kanji, then three digits
TEMPLATES = {
    **{f"PAW:{a:x}": _stat for a in [0xa9054, 0xa9060, 0xa906c, 0xa9078, 0xa9084, 0xa9090, 0xa909c, 0xa9104, 0xa9110, 0xa911c, 0xa9128, 0xa9134, 0xa9140, 0xa914c,
                                     0xa91b4, 0xa91c0, 0xa91cc, 0xa91d8, 0xa91e4, 0xa91f0, 0xa91fc, 0xa9264, 0xa9270, 0xa927c, 0xa9288, 0xa9294, 0xa92a0, 0xa92ac]},
    "PAW:a8794": [2, 3, 7, 8, 12, 13],  # 空　３８　陸　５８　海　４８
    "PAW:a8da0": [2, 3, 7, 8, 12, 13],
    "PAW:a8a6c": [5, 6, 8, 9, 18, 19],  # 機　数　　　８／　８　＠移動力　　　１０
    "PAW:a8a40": [5, 8, 9, 18, 19],
    "PAW:a8c70": [0, 1, 2],  # ３４０ウッキー
    "PROD_OV:24f8": [0, 1, 2],
    "PROD_OV:2604": [0, 1, 2],
    "PROD_OV:2708": [0, 1, 2],
    "PROD_OV:2814": [0, 1, 2],
    "PROD_OV:28dc": [0, 1, 2, 3, 4, 5, 6],  # the money line writes over the whole string
    "NSHOP_OV:20": [0, 1, 2, 3, 4],  # 　　６００ウッキー
    "PAW:a9530": [12],  # テレポーテーション　あと３回
    "PAW:a9550": [12],
    "PAW:a9570": [12],
    "BUTAI_OV:2594": [1, 2],  # 海８０: the code blanks all but the first halfword, so the labels live in `Defense:` (BUTAI_OV:25ac)
    "BUTAI_OV:259c": [1, 2],
    "BUTAI_OV:25a4": [1, 2],
    "PAW:a8ac8": [7, 8, 9, 11, 12, 13],  # fuel, ９／９９９: a tab puts the digits back past the bar, the blanks draw at 6 px
    # Counted from the end, so the text after the digit is exactly as long as the Japanese's (tools/debug/pokes.py): ３機スタック, あと３機, （３部隊）
    "PAW:a7170": [0],
    "PAW:a71c0": [0],
    "PAW:a964c": [0],
    "PAW:a9658": [3],
    "LOCEX_OV:361c": [3],
    "GORYU_OV:4": [0, 1],
    # SAVE_TITLE: 32 cells, the game's name at 0, one of these at 7 with the nation over its start, digits by the title's end.
    "MEMCARD:bc": [3, 4, 9, 10, 11, 16, 17, 18, 20, 21],
    "MEMCARD:ec": [0, 1, 2, 3, 6, 9, 10, 11, 16, 17, 18, 20, 21],
}
# The string's length in halfwords is fixed. The price writer counts its digits back from the string's end; the commander panel ends the string right
# after its digits, so a label past them vanishes and only 4 letters fit in front (shots and RAM dumps, work/qa/p7g).
HALFWORDS = {"PAW:a8c70": 7, "PROD_OV:24f8": 7, "PROD_OV:2604": 7, "PROD_OV:2708": 7, "PROD_OV:2814": 7, "NSHOP_OV:20": 9,
             "BUTAI_OV:2594": 3, "BUTAI_OV:259c": 3, "BUTAI_OV:25a4": 3,
             "PAW:a7170": 6, "PAW:a71c0": 6, "PAW:a964c": 5, "PAW:a9658": 5, "LOCEX_OV:361c": 5, "GORYU_OV:4": 5,
             "MEMCARD:ac": 6, "MEMCARD:bc": 23, "MEMCARD:ec": 23, **{f"MEMCARD:{a:x}": 4 for a in (0x14, 0x20, 0x2C, 0x38, 0x44, 0x50, 0x5C, 0x68)},
             **{i: 5 for i, want in TEMPLATES.items() if want is _stat}}
# The save file's title on the card (MEMCARD 0x801510f0, seen in the .mcd), shown by the console's card manager and not by this game: Shift-JIS fullwidth only,
# no tabs or letters of our font. Copied by length, so a short string's terminator would cut the title.
SAVE_TITLE = {f"MEMCARD:{a:x}" for a in (0xAC, 0xBC, 0xEC, 0x14, 0x20, 0x2C, 0x38, 0x44, 0x50, 0x5C, 0x68)}
# The caller centres these by halfword count, x = centre - 6 * count: at 4 or more the first letter goes under the frame. A leading {x:12} costs one
# halfword (6 px left) and gains 12, which brings a long label back into the column (x from tools/debug/boxes.lua).
CENTRED = re.compile(r"CNTRY_ST:5[a-f][0-9a-f]|PAW:b3(084|0c0|0f0|120|150)")

# Real room from the windows' positions on the original (tools/debug/room.py) and shots of the English: id regex -> px. Wins over the Japanese's own width.
MEASURED = [
    (r"PAW:917[0-9a-f]{2}|PAW:918[01][0-9a-f]", 50),  # ranks: 50 in the commander panel, 63 in unit info
    (r"PAW:90[bc][0-9a-f]{2}|PAW:90d[0-3][0-9a-f]", 61),  # unit classes: the unit list's Type column
    (r"PAW:918[4-9a-b][0-9a-f]|PAW:919[0-9a-f]{2}|PAW:91a[0-9a-f]{2}", 104),  # terrain and buildings: the map's bubble
    (r"CNTRY_ST:5[a-f][0-9a-f]", 55),  # label column to the frame at 49, measured from the window x of a 5-halfword label (-6): CENTRED
    (r"LOCEX_OV:36[89a][0-9a-f]", 96),  # deploy message: the list runs on after "Deploy locations:"
    (r"NSHOP_OV:(2[d-f][0-9a-f]|30[0-9a-f])", 130),  # shop item list
    (r"BUTAI_OV:27[b-c][0-9a-f]", 43),  # the unit list's Plan column, x=269 to the frame
    (r"PAW:a94d0", 126),  # window x is 12 left of the column at 12 halfwords: CENTRED
    (r"BUTAI_OV:25(94|9c|a4)", 60),  # defense cells, 60 apart
    (r"BUTAI_OV:25ac", 190),  # Defense: and the three labels, x=78 to the last cell's digits
    (r"BUTAI_OV:2a40", 27),  # x=67 to the frame at 92: the e touches it, a tab would only clip the N
    (r"BUTAI_OV:2[34][0-9a-f]{2}", 110),
    (r"PAW:b3(084|0c0|0f0|120|150)", 62),  # unit info's first column, from the window x of a 5-halfword label (-5) to the number at 57: CENTRED
    (r"PAW:b3(16[0-7]|17[0-7]|08[0-9a-f]|09[0-9a-f]|0[a-f][0-9a-f]|1[0-5][0-9a-f])", 50),  # unit info stat labels: 44 to the number's window, whose first cell is a blank
    (r"PAW:b3168", 51),
    (r"PAW:b3178", 77),
    (r"PAW:b31(8[0-9a-f]|9[0-9a-f])", 30),  # weapon table headers, one 30 px column each
    (r"PAW:b32(8c|94|9c)", 44),
    (r"PAW:9d8", 44),
    (r"PAW:a87b4", 84),
    (r"PAW:a99[0-9a-f]{2}", 76),
    (r"PAW:a9(05|06|07|08|09|10|11|12|13|14|1b|1c|1d|1e|1f|26|27|28|29|2a)[0-9a-f]", 64),  # stat cells of the commander panel, 64 apart
    (r"CNTRY_ST:(9[5-9a-f][0-9a-f]|a0[0-9a-f])", 66),  # nation name columns
    (r"PAW:907[0-9a-f]{2}|PAW:9[0-9a-f]{4}", 130),  # unit names, weapons: their columns hold the longest Japanese names
]

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
    size = None if entry.get("refs") or (fam not in NO_FAR and entry["len"] >= 6) else capacity(entry)
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
    for pattern, px in MEASURED:
        if re.fullmatch(pattern, entry["id"]):
            return Limit([max(px, *jp_px(entry["jp"]))], False, size)
    return Limit(jp_px(entry["jp"]), False, size)


def far_only(entry):
    """In a fixed table: never repoint it, whatever refs it has."""
    return entry["id"].startswith("PAW:") and PAW_TABLES[0] <= entry["off"] < PAW_TABLES[1]


def template_problems(entry, text):
    enc = en_text.encode(text)
    want = TEMPLATES.get(entry["id"], ())
    out = [f"halfword {i} must stay a fullwidth blank for the digits the code writes" for i in want if enc[i * 2:i * 2 + 2] != b"\x81\x40"]
    fixed = HALFWORDS.get(entry["id"])
    if fixed and (len(enc) + 1) // 2 != fixed:
        out.append(f"{(len(enc) + 1) // 2} halfwords, the code needs exactly {fixed}")
    if CENTRED.fullmatch(entry["id"]) and len(enc) > 6 and not text.startswith("{x:"):
        out.append("over 3 halfwords in a centred column: start with {x:12}")
    return out


def wrapped(entry, text):
    """Per paragraph, its lines: greedy on spaces, then words move down from the line above while the last line is a stub."""
    px = limit(entry).px
    paras, row = [], 0
    for para in text.split("{br}"):
        lines, line = [], ""
        for word in para.split(" "):
            trial = f"{line} {word}" if line else word
            if line and en_text.line_width(trial) > px[min(row, len(px) - 1)]:
                lines.append(line)
                row += 1
                line = word
            else:
                line = trial
        lines.append(line)
        while len(lines) > 1 and len(lines[-1]) < STUB:
            head, _, word = lines[-2].rpartition(" ")
            trial = f"{word} {lines[-1]}"
            if not head or en_text.line_width(trial) > px[min(row, len(px) - 1)]:
                break
            lines[-2:] = [head, trial]
        paras.append(lines)
        row += 1
    return paras


def fit(entry, text):
    """The text with line breaks for families that wrap, untouched otherwise. An explicit {br} stays."""
    if not limit(entry).wrap:
        return text
    return "{br}".join(line for lines in wrapped(entry, text) for line in lines)


def stubs(entry, text):
    """Last lines under STUB characters that fit() could not fix, in paragraphs it wrapped."""
    if not limit(entry).wrap:
        return []
    return [lines[-1] for lines in wrapped(entry, text) if len(lines) > 1 and len(lines[-1]) < STUB]


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
    return problems + template_problems(entry, text)


def _selftest():
    page = {"id": "DEMO/TXT_PEN0:96", "jp": "あ", "len": 150}
    assert fit(page, "a b") == "a b"
    long = " ".join(["word"] * 28)
    assert fit(page, long).count("{br}") >= 1
    assert check(page, long) == []
    assert check(page, " ".join(["word"] * 200))
    widow = " ".join(["word"] * 16) + " it."  # greedy: "it." alone on line 2
    assert len(fit(page, widow).split("{br}")[-1]) >= STUB and stubs(page, widow) == []
    assert stubs(page, "m" * 60 + " it.") == ["it."]
    label = {"id": "PAW:0", "jp": "移動", "len": 8, "refs": ["PAW:w80000000"]}
    assert limit(label).px == [24]
    assert check(label, "Mo") == []
    assert check(label, "Move it now") != []


if __name__ == "__main__":
    _selftest()
    print("ok")
