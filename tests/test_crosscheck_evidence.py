"""Cutting the source passages behind a D4 row."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))
from crosscheck_evidence import actor_passage, base_passage, lines  # noqa: E402


def test_base_passage_finds_the_clause_in_the_right_chapter():
    ls = lines("<p>Điều 5. Ban hành</p><p>Chương II</p><p>Điều 5. Hồ sơ</p><p>1. Một</p>"
               "<p>a) điểm</p><p>2. Hai</p><p>Điều 6. Khác</p>")
    got = base_passage(ls, {"article_id": "5", "clause_id": "1", "provision_path": "Chương II › Điều 5 › Khoản 1"})
    assert got == "Điều 5. Hồ sơ\n1. Một\na) điểm"


def test_actor_passage_keeps_the_items_of_a_numbered_instruction():
    ls = lines("<p>24. Sửa đổi, bổ sung Điều 33 như sau:</p><p>a) Sửa đổi khoản 13 Điều 33 như sau:</p>"
               "<p>“13. Mới.”</p><p>b) Sửa đổi khoản 14 Điều 33 như sau:</p><p>25. Bãi bỏ Điều 40.</p>")
    got = actor_passage(ls, "Sửa đổi, bổ sung Điều 33 như sau", "12/2017/TT-BGTVT", "33")
    assert got.splitlines()[-1] == "b) Sửa đổi khoản 14 Điều 33 như sau:"
    assert actor_passage(ls, "a) Sửa đổi khoản 13", "x", "33").splitlines()[-1] == "“13. Mới.”"


def test_actor_passage_does_not_take_article_60_for_article_6():
    ls = lines("<p>d) Sửa đổi điểm đ khoản 4 Điều 60 như sau:</p><p>b) Bãi bỏ điểm i khoản 2; điểm đ khoản 4 Điều 6;</p>")
    assert actor_passage(ls, "điểm đ khoản 4 Điều 6", "100/2019/NĐ-CP", "6") == "b) Bãi bỏ điểm i khoản 2; điểm đ khoản 4 Điều 6;"


def test_test2_legacy_transition_recovers_operation_from_event_log(tmp_path, monkeypatch):
    import json
    import crosscheck_evidence as evidence
    data = tmp_path / 'data'
    (data / 'raw').mkdir(parents=True)
    (data / 'derived').mkdir()
    def write(path, values):
        path.write_text(''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in values), encoding='utf-8')
    write(data / 'derived/event_log.jsonl', [{'event_id': 'e1', 'outcome': 'applied', 'operation': 'amend',
                                            'closed_version_ids': ['version:p:1']}])
    write(data / 'derived/provision_events.jsonl', [{'id': 'e1', 'actor_id': 'document:2',
                                                   'evidence': 'Sửa đổi Điều 1'}])
    for key, text in [('1', '<p>Điều 1. Bản gốc</p>'), ('2', '<p>Sửa đổi Điều 1 như sau:</p><p>Lời văn mới</p>')]:
        (data / 'raw' / f'{key}.json').write_text(json.dumps({'docNum': 'VB' + key,
                'documentContent': {'content': text}}), encoding='utf-8')
    release, ids, out = (tmp_path / name for name in ('rows.jsonl', 'ids.txt', 'evidence.jsonl'))
    write(release, [{'id': 'r1', 'derivation': {'transitions': [{'event_id': 'e1'}]},
                     'target': {'document_id': 'document:1', 'article_id': '1', 'law_id': 'VB1', 'provision_id': 'provision:p'}}])
    ids.write_text('r1\n')
    monkeypatch.setattr(sys, 'argv', ['crosscheck_evidence', '--data', str(data), '--release', str(release),
                                    '--ids', str(ids), '--out', str(out)])
    evidence.main()
    row = json.loads(out.read_text())
    assert row['actors'][0]['op'] == 'amend'
    assert row['actors'][0]['passage'] == 'Sửa đổi Điều 1 như sau:\nLời văn mới'
    assert row['base']['passage'] == 'Điều 1. Bản gốc'
