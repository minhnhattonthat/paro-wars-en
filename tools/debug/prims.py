"""List the textured primitives of a frame from a RAM dump: prims.py SCENE.ram.bin [--min-w N] [--tpage X,Y]. Walks every GPU ordering list it can find in RAM and prints the longest one.

One row per primitive: screen x,y,w,h, then the VRAM rect it samples (page x,y in halfwords, u,v,w,h in pixels at its depth), depth, clut x,y. That is how a label on a screen maps to file pixels."""
import argparse
import struct
import sys


def walk(ram, start):
    """Offsets of the packets of the chain at start, until it leaves RAM or ends."""
    out, at, seen = [], start, set()
    while at not in seen and 0 <= at <= len(ram) - 4:
        seen.add(at)
        tag = struct.unpack_from("<I", ram, at)[0]
        n, nxt = tag >> 24, tag & 0xFFFFFF
        if n:
            out.append((at, n))
        if nxt == 0xFFFFFF:
            return out, True
        if nxt >= len(ram) or nxt & 3:
            return out, False
        at = nxt
    return out, False


def chains(ram):
    """Heads of chains: words naming the next packet, not pointed at by anything else. Longest first."""
    words = struct.unpack(f"<{len(ram) // 4}I", ram[:len(ram) // 4 * 4])
    next_of = {}
    for i, w in enumerate(words):
        n, nxt = w >> 24, w & 0xFFFFFF
        if n <= 16 and nxt < len(ram) and not nxt & 3 and nxt != i * 4:
            next_of[i * 4] = nxt
    ends = [a for a, w in enumerate(words) if w & 0xFFFFFF == 0xFFFFFF and w >> 24 <= 16]
    prev = {}
    for a, b in next_of.items():
        prev.setdefault(b, []).append(a)
    best = []
    for end in ends:  # breadth first back from the end: the deepest node heads the longest chain
        level, depth, seen = [end * 4], 0, {end * 4}
        while True:
            more = [p for a in level for p in prev.get(a, ()) if p not in seen]
            if not more:
                break
            seen.update(more)
            level, depth = more, depth + 1
        best.append((depth, level[0]))
    return [a for _, a in sorted(best, reverse=True)]


def decode(ram, at, n):
    """A textured primitive at a packet, or None."""
    w = struct.unpack_from(f"<{n}I", ram, at + 4)
    code = w[0] >> 24
    if 0x64 <= code <= 0x7F and n >= 3:  # rectangle; size in its fourth word or fixed
        x, y = w[1] & 0xFFFF, w[1] >> 16
        u, v, clut = w[2] & 0xFF, w[2] >> 8 & 0xFF, w[2] >> 16
        size = (code >> 3) & 3
        rw, rh = (w[3] & 0xFFFF, w[3] >> 16) if size == 0 else ({1: 1, 2: 8, 3: 16}[size],) * 2
        return dict(kind="sprt", x=x, y=y, w=rw, h=rh, u=u, v=v, uw=rw, vh=rh, clut=clut, tpage=None)
    if code in (0x24, 0x25, 0x26, 0x27) and n >= 7:  # textured triangle
        return None
    if code in (0x2C, 0x2D, 0x2E, 0x2F) and n >= 9:  # textured quad
        xs = [w[i] & 0xFFFF for i in (1, 3, 5, 7)]
        ys = [w[i] >> 16 for i in (1, 3, 5, 7)]
        us = [w[i] & 0xFF for i in (2, 4, 6, 8)]
        vs = [w[i] >> 8 & 0xFF for i in (2, 4, 6, 8)]
        xs = [x - 0x10000 if x & 0x8000 else x for x in xs]
        ys = [y - 0x10000 if y & 0x8000 else y for y in ys]
        return dict(kind="quad", x=min(xs), y=min(ys), w=max(xs) - min(xs), h=max(ys) - min(ys), u=min(us), v=min(vs), uw=max(us) - min(us), vh=max(vs) - min(vs),
                    clut=w[2] >> 16, tpage=w[4] >> 16)
    return None


def page(tp):
    return (tp & 15) * 64, (tp >> 4 & 1) * 256, {0: 4, 1: 8, 2: 16}.get(tp >> 7 & 3, 16)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ram")
    ap.add_argument("--min-w", type=int, default=0)
    ap.add_argument("--tpage")
    a = ap.parse_args()
    ram = open(a.ram, "rb").read()
    heads = chains(ram)
    if not heads:
        sys.exit("no ordering list found")
    packets = sorted({p for h in heads[:200] for p in walk(ram, h)[0]})  # the game draws several lists a frame: map, then UI
    rows = []
    tpage = 0
    for at, n in packets:
        if at + 4 + n * 4 > len(ram):
            continue
        for i in range(n):  # tpage set by a mode word in the same or an earlier packet
            word = struct.unpack_from("<I", ram, at + 4 + i * 4)[0]
            if word >> 24 == 0xE1:
                tpage = word & 0xFFFF
        p = decode(ram, at, n)
        if p and p["w"] >= a.min_w:
            tp = p["tpage"] if p["tpage"] is not None else tpage
            px, py, depth = page(tp)
            clut = p["clut"]
            rows.append((p["kind"], p["x"], p["y"], p["w"], p["h"], px, py, p["u"], p["v"], p["uw"], p["vh"], depth, (clut & 63) * 16, clut >> 6))
    print(f"{len(packets)} packets, {len(rows)} textured")
    print("kind x y w h | page_x page_y u v uw vh | bpp clut_x clut_y")
    seen = set()
    for r in rows:
        if r in seen:
            continue
        seen.add(r)
        if a.tpage and tuple(map(int, a.tpage.split(","))) != (r[5], r[6]):
            continue
        print(*r[:5], "|", *r[5:11], "|", *r[11:])


if __name__ == "__main__":
    main()
