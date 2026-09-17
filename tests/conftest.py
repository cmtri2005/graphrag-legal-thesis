"""Makes the pipeline scripts importable by name.

`scripts/` is not a package — the files there are executables with a
`if __name__ == "__main__"` and are meant to be run, not imported. A couple of
them own logic worth testing directly (the resumable fetcher, the staleness
rule), so their directory goes on the path here once instead of each test
repeating the same three lines.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "pipeline"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "review"))
