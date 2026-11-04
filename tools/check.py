"""One-command check: every test but the slow ones (the pre-commit hook runs this). ROM-dependent tests skip when rom/ or work/disc is absent.
--full adds them: a whole build and verify_build, about 3 minutes. Required at each phase's end and by tools/release.py."""
import subprocess
import sys

args = [] if "--full" in sys.argv else ["-m", "not slow"]
sys.exit(subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:faulthandler", *args, "tests"]))
