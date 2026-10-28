import json
import subprocess
import sys
from pathlib import Path

from run_vilextime import queries


def test_as_of_strategy_filters_before_limit(tmp_path):
    release = tmp_path / "release.jsonl"
    rows = [
        {"id": "boundary", "split": "dev", "as_of_strategy": "ranh_gioi", "question": "q1", "as_of": "2020-01-01"},
        {"id": "middle", "split": "dev", "as_of_strategy": "giua_khoang", "question": "q2", "as_of": "2020-01-02"},
        {"id": "test", "split": "test", "as_of_strategy": "giua_khoang", "question": "q3", "as_of": "2020-01-03"},
    ]
    release.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    assert [q.id for q in queries(release, "dev", 1, "giua_khoang")] == ["middle"]
    assert [q.id for q in queries(release, "dev", None)] == ["boundary", "middle"]

    out = tmp_path / "predictions.jsonl"
    runner = Path(__file__).resolve().parents[1] / "scripts/eval/run_vilextime.py"
    subprocess.run([sys.executable, str(runner), "--system", "b1", "--retrieval-only",
                    "--split", "dev", "--as-of-strategy", "giua_khoang",
                    "--release", str(release), "--out", str(out)], check=True)
    assert [json.loads(line)["id"] for line in out.open(encoding="utf-8")] == ["middle"]
    assert json.loads(out.with_suffix(".run.json").read_text())[0]["as_of_strategy"] == "giua_khoang"
