"""The translation rules over the English that ships, in script/*.json: a clean clone runs this, work/tl isn't needed."""
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches
import bios


def test_script_is_clean():
    bad = batches.lint()
    assert not bad, "\n".join(bad[:40])


def test_bios_match_their_paragraphs():
    index = batches.entries()
    bad = [eid for eid, en in bios.flow_all().items() if index[eid][1]["en"] != en]
    assert not bad, f"run bios.py flow: {bad[:10]}"


def test_rules_bite():
    """Each rule must fail on a line that breaks it, or the green above means nothing."""
    index = batches.entries()
    terms = batches.glossary()

    def problems(eid, en, jp=None):
        group, e = index[eid]
        e = copy.deepcopy(e)
        e["jp"] = jp or e["jp"]
        return " ".join(batches.problems(group, e, en, terms))

    page = "DEMO/TXT_PEN0:96"
    assert "empty" in problems(page, "")
    assert "glossary: ペン太郎" in problems(page, "The penguin", "ペン太郎")
    assert "Avoid: Pentarou" in problems(page, "Pentaro or Pentarou", "ペン太郎")
    assert "glossary: 首長" in problems(page, "Moai's chief", "モアイ国首長よしこ")
    assert "honorific さん" in problems(page, "Pentaro", "ペンタさん")
    assert "Greek" in problems(page, "It", "κξ")
    assert "layout gap" in problems("DEMO/KABE4:1001a", "It")
    assert "digits the code writes" in problems("PAW:a8c70", "Ukki")
    assert "ordinal" in problems("PAW:8e8", "th!!")
    assert "bad characters" in problems(page, "カ")
