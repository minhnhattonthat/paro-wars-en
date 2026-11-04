"""Strings too long for their slot move into the freed kanji cells of PAW.EXE's font (docs/re/font.md), and every reference to them follows.

Refs are the extractor's: NAME:wADDR an aligned word, NAME:ADDR a lui with its first low half (extract.code_refs).
A lui whose register feeds a second low half can't move on its own, so that entry refuses to move: shorten it or patch the code."""
import struct

import en_text

PAW_BASE = 0x80010010 - 0x800
POOL_START = en_text.FONT_FILE + 492 * en_text.CELL  # 亜, the first kanji
POOL_END = en_text.FONT_FILE + 3490 * en_text.CELL
SEARCH = 8  # same window as extract.code_refs
AFTER = 16  # how far a second use of the lui's register is looked for


def pair_low(words, i):
    """Index of the low half belonging to the lui at i, as extract.code_refs finds it."""
    reg = words[i] >> 16 & 31
    for j in range(i + 1, min(len(words), i + SEARCH + 1)):
        x = words[j]
        if x >> 26 in (0, 0x0F) or x >> 21 & 31 != reg:
            continue
        return j
    return None


def resolves(hi_word, lo_word):
    return ((hi_word & 0xFFFF) << 16) + (lo_word & 0xFFFF) - (0x10000 if lo_word & 0x8000 else 0) & 0xFFFFFFFF


def lui_shared(words, i, low):
    """True if the lui's register is read again as a base after its low half, before anything overwrites it."""
    reg = words[i] >> 16 & 31
    x = words[low]
    # A low half written to the same register consumes the lui: addiu reg,reg,low or lw reg,low(reg).
    if x >> 26 < 0x28 and x >> 16 & 31 == reg:
        return False
    for j in range(low + 1, min(len(words), low + AFTER + 1)):
        x = words[j]
        op = x >> 26
        if op == 0x0F and x >> 16 & 31 == reg:
            return False
        if op and x >> 21 & 31 == reg:
            return True
    return False


def patch_ref(image, base, ref, old, new, entry_id):
    """Point one reference at new. image is the whole file, base its RAM address at offset 0."""
    word = ref.startswith("w")
    addr = int(ref[1:] if word else ref, 16)
    off = addr - base
    if off < 0 or off + 4 > len(image):
        raise ValueError(f"{entry_id}: ref {ref} outside its file")
    if word:
        if struct.unpack_from("<I", image, off)[0] != old:
            raise ValueError(f"{entry_id}: word at {ref} isn't {old:08x}")
        struct.pack_into("<I", image, off, new)
        return
    start = off % 4
    words = list(struct.unpack_from(f"<{(len(image) - start) // 4}I", image, start))
    i = (off - start) // 4
    low = pair_low(words, i)
    if low is None or resolves(words[i], words[low]) != old:
        raise ValueError(f"{entry_id}: code at {ref} doesn't resolve to {old:08x}")
    if lui_shared(words, i, low):
        raise ValueError(f"{entry_id}: lui at {ref} is shared; shorten the text or patch the code by hand")
    hi = (new + 0x8000) >> 16 & 0xFFFF
    struct.pack_into("<I", image, start + i * 4, words[i] & 0xFFFF0000 | hi)
    struct.pack_into("<I", image, start + low * 4, words[low] & 0xFFFF0000 | new & 0xFFFF)


class Pool:
    def __init__(self, paw):
        self.paw = paw
        self.at = POOL_START

    def put(self, enc):
        """Store a string, halfword aligned with its NUL; returns its RAM address."""
        at = self.at + (self.at & 1)
        end = at + len(enc) + 2
        if end > POOL_END:
            raise ValueError(f"string pool full: {end - POOL_END} bytes over")
        self.paw[at:end] = enc + b"\0\0"
        self.at = end
        return PAW_BASE + at


def _selftest():
    lui, low, nop = 0x3C050000, 0x24A50000, 0
    old = 0x8014B010
    code = struct.pack("<8I", lui | 0x8015, low | (old - 0x80150000) & 0xFFFF, nop, nop, nop, nop, 0x80148000, old)
    img = bytearray(code)
    patch_ref(img, 0x8014B000, "8014b000", old, 0x800A5968, "t")
    a, b = struct.unpack_from("<2I", img)
    assert resolves(a, b) == 0x800A5968
    patch_ref(img, 0x8014B000, "w8014b01c", old, 0x800A5968, "t")
    assert struct.unpack_from("<I", img, 28)[0] == 0x800A5968
    shared = bytearray(struct.pack("<4I", lui | 0x8015, low | 0x10, 0x8CA60020, nop))  # lw $a2,0x20($a1) after addiu $a1,$a1: consumed, moves
    patch_ref(shared, 0x8014B000, "8014b000", 0x80150010, 0x800A5968, "t")
    other = bytearray(struct.pack("<4I", lui | 0x8015, 0x24A60010, 0x24A70020, nop))  # addiu $a2,$a1,x then addiu $a3,$a1,y: shared
    try:
        patch_ref(other, 0x8014B000, "8014b000", 0x80150010, 0x800A5968, "t")
    except ValueError:
        pass
    else:
        raise AssertionError("shared lui moved")
    pool = Pool(bytearray(POOL_END + 2))
    assert pool.put(b"ab") == PAW_BASE + POOL_START
    assert pool.at == POOL_START + 4


if __name__ == "__main__":
    _selftest()
    print("ok")
