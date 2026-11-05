"""The staff roll: every line the files show has English, and what the game is told to draw stays on the new sheet."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import credits  # noqa: E402

TREE = ROOT / "work/disc/tree"
pytestmark = pytest.mark.skipif(not (TREE / credits.SEQ[0]).is_file(), reason="needs work/disc/tree")


def test_every_line_known():
    seen = set()
    for rel in credits.SEQ:
        n, ch = credits.chains((TREE / rel).read_bytes())
        for chain in ch.values():
            seen |= {t for _, t in credits.lines_of(n, chain).values()}
    assert seen == set(credits.LINES)


def test_patched_lists_stay_on_the_sheet():
    where = credits.layout()
    strips = set(where.values())
    for rel in credits.SEQ:
        d = (TREE / rel).read_bytes()
        old_n, old = credits.chains(d)
        new = credits.patch(d)
        n = credits.nodes(new)
        for head, chain in old.items():
            rows = credits.lines_of(old_n, chain)
            at, got = head, []
            while at is not None:
                x, y, u, v, w, h, page, at = n[at]
                assert (page, u, v, w) in strips and h == credits.ROW_H
                assert u + w <= (255 if page == 9 else 128), "the game keeps u + w in a byte"
                got.append(y)
            assert got == list(rows)


def test_sheet_has_every_line():
    s = credits.sheet()
    assert len(s) == 24576
    assert sum(b != 0 for b in s) > 3000
