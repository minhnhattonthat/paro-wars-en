"""One-command check: every test (the pre-commit hook runs this). ROM-dependent tests skip when rom/ or work/disc is absent."""
import subprocess
import sys

sys.exit(subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "tests"]))
