"""The LZ codec against synthetic data and, when the disc is unpacked, against real files."""
import glob
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import lzkc


@pytest.mark.parametrize("data", [b"", b"a", b"abcabcabc" * 50, bytes(range(256)) * 8, b"\0" * 4000])
def test_roundtrip_synthetic(data):
    assert lzkc.decompress(lzkc.compress(data), strict=True) == data


def test_max_length_copies_are_legal():
    # 34-byte absolute copies and 5-byte short copies are the longest tokens; both must decode to the input
    data = b"".join(bytes([i]) * 40 for i in range(20)) + bytes(range(100)) * 3
    assert lzkc.decompress(lzkc.compress(data), strict=True) == data


REAL = ["DATA/PENHELP.BIN", "DATA/ENDING/STAFF.BIN", "DATA/DEMO/PEN0_00.BIN", "DATA/BK_DT/S_000_O.BIN"]


@pytest.mark.parametrize("name", REAL)
def test_roundtrip_real(name):
    path = ROOT / "work/disc/tree" / name
    if not path.exists():
        pytest.skip("disc not unpacked")
    raw = path.read_bytes()
    plain = lzkc.decompress(raw, strict=True)
    assert lzkc.decompress(lzkc.compress(plain), strict=True) == plain
