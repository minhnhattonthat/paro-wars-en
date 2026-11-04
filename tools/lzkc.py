"""Paro Wars LZ codec, reimplemented from PAW.EXE 0x80013CB0 (docs/re/compression.md).

Header: u24 LE stream length, 1 unused byte (the stream starts at +4; the file may be sector-padded past it).
Window: 1024 bytes of zeros, write position starts at 0x3DE. Flag byte read LSB first; bit 0 = literal byte, bit 1 = token:
  t < 0x80:  2-byte token, copy (t>>2)+3 bytes from absolute window offset ((t&3)<<8)|next
  t < 0xC0:  copy ((t>>4)&3)+2 bytes from window position minus (t&0xF)
  else:      (t&0x3F)+8 literal bytes follow
usage: lzkc.py test FILE...                      decompress, recompress, decompress again; assert equal
       lzkc.py unpack FILE OUT
"""
import sys

WIN = 0x400
START = 0x3DE


def header_ok(d):
    """Could this file be LZ data? Its stream length must fit in the file and fill all but its last sector or so."""
    if len(d) < 8:
        return False
    n = d[0] | d[1] << 8 | d[2] << 16
    return 4 <= n <= len(d) - 4 and d[3] == 0 and len(d) - (n + 4) < 0x10000


def decompress(d, strict=False):
    """Return the output bytes. strict: raise on an overrun token, the same place the game's bounds check bails out."""
    n = d[0] | d[1] << 8 | d[2] << 16
    i, end = 4, 4 + n
    win = bytearray(WIN)
    pos = START
    out = bytearray()
    flags = 0

    def lit(b):
        nonlocal pos
        out.append(b)
        win[pos] = b
        pos = (pos + 1) & (WIN - 1)

    while True:
        flags >>= 1
        if not flags & 0x100:
            if i >= end:
                break
            flags = d[i] | 0xFF00
            i += 1
        if not flags & 1:
            if i >= end:
                break
            lit(d[i])
            i += 1
            continue
        if i >= end:
            break
        t = d[i]
        i += 1
        if t < 0x80:
            if i >= end:
                if strict:
                    raise ValueError("token past end")
                break
            off = (t & 3) << 8 | d[i]
            i += 1
            for k in range((t >> 2) + 3):
                lit(win[(off + k) & (WIN - 1)])
        elif t < 0xC0:
            dist = t & 0xF
            for _ in range((t >> 4 & 3) + 2):
                lit(win[(pos - dist) & (WIN - 1)])
        else:
            for _ in range((t & 0x3F) + 8):
                if i >= end:
                    if strict:
                        raise ValueError("literal run past end")
                    break
                lit(d[i])
                i += 1
    return bytes(out)


def _matches(data):
    """For each position: (long length, its window offset), (short length, its distance). The window only ever holds past output, so these don't depend on the parse."""
    n = len(data)
    longs, shorts = [(0, 0)] * n, [(0, 0)] * n
    index = {}
    for i in range(n):
        key = data[i:i + 3]
        best, best_dist = 0, 0
        if len(key) == 3:
            chain = index.setdefault(key, [])
            for j in reversed(chain[-128:]):
                dist = i - j
                if dist >= WIN:  # older entries have been overwritten
                    break
                k = 3
                while k < 34 and i + k < n and data[j + k] == data[i + k]:  # j + k may pass i: the game's copy reads what it just wrote
                    k += 1
                if k > best:
                    best, best_dist = k, dist
                    if k == 34:
                        break
            chain.append(i)
        longs[i] = (best, (START + i - best_dist) & (WIN - 1))
        best = dist_short = 0
        for dist in range(1, min(15, i) + 1):
            k = 0
            while k < 5 and i + k < n and data[i + k - dist] == data[i + k]:
                k += 1
            if k > best:
                best, dist_short = k, dist
        shorts[i] = (best, dist_short)
    return longs, shorts


def compress(data):
    """Optimal parse over the window, by bits (a flag bit per op). Output decodes to data; it need not equal Konami's bytes."""
    n = len(data)
    longs, shorts = _matches(data)
    cost = [1 << 60] * (n + 1)
    cost[0] = 0
    via = [None] * (n + 1)
    for i in range(n):
        c = cost[i]
        ops = [(i + 1, c + 9, ("lit",))]
        length, off = longs[i]
        for k in range(3, length + 1):
            ops.append((i + k, c + 17, ("long", k, off)))
        length, dist = shorts[i]
        for k in range(2, length + 1):
            ops.append((i + k, c + 9, ("short", k, dist)))
        for k in (10, 16, 24, 40, 71):  # a literal run pays off from 10 bytes
            if i + k <= n:
                ops.append((i + k, c + 9 + 8 * k, ("run", k)))
        for j, nc, op in ops:
            if nc < cost[j]:
                cost[j], via[j] = nc, (i, op)
    parse = []
    i = n
    while i:
        i, op = via[i]
        parse.append((i, op))
    out = bytearray()
    flag_at = None
    bit = 8
    flags = 0
    for i, op in reversed(parse):
        if bit == 8:
            if flag_at is not None:
                out[flag_at] = flags
            flag_at = len(out)
            out.append(0)
            bit, flags = 0, 0
        if op[0] != "lit":
            flags |= 1 << bit
        bit += 1
        if op[0] == "lit":
            out.append(data[i])
        elif op[0] == "long":
            out += bytes([((op[1] - 3) << 2) | (op[2] >> 8), op[2] & 0xFF])
        elif op[0] == "short":
            out.append(0x80 | ((op[1] - 2) << 4) | op[2])
        else:
            out.append(0xC0 | (op[1] - 8))
            out += data[i:i + op[1]]
    if flag_at is not None:
        out[flag_at] = flags
    return len(out).to_bytes(3, "little") + b"\0" + bytes(out)


def _selftest():
    samples = [b"", b"a", b"abcabcabcabcabc" * 40, bytes(range(256)) * 12, b"\0" * 5000, bytes(i * 7 & 0xFF for i in range(3000))]
    for s in samples:
        assert decompress(compress(s), strict=True) == s, s[:16]


if __name__ == "__main__":
    _selftest()
    if sys.argv[1] == "test":
        for path in sys.argv[2:]:
            raw = open(path, "rb").read()
            d = decompress(raw)
            assert decompress(compress(d), strict=True) == d, path
            print("ok", path, len(raw), "->", len(d))
    elif sys.argv[1] == "unpack":
        open(sys.argv[3], "wb").write(decompress(open(sys.argv[2], "rb").read()))
    else:
        sys.exit(__doc__)
