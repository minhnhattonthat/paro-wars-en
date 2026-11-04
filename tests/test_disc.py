"""Identity build: every file from the unpacked tree, written into a blank image, must give the original disc."""
import hashlib
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from disc import SECTOR, SUB_DATA, SUB_EOF, sector_head, walk, write_files

ORIG = ROOT / "rom" / "Paro Wars (Japan).bin"
TREE = ROOT / "work" / "disc" / "tree"
RAW = 2336  # dumpsxiso keeps XA and STR files as subheader + data + parity


@pytest.mark.skipif(not ORIG.is_file() or not TREE.is_dir(), reason="needs rom/ and work/disc/tree")
def test_tree_rebuilds_the_original_disc(tmp_path):
    out = tmp_path / "identity.bin"
    with open(ORIG, "rb") as fo, open(out, "w+b") as fb:
        total = ORIG.stat().st_size // SECTOR
        fb.truncate(total * SECTOR)
        entries = [e for e in walk(fo) if (TREE / e[0][1:]).is_file()]
        assert len(entries) == sum(1 for p in TREE.rglob("*") if p.is_file()) - 1  # all but license_data.dat

        data_files, covered = [], bytearray(total)
        for path, lba, n, size in entries:
            covered[lba : lba + n] = b"\1" * n
            local = (TREE / path[1:])
            if local.stat().st_size == size:
                data_files.append(((lba, n, size), local.read_bytes()))
            else:
                assert local.stat().st_size == n * RAW, path
                raw = local.read_bytes()
                for i in range(n):
                    fb.seek((lba + i) * SECTOR)
                    fb.write(sector_head(lba + i) + raw[i * RAW : (i + 1) * RAW])
        assert sum(n for (_, n, _), _ in data_files) > 100_000  # the encoder really wrote most of the disc
        write_files(fb, data_files)

        for lba in range(total):  # system area, directories and the gaps between files
            if not covered[lba]:
                fo.seek(lba * SECTOR)
                fb.seek(lba * SECTOR)
                fb.write(fo.read(SECTOR))
        fb.seek(0)
        got = hashlib.file_digest(fb, "sha1").hexdigest()
    want = (ROOT / "rom.sha1").read_text().split("\n")[1].split()[0]
    assert got == want, f"see: python -X utf8 tools/disc_diff.py rom/... {out}"


def test_write_pads_marks_eof_and_refuses_overflow():
    f = io.BytesIO(bytes(3 * SECTOR))
    write_files(f, [((1, 2, 4096), b"abc")])
    img = f.getvalue()
    assert img[:SECTOR] == bytes(SECTOR)  # the neighbour is untouched
    first, last = img[SECTOR : 2 * SECTOR], img[2 * SECTOR :]
    assert first[:16] == sector_head(1) and first[16:24] == SUB_DATA and first[24:29] == b"abc\0\0"
    assert last[16:24] == SUB_EOF and last[24:2072] == bytes(2048)
    with pytest.raises(ValueError):
        write_files(f, [((1, 2, 4096), bytes(4097))])
