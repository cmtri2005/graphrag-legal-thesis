import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/eval"))

import colab_b1  # noqa: E402
import vllm_generate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_digest_matches_the_repository_hash_on_real_prompts():
    for path in (ROOT / "runs/final_rehearsal_g3_20261112/r1/prompts/b4.jsonl",
                 ROOT / "runs/lightrag_20261113/dev/prompts/lightrag.jsonl"):
        row = json.loads(path.open(encoding="utf-8").readline())
        assert vllm_generate.digest(row) == colab_b1.digest(row) == row["prompt_sha256"]
