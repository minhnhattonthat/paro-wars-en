"""The graphics-text table: page, rects, English, style. Drawn by tools/gfx.py. Wording follows glossary.md; where it came from is in docs/re/graphics.md."""
import struct
from pathlib import Path

TEXT, CHUNKY, SIGN, SMALL = "ArchivoNarrow-VF.ttf", "LuckiestGuy-Regular.ttf", "Anton-Regular.ttf", "en12"


class Style:
    """ink: an index or "auto" (sampled per row from the Japanese); edge: an index, "auto" or "none"; lead: blank rows between "|" lines."""

    def __init__(self, font, size=0, ink="auto", edge="auto", shadow=None, stroke=1, wide=1.0, lead=1, down=0):
        self.font, self.size, self.ink, self.edge, self.shadow, self.stroke, self.wide, self.lead, self.down = font, size, ink, edge, shadow, stroke, wide, lead, down


# Pages: (file, offset of the page's row 0 in the decoded file, bytes per row, bits per pixel)
SELECT = ("DATA/DEMO/KABE0.BIN", 0x8000, 128, 8)  # the select screens' atlas, VRAM 896,0
TITLE = Style(TEXT, 22, 0x35, 0x38, 0x39)
GOLD = Style(TEXT, 17, 0x55, 0x58)
PLAIN = Style(TEXT, 17, 0x35, 0x38, 0x39)
BAR = Style(TEXT, 17, 0xBB, "none")
ROW = "row"  # clear to the rect's first column, row by row: the button bar's gradient

LABELS = [
    (SELECT, [(0, 0, 32, 24)], "OK", BAR, "c", ROW),
    (SELECT, [(32, 0, 32, 24)], "Back", BAR, "c", ROW),
    (SELECT, [(0, 24, 48, 24)], "Help", BAR, "c", ROW),
    (SELECT, [(48, 24, 48, 24)], "Map", BAR, "c", ROW),
    (SELECT, [(0, 72, 64, 24)], "Mode", TITLE, "r", 0),
    (SELECT, [(64, 72, 64, 24)], "Level", TITLE, "r", 0),
    (SELECT, [(0, 96, 128, 24)], "Character", TITLE, "r", 0),
    (SELECT, [(0, 128, 64, 24)], "Map", TITLE, "r", 0),
    (SELECT, [(0, 48, 128, 24), (96, 24, 32, 24)], "Select", TITLE, "l", 0),
    (SELECT, [(0, 152, 128, 16)], "Change Map", PLAIN, "r", 0),
    (SELECT, [(0, 168, 112, 16)], "Status", PLAIN, "l", 0),
    (SELECT, [(0, 184, 48, 16)], "Level", GOLD, "c", 0),
    (SELECT, [(48, 184, 80, 16)], "Energy", GOLD, "c", 0),
    (SELECT, [(0, 200, 40, 16)], "Vision", GOLD, "c", 0),
    (SELECT, [(40, 200, 64, 16)], "Z.O.C.", GOLD, "c", 0),
    (SELECT, [(0, 216, 64, 16)], "Easy", PLAIN, "c", 0),
    (SELECT, [(64, 216, 32, 16)], "On", PLAIN, "c", 0),
    (SELECT, [(96, 216, 32, 16)], "Off", PLAIN, "c", 0),
    (SELECT, [(0, 232, 80, 16)], "Hard", PLAIN, "c", 0),
    (SELECT, [(80, 232, 48, 16), (104, 200, 24, 16)], "All clear", PLAIN, "c", 0),
]

# Next and previous page on the button bar: KABE0 and KABE1 both load it at VRAM 576,256.
for _rel in ("DATA/DEMO/KABE0.BIN", "DATA/DEMO/KABE1.BIN"):
    _page = (_rel, 0x24000, 128, 8)
    LABELS += [
        (_page, [(32, 168, 32, 24)], "Next", BAR, "c", ROW),
        (_page, [(64, 168, 32, 24)], "Prev", BAR, "c", ROW),
    ]

# Map status table: VRAM 0,256 (KABE2 row 128, KABE3 row 384): a column of 64x14 labels, then 8 nation names.
for _rel, _row in (("DATA/DEMO/KABE2.BIN", 128), ("DATA/DEMO/KABE3.BIN", 384)):
    _page = (_rel, _row * 128, 128, 8)
    _cell = Style(TEXT, 13, "auto", "none")
    _name = Style(TEXT, 13, 0x6F, "none")
    for _i, _t in enumerate(("Nation","Color", "Alliance", "Player", "Controller", "Money", "Science", "Energy", "Cities")):
        LABELS.append((_page, [(0, _i * 14, 64, 14)], _t, _cell, "c", ROW))
    for _i, _t in enumerate(("Factories", "Refineries", "Airports", "Ports")):
        LABELS.append((_page, [(64, _i * 14, 64, 14 + (_i == 3))], _t, _cell, "c", ROW))
    _page = (_rel, (_row - 128) * 128, 128, 8)  # their names sit at VRAM 0,384, the file's rows just before the labels' page
    for _x, _y, _t in ((0, 0, "Penta"), (56, 0, "Michael"), (0, 16, "Akashiya"), (56, 16, "Lovely"), (0, 32, "Koitsu&Aitsu"), (56, 32, "Moai"), (0, 48, "Panda"), (56, 48, "Bow-Wow")):
        LABELS.append((_page, [(_x, _y, 54, 12)], _t, _name, "c", ROW))

# Nation plates (DEMO/KABE4): 8 columns of 128 rows, the top 48 hold the name's two strips; a line is 24 tall. Widths: tools/debug/prims.py on plate_N.
_PLATE = Style(TEXT, 20)
_names = [
    ([(0, 0, 128, 24), (0, 24, 16, 24)], "Pentaro Kingdom"),
    ([(0, 0, 128, 24), (0, 24, 16, 24)], "Michael Empire"),
    ([(0, 0, 128, 24), (0, 24, 80, 24)], "Republic of Akashiya Land"),  # its last 32 px also end names 4 and 6, so they stay blank
    ([(0, 0, 128, 24), (0, 24, 88, 24)], "Lovely Federal States"),
    ([(0, 0, 128, 24), (0, 24, 128, 24)], "Koitsu & Aitsu Federal Republic"),
    ([(0, 0, 128, 24), (0, 24, 64, 24)], "Moai Islands Emirate"),
    ([(0, 0, 128, 24), (0, 24, 128, 24)], "Panda Tea Party Beasts' Republic"),
    ([(0, 0, 128, 24)], "Bow-Wow Nation"),
]
_columns = [("DATA/DEMO/KABE4.BIN", _n * 128 * 64, _n) for _n in range(8)]  # the same strips in the scenario files, 2-4 nations each (find_copies.py)
for _line in (Path(__file__).parent / "gfx_copies.tsv").read_text(encoding="utf-8").splitlines():
    _rel, _top, _n = _line.split("\t")
    _columns.append((_rel, int(_top, 16), int(_n)))
_tail = {0: "Military Data", 1: "Main Weapons", 7: "Nation Data"}
for _rel, _top, _n in _columns:
    _page = (_rel, _top, 64, 4)
    LABELS.append((_page, _names[_n][0], _names[_n][1], _PLATE, "c", 0))
    if _n == 2:
        LABELS.append((_page, [(80, 24, 32, 24)], "", _PLATE, "c", 0))
    if _n in _tail:
        LABELS.append((_page, [(0, 24, 96, 24) if _n == 7 else (16, 24, 112, 24)], _tail[_n], _PLATE, "c", 0))

# Place names on the story map (DEMO/WMAP0): 8bpp rows of 16, as wide as the Japanese's black field. The first 16 rows have the whole 128.
_PLACE = Style(TEXT, 15)
for _i, _t in enumerate(("Great Pen-Kuro Island", "Prince Kingdom", "Lovely Federal States", "Koitsu & Aitsu Fed. Rep.", "Pentaro Kingdom", "Bling-Bling H Island", "Chinkokoko-Kaan Kingdom",
                         "Fin-Fin Range Kingdom", "February 7th Island", "Nya Continent", "Bow-Wow Nation", "Gwait Region", "Ryuken Region", "Republic of Akashiya Land",
                         "Panda Beasts' Republic", "Michael Empire")):
    LABELS.append((("DATA/DEMO/WMAP0.BIN", 0, 128, 8), [(0, _i * 16, 128, 16)], _t, _PLACE, "l", 0))
for _y, _w, _t in ((272, 88, "Moai Islands Emirate"), (288, 96, "Lip Chaser Island"), (304, 104, "Francis-Pedro Island"), (320, 96, "John Nyanjiro's Land")):
    LABELS.append((("DATA/DEMO/WMAP0.BIN", 0, 128, 8), [(0, _y, _w, 16)], _t, _PLACE, "l", 0))

# Map HUD: country names in FIX.BIN, 4bpp, 16 rows apiece.
_FIX = ("DATA/FIX.BIN", 0xC000, 64, 4)
_hud = Style(TEXT, 14, ink=1, edge=8)
for _i, _t in enumerate(("Pentaro Kingdom", "Lovely States", "Koitsu & Aitsu", "Michael Empire", "Bow-Wow Nation", "Akashiya Republic", "Panda Republic", "Moai Emirate")):
    LABELS.append((_FIX, [(0, _i * 16, 88 if _i not in (5, 6, 7) else 112, 16)], _t, _hud, "l", 0))

# Mission title cards (DATA/MTIT): a 128x128 4bpp atlas, 8 palettes, then the card's sprites as data: count, {x, y, w, h, u, v}..., panel {x, y, w, h}.
# Each title gets one or two lines of two 128x24 strips; the furigana go.
_MTIT_TABLE = 8192 + 256
_CARD = Style(TEXT, 21)
PATCHES = {}  # file -> [(offset, bytes)], written after its labels
_cards = {
    1: ("Sleep Forever on", "Francis-Pedro Island!"),
    2: ("Howl on February 7th!", ""),
    3: ("The Gold of the North:", "I'll Be Takin' That!"),
    4: ("A Chomp from the Giant Empire", ""),
    5: ("The Worst Sea Battle Ever", ""),
    6: ("Whatever Else, Blow Up", "Fan-Fan Fortress!"),
    7: ("Friends or Not, It's War!", ""),
    8: ("Glory of the Octopus!", ""),
    9: ("Operation Big the Blitz", ""),
    10: ("That's All, Folks!", "The Legendary Last Battle"),
    11: ("Super Sing & Dance Sea Battle", ""),
    12: ("The Rairai Prefecture", "Funny Face Incident"),
}
_card_size = {1: 8564, 2: 8588, 3: 8588, 4: 8540, 5: 8516, 6: 8612, 7: 8588, 8: 8540, 9: 8540, 10: 8636, 11: 8564, 12: 8564}
for _n, (_a, _b) in _cards.items():
    _rel = f"DATA/MTIT/MTIT{_n}.BIN"
    _page = (_rel, 0, 64, 4)
    LABELS.append((_page, [(0, 0, 128, 24), (0, 24, 128, 24)], _a, _CARD, "c", 0))
    LABELS.append((_page, [(0, 48, 128, 24), (0, 72, 128, 24)], _b, _CARD, "c", 0))
    LABELS.append((_page, [(0, 96, 128, 32)], "", _CARD, "c", 0))
    _y1, _rows = (72, 2) if _b else (88, 1)
    _recs = [(32, _y1, 128, 24, 0, 0), (160, _y1, 128, 24, 0, 24)]
    _box = (16, 48, 288, 96) if _b else (16, 64, 288, 56)
    if _b:
        _recs += [(32, 112, 128, 24, 0, 48), (160, 112, 128, 24, 0, 72)]
    _table = struct.pack("<I", len(_recs)) + b"".join(struct.pack("<6I", *r) for r in _recs) + struct.pack("<4I", *_box)
    PATCHES[_rel] = [(_MTIT_TABLE, _table.ljust(_card_size[_n] - _MTIT_TABLE, b"\0"))]

# Win and lose banners: the same big word in every BTLEND file. The third sprite, "!!", is already fine.
_BIG = Style(CHUNKY, 108, "auto", "auto", stroke=2)
for _i in range(9):
    _rel = f"DATA/BTLEND/WIN{_i:02}.BIN"
    LABELS.append(((_rel, 0x200, 128, 8), [(0, 0, 128, 104), (0, 128, 128, 112)], "WIN", _BIG, "c", 0))
for _i in range(8):
    _rel = f"DATA/BTLEND/LOS{_i:02}.BIN"
    LABELS.append(((_rel, 0x200, 128, 8), [(0, 0, 128, 120), (0, 128, 128, 104, 16)], "LOSE", _BIG, "c", 0))
