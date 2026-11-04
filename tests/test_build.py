"""The English build from the script as committed: raises if anything has no room, and build.py ends with verify_build (read-back, stale readers, write log)."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import verify_build

pytestmark = pytest.mark.skipif(not (ROOT / "rom/Paro Wars (Japan).bin").is_file(), reason="needs rom/")


@pytest.mark.slow
def test_build_verifies():
    out = "paro_wars_check"
    try:
        result = subprocess.run([sys.executable, "-X", "utf8", "tools/build.py", "--out", out], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
        assert "verify ok" in result.stdout and "read back" in result.stdout
    finally:
        for suffix in (".bin", ".cue", ".writes"):
            (ROOT / "build" / (out + suffix)).unlink(missing_ok=True)


def test_stale_readers():
    old = 0x8014B010
    lui, low = 0x3C058015, 0x24A5B010  # lui $a1,0x8015; addiu $a1,$a1,-0x4FF0
    code = lui.to_bytes(4, "little") + low.to_bytes(4, "little") + bytes(8) + old.to_bytes(4, "little")
    found = verify_build.stale_readers(code, {old: "t"})
    assert [at for at, _ in found] == [16, 0]
    assert verify_build.stale_readers(code, {0x80000000: "t"}) == []


@pytest.mark.skipif(not (ROOT / "work/disc/tree/PAW.EXE").exists(), reason="needs work/disc/tree")
def test_read_back_bites():
    import en_text
    import limits
    import reloc

    pool = reloc.POOL_START
    enc = en_text.encode("Hi there")
    paw = bytearray(pool + 64)
    paw[pool:pool + len(enc) + 2] = enc + b"\0\0"
    addr = (reloc.PAW_BASE + pool).to_bytes(4, "little")
    paw[8:12] = addr  # the moved string's ref
    paw[16:22] = bytes([limits.FAR_MARK, en_text.PAD]) + addr  # the far string's slot
    paw[32:40] = en_text.encode("Hi").ljust(8, b"\0")
    entries = [
        {"id": "PAW:0", "off": 32, "len": 8, "kind": "text", "en": "Hi", "jp": "あ"},
        {"id": "PAW:1", "off": 24, "len": 4, "kind": "text", "en": "Hi there", "jp": "あ", "refs": [f"PAW:w{reloc.PAW_BASE + 8:08x}"]},
        {"id": "PAW:2", "off": 16, "len": 6, "kind": "text", "en": "Hi there", "jp": "あ"},
    ]
    docs = {"PAW.EXE": [{"entries": entries}]}

    def run(image):
        return verify_build.read_back(docs, lambda rel: bytes(image), lambda name: reloc.PAW_BASE)

    bad, counts, vacated = run(paw)
    assert not bad and counts == {"slot": 1, "far": 1, "moved": 1} and vacated == {reloc.PAW_BASE + 24: "PAW:1"}
    for at, name in ((32, "PAW:0"), (8, "PAW:1"), (24, "PAW:1"), (17, "PAW:2"), (pool, "PAW:1")):
        broken = bytearray(paw)
        broken[at] ^= 0x55
        assert any(p.startswith(name) for p in run(broken)[0]), at


def test_write_log(tmp_path):
    import disc
    import romdiff

    path = tmp_path / "x.bin"
    path.write_bytes(bytes(disc.SECTOR * 4))
    log = []
    with open(path, "r+b") as f:
        disc.write_files(f, [((1, 1, 3), b"abc")], log)
        disc.write_files(f, [((1, 1, 3), b"xyz")], log)  # same sector again: the second line's "before" isn't the original
    writes = [(int(a, 16), bytes.fromhex(b), bytes.fromhex(c), d) for a, b, c, d in (line.split(None, 3) for line in log)]
    errors = romdiff.check(bytes(disc.SECTOR * 4), path.read_bytes(), set(), writes)[0]
    assert any("overlaps" in e for e in errors) and any("expects orig" in e for e in errors)
    assert romdiff.check(bytes(disc.SECTOR * 4), path.read_bytes(), set(), writes[1:2])[0]
