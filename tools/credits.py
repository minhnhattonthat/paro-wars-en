"""The staff roll (docs/re/graphics.md row 12): DATA/ENDING/STAFF.BIN is a 4bpp glyph sheet, the 16 SEQ_* files hold its layout as sprite lists.

A list is a chain of 24-byte nodes {x, y, u, v, w, h, page, tpage, 1, 0, next}, drawn together at an object's place. The sheet's 384 rows of 64 bytes are three 128x128 columns in VRAM,
reached as page 9 u 0-127, page 9 u 128-255 and page 10 u 0-127, all at v 128-255. English: one strip per line in a new sheet, one node per line, in the game's own font.
credits.py dump: every line as the files have it. Readings of names not checked against a source are listed in docs/tl-notes.md."""
import struct
import sys
from pathlib import Path

import en_text

ROOT = Path(__file__).resolve().parents[1]
STAFF = "DATA/ENDING/STAFF.BIN"
SEQ = [f"DATA/ENDING/SEQ_{c}{k}.BIN" for c in ("PEN", "BUT", "TAK", "LOV", "KOI", "MOA", "PAN", "BAU") for k in "ET"]
BASE = 0x801C0000
TPAGE = 0x16

_COL0 = ["企画山形茶王小玉", "紀年池田修圭一戦", "闘若狭祥吾加藤賢", "郎佐右伊徳夢之介", "剛輝久上戸康輔鈴", "木陽子技真理積細", "師工学家村井聖夜", "収録坂登音声編集"]
_COL1 = ["作曲太知巳添制由", "千丸出演白石冬美", "花島津冴松本梨香", "淑生月中真奈永千", "葉繁恵次勇栗林苅", "部明原昌亮三宅今", "泉健米岡正色浩阪"]
_COL2 = ["みむがぬりえのあ", "かねひるい", "デレクターメイン", "プログラムモエビ", "ジアルザニフチサ", "ウドヘミカコスケ", "ベリバダトシゴパ"]
_SMALL = "ィョャュッ/()・"  # 8 px cells on row 240 of column 2

LINES = {
    "企画": "Planning",
    "ディレクター": "Director",
    "メインプログラム": "Main Program",
    "戦闘プログラム": "Battle Program",
    "デモプログラム": "Demo Program",
    "エンディングプログラム": "Ending Program",
    "ビジュアルデザイン": "Visual Design",
    "アニメーター": "Animator",
    "グラフィックデザイン": "Graphic Design",
    "ぬりえ技師": "Coloring Technician",
    "積み木工学家": "Building Block Engineer",
    "ロゴデザイン": "Logo Design",
    "パッケージデザイン": "Package Design",
    "サウンドディレクター": "Sound Director",
    "音声収録ディレクター": "Voice Recording Director",
    "音声編集": "Voice Editing",
    "作曲": "Music",
    "音色制作": "Tone Design",
    "サウンドプログラム": "Sound Program",
    "声の出演": "Voice Cast",
    "ヘン太郎": "Pentaro",
    "花子": "Hanako",
    "ミカエル": "Michael",
    "タコスケ": "Takosuke",
    "ベリアル": "Belial",
    "ひかる": "Hikaru",
    "あかね": "Akane",
    "モアイ/バウバウ": "Moai / Bow-Wow",
    "パンダ": "Panda",
    "ジョンニャン次郎": "John Nyanjiro",
    "ニャニャ美": "Nyanyami",
    "スヘシャルサンクス": "Special Thanks",
    "プロデューサー": "Producer",
    "山形茶王(小玉紀年)": "Chao Yamagata (Noritoshi Kodama)",
    "池田修": "Osamu Ikeda",
    "池田圭一": "Keiichi Ikeda",
    "若狭祥吾": "Shogo Wakasa",
    "加トケン": "Kato-Ken",
    "佐藤右伊": "Ui Sato",
    "徳田夢之介": "Yumenosuke Tokuda",
    "剛輝久": "Teruhisa Go",
    "ミチコ": "Michiko",
    "むかい山": "Mukaiyama",
    "上戸康輔": "Kosuke Kamito",
    "鈴木陽子": "Yoko Suzuki",
    "小山真理子": "Mariko Koyama",
    "苅部明恵": "Akie Karibe",
    "村井聖夜": "Seiya Murai",
    "阪上登": "Noboru Sakagami",
    "太田知巳": "Tomomi Ota",
    "添田浩介": "Kosuke Soeda",
    "由井千丸": "Chimaru Yui",
    "白石冬美": "Fuyumi Shiraishi",
    "島津冴子": "Saeko Shimazu",
    "松本梨香": "Rika Matsumoto",
    "藤田淑子": "Toshiko Fujita",
    "生月真美": "Mami Ikutsuki",
    "永島由子": "Yuko Nagashima",
    "中山真奈美": "Manami Nakayama",
    "千葉繁": "Shigeru Chiba",
    "戸田恵子": "Keiko Toda",
    "田の中勇": "Isamu Tanonaka",
    "栗林みえ": "Mie Kuribayashi",
    "原田昌亮": "Shosuke Harada",
    "ジョン・三宅・ニャン次郎": "John Miyake Nyanjiro",
    "今泉健一郎": "Kenichiro Imaizumi",
    "米岡正紀": "Masanori Yoneoka",
}


def _cells(u, v, w, page):
    """The Japanese a strip shows. A width of 15 or 63 is the sheet's way of keeping off the next cell."""
    if v == 240 and page == 10:
        return "".join(_SMALL[(u + c) // 8] for c in range(0, w, 8))
    sheet = _COL2 if page == 10 else _COL0 if u < 128 else _COL1
    return "".join(sheet[(v - 128) // 16][(u % 128 + c) // 16] for c in range(0, w + 1 & ~15, 16))


def nodes(d):
    """Offset -> (x, y, u, v, w, h, page, next offset or None)."""
    out = {}
    for at in range(0, len(d) - 24, 4):
        x, y, u, v, w, h, page, hi, tp, one, z, nxt = struct.unpack_from("<hhBBBBBBHIII", d, at)
        if tp == TPAGE and 0 < h <= 16 and hi == 1 and one == 1 and z == 0 and page in (9, 10) and v >= 128 and (nxt == 0 or BASE <= nxt < BASE + len(d)):
            out[at] = (x, y, u, v, w, h, page, nxt - BASE if nxt else None)
    return out


def chains(d):
    """Lists: head offset -> node offsets in chain order. A list's head is the one no node points at; every pointer into the nodes from elsewhere must name a head."""
    n = nodes(d)
    pointed = {v[7] for v in n.values() if v[7] is not None}
    out = {}
    for head in n:
        if head not in pointed:
            at, chain = head, []
            while at in n:
                chain.append(at)
                at = n[at][7]
            out[head] = chain
    return n, out


def lines_of(n, chain):
    """Base y (small kana sit 1-2 px lower) -> (x, Japanese) of each line in a list."""
    rows = {}
    for at in chain:
        x, y, u, v, w, h, page, _ = n[at]
        rows.setdefault(y - y % 10, []).append((x, _cells(u, v, w, page)))
    return {y: (min(s[0] for s in strips), "".join(t for _, t in sorted(strips))) for y, strips in sorted(rows.items())}


def _rows(text):
    """The game's font as rows of 0/1, one blank column between letters; every row kept, so all lines share a baseline."""
    rows = [[] for _ in range(ROW_H)]
    for ch in text:
        glyph = en_text.FONT[ord(ch)]
        w = len(glyph[0])
        for y in range(ROW_H):
            rows[y] += [c == "#" for c in glyph[y]] + [False] if y < len(glyph) else [False] * (w + 1)
    return [r[:-1] for r in rows]


ROW_H = 10  # the font's rows: a shadow row as in the Japanese would cost 17 lines of room, and the sky is dark enough without


def layout():
    """English line -> (page, u, v, w): shelves across the sheet's columns. Page 9's two columns are side by side in VRAM, so a line may run across them."""
    widths = sorted({t: len(_rows(t)[0]) for t in set(LINES.values())}.items(), key=lambda kv: (-kv[1], kv[0]))  # text breaks ties: set order changes per process, and the build must be reproducible
    shelves = []  # [page, column, v, used]
    for col, page, room in ((0, 9, 255), (2, 10, 128)):  # 255: the game stores u + w in a byte, and 256 draws the strip backwards
        for r in range(128 // ROW_H):
            shelves.append([page, col, 128 + r * ROW_H, 0, room])
    out = {}
    for text, w in widths:
        for s in shelves:
            if s[3] + w <= s[4]:
                out[text] = (s[0], s[3], s[2], w)
                s[3] += w
                break
        else:
            raise ValueError(f"staff sheet full at {text!r}")
    return out


def sheet():
    """The new STAFF.BIN: index 1 is the Japanese sheet's ink."""
    out = bytearray(24576)
    for text, (page, u, v, w) in layout().items():
        for y, r in enumerate(_rows(text)):
            for x, on in enumerate(r):
                if on:
                    col = 2 if page == 10 else (u + x) // 128
                    a = (col * 128 + v - 128 + y) * 64 + ((u + x) % 128) // 2
                    out[a] |= 1 << 4 if (u + x) & 1 else 1
    return bytes(out)


def patch(d):
    """A SEQ file with each list rewritten to one node per line. Nodes shared between lists (the Japanese reused プログラム) are left out of the new chains."""
    d = bytearray(d)
    n, ch = chains(bytes(d))
    use = {}
    for chain in ch.values():
        for at in chain:
            use[at] = use.get(at, 0) + 1
    where = layout()
    for head, chain in ch.items():
        rows = lines_of(n, chain)
        own = [at for at in chain if use[at] == 1]
        if len(own) < len(rows):
            raise ValueError(f"list {head:#x}: {len(rows)} lines, {len(own)} nodes of its own")
        carriers = own[:len(rows)]
        for i, (y, (x, jp)) in enumerate(rows.items()):
            page, u, v, w = where[LINES[jp]]
            nxt = BASE + carriers[i + 1] if i + 1 < len(carriers) else 0
            struct.pack_into("<hhBBBBBBHIII", d, carriers[i], x, y, u, v, w, ROW_H, page, 1, TPAGE, 1, 0, nxt)
    return bytes(d)


def spans(rel, d):
    if rel == STAFF:
        return [(0, 24576)]
    return [(at, at + 24) for at in nodes(d)]


def main():
    seen = set()
    for rel in SEQ:
        d = (ROOT / "work/disc/tree" / rel).read_bytes()
        n, ch = chains(d)
        print(rel, len(n), "nodes", len(ch), "lists")
        for head, chain in ch.items():
            rows = lines_of(n, chain)
            seen |= {t for _, t in rows.values()}
            if len(sys.argv) > 2:
                print(hex(head), rows)
        chained = {v[7] for v in n.values()}
        words = struct.unpack(f"<{len(d) // 4}I", d[:len(d) // 4 * 4])
        odd = {w - BASE for i, w in enumerate(words) if w - BASE in n and w - BASE in chained and i * 4 - 20 not in n}
        if odd:
            print("  pointers into a list's middle:", sorted(map(hex, odd)))
    print("no English for", seen - set(LINES), "; unused", set(LINES) - seen)
    wide = layout()
    print(len(LINES), "lines,", len(wide), "strips; widest", max(w for *_, w in wide.values()), "px")


if __name__ == "__main__":
    if sys.argv[1:2] != ["dump"]:
        sys.exit(__doc__)
    main()
