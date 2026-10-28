import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))
import agent_sample  # noqa: E402


def test_sample_is_fixed_and_has_no_duplicates():
    rows = [{"id": f"r{i}"} for i in range(325)]
    a, b = agent_sample.sample(rows), agent_sample.sample(list(reversed(rows)))
    assert [r["id"] for r in a] == [r["id"] for r in b] and len({r["id"] for r in a}) == 50
