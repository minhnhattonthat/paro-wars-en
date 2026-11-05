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
    # x 0 is a clean column of the bar: "row" keeps a rect's two end columns, and the Japanese has ink there. 15 px because Back at 17 only fits squeezed, which fuses it.
    (SELECT, [(0, 0, 32, 24)], "OK", BAR, "c", (0, 0)),
    (SELECT, [(32, 0, 32, 24)], "Back", Style(TEXT, 15, 0xBB, "none"), "c", (0, 0)),
    (SELECT, [(0, 24, 48, 24)], "Help", BAR, "c", (0, 0)),
    (SELECT, [(48, 24, 48, 24)], "Map", BAR, "c", (0, 0)),
    (SELECT, [(0, 72, 64, 24)], "Mode", TITLE, "r", 0),
    (SELECT, [(64, 72, 64, 24)], "Level", TITLE, "r", 0),
    (SELECT, [(0, 96, 128, 24)], "Character", TITLE, "r", 0),
    (SELECT, [(0, 128, 64, 24)], "Map", TITLE, "r", 0),
    (SELECT, [(0, 48, 128, 24), (96, 24, 32, 24)], "Select", TITLE, "l", 0),
    (SELECT, [(0, 152, 128, 16)], "Change Map", Style(TEXT, 12, 0x35, 0x38, 0x39), "r", 0),  # one line on screen, so one size: at 17 only Status keeps it, having no descender
    (SELECT, [(0, 168, 112, 16)], "Status", Style(TEXT, 12, 0x35, 0x38, 0x39), "l", 0),
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

# Mode select's two big signs: VRAM 768,0 and 768,128. The select screen loads KABE0's copy; KABE3 holds the same rows.
_MODE = Style(CHUNKY, 48, "auto", "auto", stroke=2)
LABELS += [
    (("DATA/DEMO/KABE3.BIN", 0, 128, 8), [(0, 0, 128, 104)], "SCENARIO|MODE", _MODE, "c", 0),
    (("DATA/DEMO/KABE3.BIN", 0, 128, 8), [(0, 128, 128, 104)], "MAP BATTLE|MODE", _MODE, "c", 0),
    (("DATA/DEMO/KABE0.BIN", 0, 128, 8), [(0, 512, 128, 104)], "SCENARIO|MODE", _MODE, "c", 0),
    (("DATA/DEMO/KABE0.BIN", 0, 128, 8), [(0, 640, 128, 104)], "MAP BATTLE|MODE", _MODE, "c", 0),
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
    _cell = Style(TEXT, 13, 193, "none")  # the Japanese's commonest ink: sampled per row, thin glyphs like 色 gave a faint one
    _name = Style(TEXT, 13, 0x6F, "none")
    for _i, _t in enumerate(("Nation","Color", "Alliance", "Player", "Controller", "Money", "Science", "Energy", "Cities")):
        LABELS.append((_page, [(0, _i * 14, 64, 14)], _t, _cell, "c", ROW))
    for _i, _t in enumerate(("Factories", "Refineries", "Airports", "Ports")):
        # inside the frame, on x 66's clean rows: コンビナートの数 fills its cell, so "row" read ink for background and left dark lines
        LABELS.append((_page, [(66, _i * 14, 60, 14 + (_i == 3))], _t, _cell, "c", (66, 0)))
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


def _plate(page, n):
    out = [(page, _names[n][0], _names[n][1], _PLATE, "c", 0)]
    if n == 2:
        out.append((page, [(80, 24, 32, 24)], "", _PLATE, "c", 0))
    if n in _tail:
        out.append((page, [(0, 24, 96, 24) if n == 7 else (16, 24, 112, 24)], _tail[n], _PLATE, "c", 0))
    return out


for _rel, _top, _n in _columns:
    LABELS += _plate((_rel, _top, 64, 4), _n)

# DATA/FLAG.BIN: palette, then nine LZ streams back to back, one 128 x 128 column each: the nation's name strips over its flag. The banner when a turn starts (gfx.py rewrites the streams).
# The banner shows the name only, so the tails go blank: Bow-Wow's stream doesn't fit its slot otherwise.
FLAG = "DATA/FLAG.BIN"
_FP = (FLAG, 0, 64, 4)
FLAG_STREAMS = [_plate(_FP, _n)[:1] + ([(_FP, [(80, 24, 32, 24)], "", _PLATE, "c", 0)] if _n == 2 else [(_FP, [(0, 24, 96, 24) if _n == 7 else (16, 24, 112, 24)], "", _PLATE, "c", 0)] if _n in _tail else []) for _n in range(8)]
FLAG_STREAMS.append([(_FP, [(0, 0, 128, 24)], "Nya Empire", _PLATE, "c", 0)])
# Panda's banner ends in the last 80 px of Akashiya's strip 2 (共和国 in both), so that cell has to read Republic in each.
FLAG_STREAMS[2] = [(_FP, [(0, 0, 124, 24)], "Akashiya", _PLATE, "r", 0), (_FP, [(124, 0, 4, 24)], "", _PLATE, "c", 0), (_FP, [(0, 24, 36, 24)], "Land", Style(TEXT, 20, down=-2), "r", 0),  # down: no descender, so centring drops it below its neighbours' baseline
 (_FP, [(36, 24, 76, 24)], "Republic", _PLATE, "r", 0)]  # r: Panda's sprite starts near x 36 and cuts anything left of it
FLAG_STREAMS[6] = [(_FP, [(0, 0, 112, 24)], "Panda Beasts'", _PLATE, "r", 0), (_FP, [(112, 0, 16, 24), (0, 24, 128, 24)], "", _PLATE, "c", 0)]  # 112: the tail sprite overlaps this strip's end

# Place names on the story map (DEMO/WMAP0): 8bpp rows of 16. The game places a name so that the Japanese's field just fits the map, so English keeps to that width (past it the map's edge cuts it).
# The game's own pixel font in the brightest grey of the Japanese's ramp: no edge, since the game shades the field. Outline fonts closed every e at this size, so long names take a short form that fits (mask refuses one that doesn't).
_PLACE = Style(SMALL, ink=0xE1, edge="none")
for _i, (_w, _t) in enumerate(((104, "Great Pen-Kuro Isle"), (64, "Prince Realm"), (96, "Lovely States"), (128, "Koitsu & Aitsu Fed. Rep."), (64, "Pentaro"), (80, "Bling-Bling H Isle"),
                               (104, "Chinkoko-Kaan Realm"), (104, "Fin-Fin Range Realm"), (56, "Feb. 7 Isle"), (56, "Nya Land"), (56, "Bow-Wow"), (72, "Gwait Region"), (48, "Ryuken"),
                               (104, "Akashiya Republic"), (128, "Panda Beasts' Republic"), (64, "Michael Emp."), (40, "Hawaii"), (88, "Moai Emirate"), (96, "Lip Chaser Island"),
                               (104, "Francis-Pedro Island"), (96, "Nyanjiro's Land"))):
    LABELS.append((("DATA/DEMO/WMAP0.BIN", 0, 128, 8), [(0, _i * 16, _w, 16)], _t, _PLACE, "l", 0))

# Map HUD: country names in FIX.BIN, 4bpp, 16 rows apiece.
_FIX = ("DATA/FIX.BIN", 0xC000, 64, 4)
_hud = Style(TEXT, 14, ink=1, edge=8)
# A rect is the Japanese's whole width: the game shows that many pixels (Bow-Wow's 70 cut "Nation"), and whatever isn't cleared stays on screen.
for _i, (_t, _w) in enumerate((("Pentaro Kingdom", 88), ("Lovely States", 98), ("Koitsu & Aitsu", 111), ("Michael Empire", 88), ("Bow-Wow", 70), ("Akashiya Republic", 112), ("Panda Republic", 112), ("Moai Emirate", 112))):
    LABELS.append((_FIX, [(0, _i * 16, _w, 16)], _t, _hud, "l", 0))
LABELS.append((_FIX, [(88, 0, 40, 16), (88, 48, 40, 16)], "Nyanjiro Army", _hud, "l", 0))  # ニャン次郎軍, split across two rows of the atlas

# A saved game's row on the memory card screen (MCWGRPH, VRAM 928,0): nation, 第 N 章, ターン, クリア, mode.
_SAVE = ("DATA/MCWGRPH.BIN", 0xC000, 64, 4)
_row = Style(SMALL)  # the game's pixel font: outline fonts close the t and e once the game's edge goes round them
for _y, _h, _t in ((0, 20, "Pentaro Realm"), (20, 20, "Michael Empire"), (40, 20, "Akashiya Land"), (60, 20, "Lovely States"), (80, 20, "Koitsu & Aitsu"), (100, 20, "Moai Emirate"), (128, 19, "Panda Republic"), (147, 20, "Bow-Wow")):
    LABELS.append((_SAVE, [(0, _y, 80, _h)], _t, _row, "c", 0))
for _x, _y, _w, _t in ((80, 0, 32, "Clear"), (80, 20, 32, "Turn"), (80, 40, 12, "Ch"), (92, 40, 12, ""), (80, 60, 32, "Map")):
    LABELS.append((_SAVE, [(_x, _y, _w, 20)], _t, Style(SMALL, ink=3, edge="none") if _t == "Ch" else _row, "c", 0))
LABELS.append((_SAVE, [(0, 168, 56, 16)], "Scenario", _row, "c", 0))
LABELS.append((_SAVE, [(0, 184, 56, 16)], "Map Battle", _row, "c", 0))

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

# Signs painted on the story backdrops: the art stays, the inks go (DEMO/TXT_AIT4 and BUT2's chess match, MOA2's contest).
_CLOTH = Style(CHUNKY, 22, 106, 70, lead=3)
_BUBBLE = Style(TEXT, 15)
_TEASIGN = Style(SMALL, ink=0x1E, edge="none")
LABELS += [
    (("DATA/DEMO/BACK10A.BIN", 0, 128, 8), [(68, 40, 60, 56), (0, 168, 124, 56)], "Pound for Pound|in Chess", _CLOTH, "c", ("clean", 50, 64, 40, 56)),  # the cloth's shading stays: only the Japanese's inks go
    (("DATA/DEMO/BACK11A.BIN", 0, 128, 8), [(64, 40, 64, 56), (0, 168, 124, 56)], "Paro World|Super Sing & Dance|Contest", _CLOTH, "c", ("clean", 50, 64, 40, 56)),
    (("DATA/DEMO/BACK13A.BIN", 0, 128, 8), [(14, 166, 36, 12)], "Teaism", _TEASIGN, "c", 1),  # 茶会主義 in its 36 px field, and the same sign when the view pans (BACK13B)
    (("DATA/DEMO/BACK13B.BIN", 0, 128, 8), [(78, 38, 36, 12)], "Teaism", _TEASIGN, "c", 1),
    (("DATA/DEMO/BACK3.BIN", 0, 128, 8), [(44, 284, 20, 10)], "Peace", Style(TEXT + "#Regular", 9, 2, "none"), "l", 6),  # 平和, the plaque in Bow-Wow's office; the screen's edge cuts its last 2 px
    (("DATA/DEMO/PEN4_01.BIN", 0, 128, 8), [(38, 135, 84, 34)], "Lite-Salt FC|(On Patrol)", _BUBBLE, "c", 0),
    (("DATA/DEMO/PEN4_01.BIN", 0, 128, 8), [(18, 179, 102, 34)], "Luxury Liner|Paro Nyanko", _BUBBLE, "c", 0),
]

# Win and lose banners: the same big word in every BTLEND file. The third sprite, "!!", is already fine.
_BIG = Style(CHUNKY, 108, "auto", "auto", stroke=2)
for _i in range(9):
    _rel = f"DATA/BTLEND/WIN{_i:02}.BIN"
    LABELS.append(((_rel, 0x200, 128, 8), [(0, 0, 128, 104), (0, 128, 128, 112)], "WIN", _BIG, "c", 0))
for _i in range(8):
    _rel = f"DATA/BTLEND/LOS{_i:02}.BIN"
    LABELS.append(((_rel, 0x200, 128, 8), [(0, 0, 128, 120), (0, 128, 128, 104, 16)], "LOSE", _BIG, "c", 0))
    LABELS.append(((_rel, 0x200, 128, 8), [(0, 286, 6, 58)], "", _BIG, "c", 0))  # the end of つ, on the !! sprite's left edge
