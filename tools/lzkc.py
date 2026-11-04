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


def compress(data):
    """Greedy encoder over the same window. Output decodes to data; it need not equal Konami's bytes."""
    win = bytearray(WIN)
    pos = START
    out = bytearray()
    flag_at = None
    bit = 8
    flags = 0

    def emit(is_token, payload):
        nonlocal flag_at, bit, flags
        if bit == 8:
            if flag_at is not None:
                out[flag_at] = flags
            flag_at = len(out)
            out.append(0)
            bit, flags = 0, 0
        if is_token:
            flags |= 1 << bit
        bit += 1
        out.extend(payload)

    def push(b):
        nonlocal pos
        win[pos] = b
        pos = (pos + 1) & (WIN - 1)

    i, n = 0, len(data)
    # shortcut: hash chains would compress slightly faster; files are at most ~200 KB and this is a build step.
    index = {}
    while i < n:
        best_len, best_off = 0, 0
        key = data[i:i + 3]
        if len(key) == 3:
            for off in index.get(key, ())[-64:]:
                dist = (pos - off) & (WIN - 1)
                if dist < 3:
                    continue
                k = 0
                while k < 34 and i + k < n:
                    # past dist bytes the copy reads what it has just written, as the game's loop does
                    src = data[i + k - dist] if k >= dist else win[(off + k) & (WIN - 1)]
                    if src != data[i + k]:
                        break
                    k += 1
                if k > best_len:
                    best_len, best_off = k, off
        # the short form copies 2..5 bytes from up to 15 back, overlap allowed
        short_len, short_dist = 0, 0
        for dist in range(1, 16):
            k = 0
            while k < 5 and i + k < n:
                src = data[i + k - dist] if k >= dist else win[(pos - dist + k) & (WIN - 1)]
                if src != data[i + k]:
                    break
                k += 1
            if k > short_len:
                short_len, short_dist = k, dist
        if best_len >= 3 and best_len >= short_len:
            emit(True, bytes([((best_len - 3) << 2) | (best_off >> 8), best_off & 0xFF]))
            take = best_len
        elif short_len >= 2:
            emit(True, bytes([0x80 | ((short_len - 2) << 4) | short_dist]))
            take = short_len
        else:
            emit(False, data[i:i + 1])
            take = 1
        for b in data[i:i + take]:
            if i + 2 < n:
                index.setdefault(data[i:i + 3], []).append(pos)
            push(b)
            i += 1
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
