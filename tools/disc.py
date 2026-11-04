"""disc.py: read the ISO9660 tree of a MODE2/2352 image and write data files back in place, with EDC/ECC.

Used instead of mkpsxiso: this disc has a child directory record before its parent's and a PVD abstract id, which
mkpsxiso can't reproduce, and every file's LBA is compiled into the game (docs/re/disc.md)."""
import numpy as np

SECTOR = 2352
USER = 24  # sync 12 + header 4 + subheader 8
SYNC = bytes([0] + [255] * 10 + [0])
SUB_DATA = bytes([0, 0, 8, 0] * 2)
SUB_EOF = bytes([0, 0, 0x89, 0] * 2)
BATCH = 4096  # sectors encoded at once: numpy pays per call, so many small files must share a call

EDC = np.zeros(256, np.uint32)
for i in range(256):
    x = i
    for _ in range(8):
        x = (x >> 1) ^ (0xD8018001 if x & 1 else 0)
    EDC[i] = x
ECC_F = np.zeros(256, np.uint8)
ECC_B = np.zeros(256, np.uint8)
for i in range(256):
    j = ((i << 1) ^ (0x11D if i & 0x80 else 0)) & 0xFF
    ECC_F[i] = j
    ECC_B[i ^ j] = i


def _pq_order(majors, minors, mult, inc):
    size = majors * minors
    return np.array([[((m >> 1) * mult + (m & 1) + n * inc) % size for n in range(minors)] for m in range(majors)])


P_ORDER = _pq_order(86, 24, 2, 86)
Q_ORDER = _pq_order(52, 43, 86, 88)


def _parity(src, order):
    a = np.zeros((len(src), order.shape[0]), np.uint8)
    b = a.copy()
    for minor in range(order.shape[1]):
        t = src[:, order[:, minor]]
        a = ECC_F[a ^ t]
        b ^= t
    a = ECC_B[ECC_F[a] ^ b]
    return np.concatenate((a, a ^ b), axis=1)


def sector_head(lba):
    """Sync and Mode 2 header of a sector."""
    x = lba + 150
    msf = (x // 4500, x // 75 % 60, x % 75)
    return SYNC + bytes(v // 10 * 16 + v % 10 for v in msf) + b"\x02"


def encode_form1(lbas, user, eof):
    """Whole sectors, shape (N, 2352), from lba list, user data (N, 2048) and last-sector flags."""
    s = np.zeros((len(lbas), SECTOR), np.uint8)
    s[:, :16] = np.frombuffer(b"".join(map(sector_head, lbas)), np.uint8).reshape(-1, 16)
    s[:, 16:24] = np.frombuffer(SUB_DATA, np.uint8)
    s[np.asarray(eof, bool), 16:24] = np.frombuffer(SUB_EOF, np.uint8)
    s[:, 24:2072] = user
    crc = np.zeros(len(lbas), np.uint32)
    for i in range(16, 2072):
        crc = (crc >> 8) ^ EDC[(crc ^ s[:, i]) & 0xFF]
    s[:, 2072:2076] = np.frombuffer(crc.astype("<u4").tobytes(), np.uint8).reshape(-1, 4)
    src = s[:, 12:2248].copy()  # Form 1 ECC treats the 4 header bytes as zero
    src[:, :4] = 0
    src[:, 2064:2236] = s[:, 2076:2248] = _parity(src, P_ORDER)
    s[:, 2248:2352] = _parity(src, Q_ORDER)
    return s


def write_files(f, files, log=None):
    """Write (entry, data) pairs, entry being (lba, sectors, size) from walk(), to an image opened r+b.

    Short data is zero-padded to the file's sectors. shortcut: a file can't grow past its sectors or change its ISO
    size; to grow one, also rewrite its directory record and the game's compiled record (docs/re/disc.md).
    log, a list, gets one romdiff.py --writes line per changed sector: what the image held then, so writing a sector twice fails there."""
    lbas, chunks, eofs = [], [], []

    def flush():
        user = np.frombuffer(b"".join(chunks), np.uint8).reshape(-1, 2048)
        for lba, row in zip(lbas, encode_form1(lbas, user, eofs)):
            f.seek(lba * SECTOR)
            if log is not None:
                old = np.frombuffer(f.read(SECTOR), np.uint8)
                diff = np.flatnonzero(old != row)
                if len(diff):
                    a, b = int(diff[0]), int(diff[-1]) + 1
                    log.append(f"{lba * SECTOR + a:X} {old[a:b].tobytes().hex()} {row[a:b].tobytes().hex()} LBA {lba}")
                f.seek(lba * SECTOR)
            f.write(row.tobytes())
        lbas.clear(), chunks.clear(), eofs.clear()

    for (lba, n, _), data in files:
        if len(data) > n * 2048:
            raise ValueError(f"LBA {lba}: {len(data)} bytes don't fit in {n} sectors")
        lbas += range(lba, lba + n)
        chunks.append(data.ljust(n * 2048, b"\0"))
        eofs += [False] * (n - 1) + [True]
        if len(lbas) >= BATCH:
            flush()
    if lbas:
        flush()


def read_user(f, lba, n=1):
    out = bytearray()
    for i in range(n):
        f.seek((lba + i) * SECTOR + USER)
        out += f.read(2048)
    return bytes(out)


def walk(f, lba=None, size=None, prefix=""):
    """Every directory and file as (path, lba, sectors, size), the root as "/"."""
    if lba is None:
        root = read_user(f, 16)[156:190]
        lba, size = int.from_bytes(root[2:6], "little"), int.from_bytes(root[10:14], "little")
        out = [("/", lba, (size + 2047) // 2048, size)]
    else:
        out = []
    data = read_user(f, lba, (size + 2047) // 2048)
    i = 0
    while i < len(data):
        n = data[i]
        if n == 0:  # records never cross a sector: skip to the next one
            i = (i // 2048 + 1) * 2048
            continue
        rec = data[i : i + n]
        i += n
        name = rec[33 : 33 + rec[32]]
        if name in (b"\0", b"\1"):
            continue
        child_lba = int.from_bytes(rec[2:6], "little")
        child_size = int.from_bytes(rec[10:14], "little")
        path = prefix + "/" + name.decode("ascii").split(";")[0]
        out.append((path, child_lba, (child_size + 2047) // 2048, child_size))
        if rec[25] & 2:
            out += walk(f, child_lba, child_size, path)
    return out
