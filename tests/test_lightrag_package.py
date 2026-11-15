import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/eval"))

import lightrag_package  # noqa: E402


def test_coverage_counts_gold_and_other_version_spans_in_json_escaped_evidence():
    rows = [
        {"id": "a", "answerable": True, "short_answer": "25.000.000 đồng", "_distractors": ["50 000 000 đồng"]},
        {"id": "b", "answerable": True, "short_answer": "03 tháng… 12 tháng", "_distractors": []},
        {"id": "c", "answerable": False, "short_answer": None, "_distractors": []},
    ]
    evidence = {"a": 'phạt đến 25.000.000\\nđồng. Sửa thành: \\"50.000.000 đồng\\"',   # LightRAG keeps \n and \" escaped
                "b": "từ 03 tháng đến 06 tháng", "c": "không tính"}
    out = lightrag_package.coverage(rows, evidence)
    out.pop("median_evidence_chars")
    assert out == {"rows": 2, "gold": 1, "contrast_rows": 1, "other": 1, "gold_and_other": 1}
