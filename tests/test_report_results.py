import json

from report_results import render


def _metrics(acc):
    return {"rows": 2, "accuracy": acc, "accuracy_lenient": acc, "tv_recall@1": 0.5, "recall@1": 0.5,
            "tver": None, "wrong_version": 0.0, "citation_coverage": 1.0, "ci95": {"accuracy": [0.0, 1.0]}}


def test_render_reads_score_and_confirm_without_recomputing(tmp_path):
    groups = lambda acc: {"giua_khoang": {g: _metrics(acc) for g in ("all", "T1", "T2", "T3", "T6")}}
    diff = {"giua_khoang": {"all": {"accuracy": 0.25, "tv_recall@1": 0.0, "tver": None,
                                    "ci95": {"accuracy": [0.1, 0.4]}}}}
    score = tmp_path / "dev" / "x.score.json"
    score.parent.mkdir()
    score.write_text(json.dumps({"b1": groups(0.25), "b2ctx": groups(0.5), "b2ctx − b1": diff}))
    confirm = tmp_path / "confirm.json"
    confirm.write_text(json.dumps({"split": "dev", "draws": 2000, "tests_run": 1, "results": {
        "XN9": {"estimate": 0.25, "ci95": [0.1, 0.4], "p": 0.01, "p_holm": 0.01, "verdict": "ủng hộ",
                "rows": {"all": 2}, "lineages": {"all": 1}}}}))

    md = render([score], confirm)
    assert "**Số dev**" in md
    assert "| `b2ctx` | 0,500 [0,000; 1,000] |" in md
    assert "| b2ctx − b1 | +0,250 [+0,100; +0,400] | +0,000 | — |" in md
    assert "2.000 lần lấy mẫu lại, Holm trên 1/9 kiểm định (**chưa đủ họ**)" in md
    assert "| XN9 |" in md and "| ủng hộ | 2/1 |" in md
    assert "| XN1 |" in md and "chưa chạy" in md
