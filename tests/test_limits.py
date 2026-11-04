"""The width lint: self-tests, the menu tables, moved strings, and every English text written so far fits its box."""
import glob
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import limits
import menu_tables
import reloc

need = pytest.mark.skipif(not (ROOT / "work/disc/tree/PAW.EXE").exists(), reason="needs work/disc/tree")


def docs():
    for path in sorted(glob.glob(str(ROOT / "script/*/*.json"))):
        yield json.loads(Path(path).read_text(encoding="utf-8"))


def test_reloc_selftest():
    reloc._selftest()


@need
def test_limits_selftest():
    limits._selftest()


@need
def test_digit_writers():
    """Every call to the code that writes digits into a string finds its cells in the English, on screens no tour reached too."""
    sys.path.insert(0, str(ROOT / "tools/debug"))
    import pokes

    assert pokes.main() == 0


def test_verify_stray():
    import verify_build

    assert verify_build.stray(b"abcd", b"axcd", [(1, 2)], set()) == []
    assert verify_build.stray(b"abcd", b"axcd", [], {1}) == []
    assert verify_build.stray(b"abcd", b"axcd", [(2, 4)], {0}) == [1]
    assert verify_build.stray(b"abcd", b"abc", [(0, 4)], set())[0][0] == "size"


@need
def test_menu_windows_hold_their_japanese():
    """The dialog formula must not be tighter than what the game already shows."""
    index = menu_tables.index()
    assert len(index) > 40
    for doc in docs():
        for e in doc["entries"]:
            if e["id"] in index and e["kind"] == "text":
                assert max(limits.jp_px(e["jp"])) <= limits.limit(e).px[0] + 12, e["id"]


@need
def test_every_translation_fits():
    bad = []
    for doc in docs():
        for e in doc["entries"]:
            if e["kind"] == "text" and e["en"]:
                for problem in limits.check(e, e["en"]):
                    bad.append(f"{e['id']}: {problem}: {e['en']!r}")
    assert not bad, "\n".join(bad[:40])
