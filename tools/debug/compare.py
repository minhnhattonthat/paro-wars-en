"""compare.py OUT ORIG_DIR EN_DIR SCENE[/SHOT] ...: original left, English right, zoomed, per scene. Each arg names a scene dir, optionally a shot in it."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL


def main():
    out, a, b, *names = sys.argv[1:]
    files = []
    for name in names:
        scene, _, shot = name.partition("/")
        shot = shot or scene
        files += [str(Path(a) / scene / f"{shot}.png"), str(Path(b) / scene / f"{shot}.png")]
    subprocess.run([sys.executable, "-X", "utf8", f"{SKILL}/scripts/sheet.py", *files, "--zoom", "2", "--cols", "2", "--out", out], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
