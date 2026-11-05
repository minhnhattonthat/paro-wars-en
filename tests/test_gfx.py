"""FLAG.BIN keeps its size and every stream's offset; only the name strips change."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import gfx  # noqa: E402
import gfx_labels  # noqa: E402
import lzkc  # noqa: E402


OFFSETS = 0x20, 0x884, 0xEE9, 0x163D, 0x1F3D, 0x26FA, 0x2D4F, 0x357D, 0x3A9C


def streams(data):
    return [lzkc.decompress(data[at:at + 4 + int.from_bytes(data[at:at + 3], "little")], strict=True) for at in OFFSETS]


def test_clean_map_erases_ink_and_keeps_tones():
    """Two cloth tones split at row 10; ink crosses them. The clean band is x 0-7 and the rect x 8-39."""
    page = ("x", 0, 40, 8)
    data = bytearray(([5] * 40) * 10 + ([6] * 40) * 10)
    for y in range(4, 16):
        for x in range(20, 28):
            data[y * 40 + x] = 9
    under = gfx._clean_map(data, page, [(8, 0, 32, 20)], ("clean", 0, 8, 0, 20))
    assert set(under.values()) == {5, 6}
    assert under[24, 2] == 5 and under[24, 17] == 6
    assert under[10, 3] == 5 and under[35, 16] == 6


def test_every_label_fits():
    """A pixel-font label too wide stops the build, so catch it in the pre-commit check, which doesn't build."""
    labels = gfx_labels.LABELS + [label for stream in gfx_labels.FLAG_STREAMS for label in stream]
    seen = {(text, id(style), sum(r[2] for r in rects), max(r[3] for r in rects)) for _, rects, text, style, *_ in labels}
    for text, style_id, w, h in seen:
        style = next(s for _, _, _, s, *_ in labels if id(s) == style_id)
        lines = text.split("|")
        for line in lines:
            if line:
                gfx.mask(line, style, w, h // len(lines))


def test_flag():
    old = (ROOT / "work/disc/tree" / gfx_labels.FLAG).read_bytes()
    new = gfx.apply(gfx_labels.FLAG, old)
    assert len(new) == len(old) and new[:0x20] == old[:0x20]
    for a, b in zip(streams(old), streams(new)):
        assert len(a) == len(b) == 0x2000
        assert a[:48 * 64] != b[:48 * 64]  # the name
        assert a[48 * 64:] == b[48 * 64:]  # the flag
