"""release.py [--version 1.0] [--force]: build, gate and package the patch. Stops at the first failure.

build + full check -> smoke -> Japanese-left scan -> qa_gate on every work/qa/**/manifest.tsv -> no open line in docs/polish.md
-> xdelta3 patch of the .bin -> re-apply to a clean original and compare -> zip (patch + PATCHING.txt, stored) in release/.
The debug tool is Lua run by the emulator (tools/debug/warp.lua), so no build of this game holds any debug code.
Never publishes; that is the owner's call.
"""
import argparse
import glob
import hashlib
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS

ORIG = ROOT / "rom/Paro Wars (Japan).bin"
BUILT = ROOT / "build/paro_wars_en.bin"
CUE = ROOT / "build/paro_wars_en.cue"
CODE_RUNS = "14 runs in code files"  # machine code that happens to look like Shift-JIS, read in phase 7: a new run must be looked at


def run(*cmd, **kw):
    print("==", " ".join(str(c) for c in cmd), flush=True)
    p = subprocess.run([str(c) for c in cmd], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if p.returncode:
        sys.exit(f"FAILED ({p.returncode}): {p.stdout[-3000:]}\n{p.stderr[-3000:]}")
    return p.stdout


def hashes(path):
    crc, sha, size = 0, hashlib.sha1(), 0
    with open(path, "rb") as f:
        while chunk := f.read(1 << 22):
            crc, size = zlib.crc32(chunk, crc), size + len(chunk)
            sha.update(chunk)
    return size, f"{crc:08X}", sha.hexdigest()


def gates():
    out = run(sys.executable, "-X", "utf8", "tools/jp_left_files.py", BUILT)
    if CODE_RUNS not in out or "\n0 runs in compressed script files" not in out:
        sys.exit("Japanese left:\n" + out)
    manifests = glob.glob(str(ROOT / "work/qa/**/manifest.tsv"), recursive=True)
    if len(manifests) < 2:
        sys.exit(f"expected the tour and story manifests, found {manifests}")
    for m in manifests:
        run(sys.executable, "-X", "utf8", f"{SCRIPTS}/qa_gate.py", "check", m, str(Path(m).parent / "verdicts"))
    open_lines = [x for x in (ROOT / "docs/polish.md").read_text(encoding="utf-8").splitlines() if x.startswith("- [ ]")]
    if open_lines:
        sys.exit("docs/polish.md has open lines:\n" + "\n".join(open_lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's files")
    a = ap.parse_args()
    name = f"Paro_Wars_EN_v{a.version}"
    out = ROOT / "release" / name
    zpath = ROOT / "release" / f"{name}.zip"
    if zpath.exists() and not a.force:
        sys.exit(f"{zpath} exists; --force to overwrite")
    out.mkdir(parents=True, exist_ok=True)

    run(sys.executable, "-X", "utf8", "tools/check.py", "--full")  # builds, tests, verify_build
    run(sys.executable, "-X", "utf8", f"{SCRIPTS}/emu.py", CUE, "--out", "work/qa/smoke", "--route", "tools/routes/boot.txt", "--smoke")
    gates()

    patch = out / f"{name}.xdelta"
    run("xdelta3", "-e", "-f", "-9", "-S", "none", "-s", ORIG, BUILT, patch)
    with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
        back = Path(tmp) / "back.bin"
        run("xdelta3", "-d", "-f", "-s", ORIG, patch, back)
        built, applied = hashes(BUILT), hashes(back)
        if built != applied:
            sys.exit(f"re-applied patch differs: {built} vs {applied}")

    base = hashes(ORIG)
    text = (ROOT / "tools/PATCHING.txt").read_text(encoding="utf-8").format(version=a.version, patch=patch.name, base_size=base[0], base_crc=base[1], base_sha=base[2], new_crc=built[1], new_sha=built[2])
    (out / "PATCHING.txt").write_text(text, encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        z.write(patch, patch.name)
        z.write(out / "PATCHING.txt", "PATCHING.txt")
    print(f"{zpath} ({zpath.stat().st_size} bytes); patched .bin CRC32 {built[1]} SHA-1 {built[2]}")


if __name__ == "__main__":
    main()
