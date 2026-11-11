import json
import random
import pytest

from test2_packs import QUOTA, QUOTA2, copy_share, draw, judge_question, lineage_truth, pending, published_scope, qcheck, qpack, redo, score, stratum

AB = {"status": "checked", "source": "human", "labeler": "A+B"}


def test_truth_uses_only_independent_labels_and_lineage_level_reasons():
    ok = {**AB, "verdict": "dat", "reasons": []}
    moved = {**AB, "verdict": "khong_dat", "reasons": ["relocation_unclear"]}
    asked = {**AB, "verdict": "khong_dat", "reasons": ["question_leaks"]}
    assert lineage_truth([ok, ok]) == ("tot", [])
    assert lineage_truth([ok, moved]) == ("xau", ["relocation_unclear"])
    assert lineage_truth([ok, asked]) is None                  # a question flaw the filter cannot see
    helped = {**moved, "labeler": "luật sư X, có phiếu Claude hỗ trợ"}
    assert lineage_truth([ok, helped]) is None                 # not blind to Claude
    assert lineage_truth([ok, {**ok, "labeler": "A"}]) is None  # one person is not a final label
    assert lineage_truth([ok, {**moved, "labeler": "luật sư (mẫu agent)"}])[0] == "xau"


def test_stratum_tags():
    assert stratum({"group": "T2", "near_identical": True}) == "T2 gần giống"
    assert stratum({"group": "T6", "repeal_mode": "ancestor"}) == "T6 cấp trên"
    assert stratum({"group": "T6", "repeal_mode": "direct"}) == "T6 đích danh"


def test_score_gate(tmp_path, capsys):
    key = tmp_path / "key.tsv"
    key.write_text("item\tnhom\tvai_tro\tsu_that\tma\n"
                   "x1\tT2\thieu_chuan\txau\tcosmetic_only\nx2\tT2\thieu_chuan\txau\trename_only\n"
                   "g1\tT2\thieu_chuan\ttot\t\nc1\tT3\tung_vien\t\t\n", encoding="utf-8")
    res = tmp_path / "result.tsv"
    res.write_text("item\tquyet_dinh\tma\tcan_cu\tghi_chu\n"
                   "x1\tloai\tcosmetic_only\t\t\nx2\tloai\trename_only\t\t\ng1\tgiu\t\t\t\nc1\tgiu\t\t\t\n",
                   encoding="utf-8")
    assert score(tmp_path, [res], key)
    res.write_text(res.read_text(encoding="utf-8").replace("x2\tloai", "x2\tgiu"), encoding="utf-8")
    assert not score(tmp_path, [res], key)                       # caught 1/2 < 0.80
    assert "ứng viên được giữ: {'T3': 1}" in capsys.readouterr().out
    fix = tmp_path / "fix.tsv"
    fix.write_text("item\tquyet_dinh\tma\tcan_cu\tghi_chu\nx2\tloai\trename_only\t\t\n", encoding="utf-8")
    assert score(tmp_path, [res, fix], key)                    # the later result wins


def test_redo_takes_all_calibration_and_only_candidates_rejected_for_the_fixed_code(tmp_path):
    old = tmp_path / "gan/packs"
    old.mkdir(parents=True)
    for name in ("CLAUDE.md", "AGENTS.md"):
        (old.parent / name).write_text("x", encoding="utf-8")
    ids = ["k1", "k2", "c1", "c2", "c3"]
    (old / "pack_01.jsonl").write_text("".join(json.dumps({"item": i}) + "\n" for i in ids), encoding="utf-8")
    (tmp_path / "key_loc.tsv").write_text("item\tnhom\tvai_tro\tsu_that\tma\n" + "".join(
        f"{i}\tT2\t{'hieu_chuan' if i[0] == 'k' else 'ung_vien'}\t\t\n" for i in ids), encoding="utf-8")
    res = tmp_path / "r.tsv"
    res.write_text("item\tquyet_dinh\tma\tcan_cu\tghi_chu\nk1\tgiu\t\t\t\nk2\tloai\tother\t\t\n"
                   "c1\tgiu\t\t\t\nc2\tloai\ttransitional_rule\t\t\nc3\tloai\tother\t\t\n", encoding="utf-8")
    got = redo(tmp_path / "gan2/packs", old, res, {"transitional_rule"})
    assert sorted(got) == ["c2", "k1", "k2"]
    assert (tmp_path / "gan2/HUONG_DAN.md").exists() and (tmp_path / "gan2/CLAUDE.md").exists()


def test_second_round_continues_the_first_without_overlap():
    pool = lambda: {s: [f"{s}-{i}" for i in range(QUOTA[s] + QUOTA2[s] + 3)] for s in QUOTA}
    first, second = draw(pool(), random.Random("x"))
    assert not set(first) & set(second)
    assert len(first) == sum(QUOTA.values()) and len(second) == sum(QUOTA2.values())
    assert draw(pool(), random.Random("x")) == (first, second)   # same seed, same round 1


def test_copy_share_ignores_function_words_and_gates_at_forty_percent():
    gold = ["Phí đăng ký là 30 nghìn đồng cho mỗi hồ sơ"]
    assert copy_share("Phí đăng ký là bao nhiêu?", gold) == 1.0               # chỉ chữ có nghĩa: phí, đăng, ký
    assert copy_share("Doanh nghiệp phải trả mức tiền ra sao?", gold) == 0.0
    copied = "Một công ty cần nộp phí đăng ký hồ sơ bao nhiêu tiền?"
    assert judge_question(copied, "", gold).startswith("copy_share")
    assert judge_question("Một công ty cần trả bao nhiêu tiền khi xin làm thủ tục này?", "", gold) is None
    assert judge_question("KHONG_DU_NGU_CANH", "", gold) == "insufficient_context"


def published_fixture(data):
    dest = data / "vilextime_dataset"
    dest.mkdir(parents=True)
    (dest / "vilextime.jsonl").write_text(
        json.dumps({"id": "d", "lineage_id": "old-dev", "split": "dev", "group": "T1"}) + "\n" +
        json.dumps({"id": "t", "lineage_id": "old-test", "split": "test", "group": "T2"}) + "\n")
    (dest / "vilextime_meta.jsonl").write_text(
        json.dumps({"id": "d", "target": {"document_id": "doc-dev-t1"}}) + "\n")
    return dest


def test_dev_scope_includes_documents_represented_only_by_t1(tmp_path):
    dest = published_fixture(tmp_path)
    assert published_scope(tmp_path) == ({"old-dev", "old-test"}, {"doc-dev-t1"})
    (dest / "vilextime_meta.jsonl").write_text("")
    with pytest.raises(SystemExit, match="d: thiếu document_id của dev.*khôi phục metadata v1.0"):
        published_scope(tmp_path)


def test_question_packs_exclude_dev_documents_and_v1_lineages_without_changing_filter_results(tmp_path, monkeypatch):
    published_fixture(tmp_path / "data")
    rows = {lid: [{"lineage_id": lid, "group": "T2", "answer": "Mức phí 30 nghìn đồng.",
                   "target": {"document_id": doc, "document_title": "Phí cấp phép", "lead_in": ""}}]
            for lid, doc in [("new-dev", "doc-dev-t1"), ("old-test", "doc-test"), ("fresh", "doc-new")]}
    monkeypatch.setattr("test2_packs.lineage_rows", lambda data, ids: rows)
    key = tmp_path / "key.tsv"
    key.write_text("item\tnhom\tvai_tro\n" + "".join(f"{lid}\tT2\tung_vien\n" for lid in rows))
    result = tmp_path / "result.tsv"
    result.write_text("item\tquyet_dinh\tma\tcan_cu\tghi_chu\n" + "".join(f"{lid}\tgiu\t\t\t\n" for lid in rows))
    before = result.read_bytes()
    out = tmp_path / "questions/packs"
    qpack(out, [result], tmp_path / "data", key, None)
    records = [json.loads(line) for line in (out / "pack_01.jsonl").read_text().splitlines()]
    assert [r["item"] for r in records] == ["fresh"]
    excluded = [json.loads(line) for line in (out.parent / "excluded_scope.jsonl").read_text().splitlines()]
    assert {r["item"]: r["reason"] for r in excluded} == {"new-dev": "dev document", "old-test": "v1.0 lineage"}
    assert result.read_bytes() == before


def test_qcheck_records_actual_writer_instead_of_attributing_codex_to_claude(tmp_path, monkeypatch):
    out = tmp_path / "writer/packs"
    out.mkdir(parents=True)
    (out / "pack_01.jsonl").write_text(json.dumps({"item": "p", "nhom": "T2"}) + "\n")
    (out.parent / "HUONG_DAN.md").write_text("Fixed question prompt")
    answers = tmp_path / "answers.jsonl"
    question = "Một công ty cần trả bao nhiêu tiền khi xin làm thủ tục này?"
    answers.write_text(json.dumps({"item": "p", "question": question}) + "\n")
    rows = {"p": [{"lineage_id": "p", "group": "T2", "answer": "Phí đăng ký là 30 nghìn đồng.",
                    "target": {"document_title": "Phí đăng ký", "lead_in": ""}}]}
    monkeypatch.setattr("test2_packs.lineage_rows", lambda data, ids: rows)
    dest = tmp_path / "checked.jsonl"
    qcheck(out, [answers], tmp_path, "Codex (model identity unavailable)", dest, provider="codex")
    row = json.loads(dest.read_text())
    assert row["question"] == question and row["provider"] == "codex"
    assert row["model"] == "Codex (model identity unavailable)"


def test_pending_keeps_old_draw_and_prompt_but_omits_done_calibration_and_dev(tmp_path, monkeypatch):
    data = tmp_path / "data"
    published_fixture(data)
    old = tmp_path / "old/packs"
    old.mkdir(parents=True)
    for name in ("AGENTS.md", "CLAUDE.md", "HUONG_DAN.md"):
        (old.parent / name).write_text("EXACT ORIGINAL INSTRUCTION BYTES\n")
    ids = ["done", "calibration", "dev-new", "fresh-b", "fresh-a"]
    (old / "pack_01.jsonl").write_text("".join(json.dumps({"item": i}) + "\n" for i in ids))
    key = tmp_path / "key.tsv"
    key.write_text("item\tvai_tro\n" + "".join(
        f"{i}\t{'hieu_chuan' if i == 'calibration' else 'ung_vien'}\n" for i in ids))
    result = tmp_path / "result.tsv"
    result.write_text("item\tquyet_dinh\n" + "done\tgiu\n")
    monkeypatch.setattr("test2_packs.lineage_rows", lambda data, wanted: {
        i: [{"target": {"document_id": "doc-dev-t1" if i == "dev-new" else "doc-fresh"}}] for i in wanted})
    before = result.read_bytes()
    out = tmp_path / "resume/packs"
    assert pending(out, old, [result], data, key) == ["fresh-b", "fresh-a"]
    assert (out.parent / "HUONG_DAN.md").read_bytes() == (old.parent / "HUONG_DAN.md").read_bytes()
    assert "calibration" not in (out / "pack_01.jsonl").read_text()
    assert result.read_bytes() == before
    with pytest.raises(FileExistsError):
        pending(out, old, [result], data, key)


def test_inventory_draw_excludes_old_attempts_and_is_order_independent(tmp_path):
    from test2_packs import inventory_draw
    inventory = tmp_path / 'pool.tsv'
    inventory.write_text('lineage\ttầng\ttrạng thái\tnguồn\n'
                         'a\tT2\tunfiltered\tx\n'
                         'b\tT2\tquestion_attempted_rejected_or_pending\tx\n'
                         'c\tT2\tunfiltered\tx\n'
                         'd\tT2\texcluded:dev_document\tx\n')
    seed = 'vilextime-final-0511'
    picked = inventory_draw(inventory, {'T2': ['a', 'b', 'c', 'd']}, {'T2': 2}, seed)
    assert set(picked) == {'a', 'c'}
    assert inventory_draw(inventory, {'T2': ['d', 'c', 'b', 'a']}, {'T2': 2}, seed) == picked
    with pytest.raises(ValueError, match='chỉ còn 2'):
        inventory_draw(inventory, {'T2': ['a', 'b', 'c', 'd']}, {'T2': 3}, seed)
    with pytest.raises(ValueError, match='quota'):
        inventory_draw(inventory, {}, {'invented': 1}, seed)


def test_inventory_build_refuses_overwrite_and_private_inside_packs(tmp_path):
    from test2_packs import build
    out, private = tmp_path / 'packs', tmp_path / 'private'
    kwargs = dict(inventory=tmp_path / 'pool.tsv', quotas={}, private_dir=private)
    with pytest.raises(ValueError, match='tách khỏi'):
        build(out, tmp_path, **{**kwargs, 'private_dir': out / 'private'})
    out.mkdir()
    with pytest.raises(FileExistsError):
        build(out, tmp_path, **kwargs)


def test_pack_size_forty_bounds_worker_input(tmp_path):
    from test2_packs import write_packs
    out = tmp_path / 'packs'
    out.mkdir()
    write_packs(out, [{'item': str(i)} for i in range(81)], 40)
    assert [len(p.read_text().splitlines()) for p in sorted(out.glob('*.jsonl'))] == [40, 40, 1]


def test_hint_version_lookup_uses_provision_index_without_changing_rows():
    import sqlite3
    from test2_packs import HintConnection
    db = sqlite3.connect(':memory:')
    db.executescript('CREATE TABLE units (layer TEXT, provision_id TEXT, ordinal INTEGER, '
                     'local_from TEXT, local_to TEXT, text TEXT); '
                     'CREATE INDEX units_layer ON units(layer); '
                     'CREATE INDEX units_provision ON units(provision_id);')
    db.executemany('INSERT INTO units VALUES (?,?,?,?,?,?)', [
        ('version', 'p', 2, '2021', None, 'new'),
        ('asis', 'p', None, None, None, 'base'),
        ('version', 'q', 1, '2020', None, 'other'),
        ('version', 'p', 1, '2020', '2021', 'old')])
    db.execute('PRAGMA query_only=ON')
    sql = "SELECT ordinal, local_from, local_to, text FROM units WHERE layer='version' AND provision_id=? ORDER BY ordinal"
    planned = HintConnection(db)
    assert planned.execute(sql, ('p',)).fetchall() == db.execute(sql, ('p',)).fetchall()
    assert any('units_provision' in r[3] for r in planned.execute('EXPLAIN QUERY PLAN ' + sql, ('p',)))


def test_hint_term_cache_preserves_counts_and_absent_terms():
    import sqlite3
    from test2_packs import HintConnection
    db = sqlite3.connect(':memory:')
    db.executescript("CREATE TABLE units (id TEXT); CREATE VIRTUAL TABLE words USING fts5(text);"
                     "CREATE VIRTUAL TABLE units_vocab USING fts5vocab(words, 'row');"
                     "INSERT INTO words VALUES ('alpha beta'); INSERT INTO words VALUES ('alpha gamma');")
    planned = HintConnection(db)
    sql = 'SELECT term, doc FROM units_vocab WHERE term IN (?,?,?)'
    first, second = ('alpha', 'beta', 'absent'), ('alpha', 'gamma', 'absent')
    assert dict(planned.execute(sql, first)) == dict(db.execute(sql, first))
    assert dict(planned.execute(sql, second)) == dict(db.execute(sql, second))
    assert planned.frequencies == {'alpha': 2, 'beta': 1, 'gamma': 1, 'absent': None}


def test_t1_pack_uses_only_base_t1_and_pack_rules_and_lineage_rows_reads_t1(tmp_path, monkeypatch):
    from test2_packs import lineage_rows
    g = tmp_path / "data/derived/vilextime"
    g.mkdir(parents=True)
    for name in ("T1", "T2", "T3", "T6"):
        (g / f"{name}.jsonl").write_text(json.dumps({"lineage_id": "a" if name == "T1" else "b", "as_of": "2020-01-01"}) + "\n")
    assert set(lineage_rows(tmp_path / "data", {"a", "b"})) == {"a", "b"}
    published_fixture(tmp_path / "data")
    rows = {"a": [{"lineage_id": "a", "group": "T1", "answer": "Phí 30 nghìn đồng.",
                   "target": {"document_id": "doc-new", "document_title": "Phí", "lead_in": ""}}]}
    monkeypatch.setattr("test2_packs.lineage_rows", lambda data, ids: rows)
    key = tmp_path / "key.tsv"; key.write_text("item\tnhom\tvai_tro\na\tT1\tung_vien\n")
    result = tmp_path / "result.tsv"; result.write_text("item\tquyet_dinh\tma\tcan_cu\tghi_chu\na\tgiu\t\t\t\n")
    out = tmp_path / "q/packs"
    qpack(out, [result], tmp_path / "data", key, None)
    guide = (out.parent / "HUONG_DAN.md").read_text()
    assert "# NHÓM T1" in guide and "# NHÓM T2" not in guide and "# NHÓM T6" not in guide
