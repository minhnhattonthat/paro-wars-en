"""FLAG.BIN keeps its size and its chain of nine streams; only the name strips change."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import gfx  # noqa: E402
import gfx_labels  # noqa: E402
import lzkc  # noqa: E402


def streams(data):
    out, at = [], 0x20
    for _ in gfx_labels.FLAG_STREAMS:
        end = at + 4 + int.from_bytes(data[at:at + 3], "little")
        out.append(lzkc.decompress(data[at:end], strict=True))
        at = end
    return out


def test_flag():
    old = (ROOT / "work/disc/tree" / gfx_labels.FLAG).read_bytes()
    new = gfx.apply(gfx_labels.FLAG, old)
    assert len(new) == len(old) and new[:0x20] == old[:0x20]
    for a, b in zip(streams(old), streams(new)):
        assert len(a) == len(b) == 0x2000
        assert a[:48 * 64] != b[:48 * 64]  # the name
        assert a[48 * 64:] == b[48 * 64:]  # the flag
