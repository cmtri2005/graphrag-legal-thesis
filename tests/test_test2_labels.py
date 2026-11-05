"""Approved card 4.0 validation, independent labels and agreement reporting."""
import io
import json

import pytest

import test2_labels as labels


@pytest.fixture
def record():
    return {"lineage_id": "provision:p", "group": "T6", "stratum": "T6 cấp trên", "batch": 1,
            "question": "Thời hạn gửi hồ sơ là bao lâu?",
            "rows": [{"as_of": "2020-01-01", "answer": "Thời hạn là 30 ngày.", "short_answer": "30 ngày"},
                     {"as_of": "2021-01-01", "answer": "", "short_answer": ""}],
            "sources": {"actors": [{"text": "Bãi bỏ Điều 2 của Nghị định này.", "source_url": "https://example.org/law"}]}}


@pytest.fixture
def valid():
    return {"q1": "dung", "q2": "co", "q3": "co", "q4": "khong",
            "quote": "Bãi bỏ Điều 2 của Nghị định này.", "search_log": "Đã đọc văn bản bãi bỏ và khoản anh em."}


def test_required_evidence_and_derived_verdict(record, valid):
    result, errors = labels.validate_label(record, {**valid, "verdict": "khong_dat"})
    assert errors == []
    assert result["verdict"] == "dat"
    assert "quote:" in " ".join(labels.validate_label(record, {**valid, "quote": ""})[1])
    assert "search_log:" in " ".join(labels.validate_label(record, {**valid, "search_log": ""})[1])
    outside, errors = labels.validate_label(record, {**valid, "quote": "Câu trích từ phần khác của bản gốc."})
    assert not errors and outside["quote_in_provided_sources"] is False
    # Only whitespace differs after copying a sentence from its source.
    assert not labels.validate_label(record, {**valid, "quote": "Bãi bỏ Điều 2\ncủa Nghị định này."})[1]


def test_reasons_are_per_question_and_adverse_answer(record, valid):
    bad = {**valid, "q2": "khong", "q2_reason": "relocated"}
    assert "Q2:" in " ".join(labels.validate_label(record, bad)[1])
    accepted = {**valid, "q2": "khong", "q2_reason": "cosmetic_only"}
    result, errors = labels.validate_label(record, accepted)
    assert not errors and result["verdict"] == "khong_dat"
    assert "Q1:" in " ".join(labels.validate_label(record, {**valid, "q1_reason": "gold_wrong"})[1])
    unclear = {**valid, "q4": "khong_chac", "q4_reason": "relocation_unclear"}
    assert "note:" in " ".join(labels.validate_label(record, unclear)[1])
    assert not labels.validate_label(record, {**unclear, "note": "Nghi ở Điều 3 văn bản mới."})[1]


def test_save_and_state_read_only_own_labels(tmp_path, record, valid):
    a, b = tmp_path / "test2_A.tsv", tmp_path / "test2_B.tsv"
    assert labels.save_label(a, [record], "A", "absent", valid)["errors"]
    assert not a.exists()
    assert not labels.save_label(a, [record], "A", record["lineage_id"], valid)["errors"]
    b.write_text("THIS MUST NOT BE READ", encoding="utf-8")
    h = labels.handler([record], a, "A").__new__(labels.handler([record], a, "A"))
    h.path = "/api/state"
    got = []
    h.send = lambda value, *args, **kwargs: got.append(value)
    h.do_GET()
    assert got[0]["who"] == "A"
    assert got[0]["questions"][0]["label"]["labeler"] == "A"
    assert "THIS MUST NOT" not in json.dumps(got)
    # Query strings cannot switch the selected person's sheet.
    h.path = "/api/state?who=B"
    h.do_GET()
    assert got[-1]["errors"]


def test_http_rejects_foreign_origin_and_unknown_routes(tmp_path, record, valid):
    cls = labels.handler([record], tmp_path / "test2_A.tsv", "A")
    h = cls.__new__(cls)
    h.path = "/api/save"
    body = json.dumps({"lineage_id": record["lineage_id"], "label": valid}).encode()
    h.rfile = io.BytesIO(body)
    h.headers = {"Origin": "https://foreign.invalid", "Host": "127.0.0.1:8775", "Content-Length": str(len(body))}
    got = []
    h.send = lambda value, *args, **kwargs: got.append((value, args))
    h.do_POST()
    assert got[0][1] == (403,)
    assert not (tmp_path / "test2_A.tsv").exists()
    h.headers.pop("Origin")
    h.do_POST()
    assert not got[-1][0]["errors"]
    assert labels.read_labels(tmp_path / "test2_A.tsv")[record["lineage_id"]]["verdict"] == "dat"
    override = json.dumps({"who": "B", "lineage_id": record["lineage_id"], "label": valid}).encode()
    h.rfile = io.BytesIO(override)
    h.headers["Content-Length"] = str(len(override))
    h.do_POST()
    assert got[-1][1] == (403,)
    assert not (tmp_path / "test2_B.tsv").exists()


def test_raw_text_escaped_before_diff_and_short_answer_marks():
    marked = labels.marked_text("<script>30 ngày", "<script>20 ngày", "30 ngày")
    assert "<script>" not in marked
    assert "&lt;script&gt;" in marked
    assert "<mark>" in marked and "<strong>" in marked


def test_every_short_span_is_highlighted_and_lead_in_and_repeal_shown(tmp_path, record):
    text = "Phạt tiền 30 ngày, nghỉ 30 ngày, rồi nộp hồ sơ."
    marked = labels.marked_text(text, "", "30 ngày … nộp hồ sơ")
    assert marked.count("<strong>") == 3
    # The accepted short-answer syntax allows spans taken from the parent's lead-in.
    record["rows"][0].update(target={"lead_in": "Phạt tiền từ 10 đến 20 triệu đồng."},
                             short_answer="20 triệu đồng … 30 ngày")
    record["rows"][1].update(answer=None, answerable=False)
    rows = labels.state([record], tmp_path / "empty.tsv", "A")["questions"][0]["rows"]
    assert "<strong>20 triệu đồng</strong>" in rows[0]["marked_lead_in"]
    assert "<strong>" in rows[0]["marked_answer"]
    assert rows[1]["answer_status"] == "no_answer"


def test_report_excludes_pilot_and_preserves_undefined_negative_agreement(record, valid):
    pilot = {**record, "lineage_id": "pilot", "batch": 0}
    row, errors = labels.validate_label(record, valid)
    row.update(labeler="A", guideline_version="4.0", worksheet_sha256=labels.worksheet_sha256(record))
    assert not errors
    a = {record["lineage_id"]: row, "pilot": row}
    b = {k: {**r, "labeler": "B"} for k, r in a.items()}
    report = labels.agreement_report([pilot, record], a, b)
    assert report["selected"] == report["paired"] == 1
    assert report["metrics"]["q1"]["ac1"] == 1
    assert report["metrics"]["q1"]["p_neg"] is None
    assert report["metrics"]["q1"]["gate"] == "not_met"
    assert report["metrics"]["q4"]["p_neg"] is None
    assert report["metrics"]["q4"]["gate"] == "not_met"
    limited = labels.agreement_report([pilot, record], a, b, limit=50)
    assert limited["sample_completeness"]["status"] == "insufficient_selected"
    assert limited["sample_completeness"]["paired"] == 1
    assert not limited["sample_completeness"]["requested_sample_available"]
    missing = labels.agreement_report([pilot, record], a, {})
    assert missing["sample_completeness"]["status"] == "missing_pairs"
    pilot_a = {**row, "worksheet_sha256": labels.worksheet_sha256(pilot)}
    assert labels.agreement_report([pilot, record], {**a, "pilot": pilot_a},
                                   {**b, "pilot": {**pilot_a, "labeler": "B"}}, batch=0)["selected"] == 1
    with pytest.raises(ValueError, match="không hợp lệ"):
        labels.agreement_report([record], {record["lineage_id"]: {**row, "verdict": "khong_dat"}},
                                {record["lineage_id"]: {**row, "labeler": "B"}})


def test_report_adverse_agreement_and_disagreements(record, valid):
    records = [{**record, "lineage_id": str(i)} for i in range(3)]
    good, _ = labels.validate_label(record, valid)
    bad, _ = labels.validate_label(record, {**valid, "q2": "khong", "q2_reason": "cosmetic_only"})
    a = {str(i): {**(bad if i < 2 else good), "labeler": "A", "guideline_version": "4.0",
                  "worksheet_sha256": labels.worksheet_sha256(records[i])} for i in range(3)}
    b = {str(i): {**(bad if i == 0 else good), "labeler": "B", "guideline_version": "4.0",
                  "worksheet_sha256": labels.worksheet_sha256(records[i])} for i in range(3)}
    report = labels.agreement_report(records, a, b)
    assert report["metrics"]["q2"]["p_neg"] == pytest.approx(2 / 3)
    assert report["metrics"]["verdict"]["p_neg"] == pytest.approx(2 / 3)
    assert report["disagreements"] == ["1"]
    assert labels.agreement_report(records, a, b, limit=1)["paired"] == 1


def test_q4_pneg_merges_co_and_khong_chac_but_ac1_keeps_three_levels(record, valid):
    records = [{**record, "lineage_id": str(i)} for i in range(10)]
    def own(who, q4_values):
        result = {}
        for r, value in zip(records, q4_values):
            body = {**valid, "q4": value, "note": "Chỗ nghi ở Điều 3."}
            if value != "khong":
                body["q4_reason"] = "superseded_by_other_norm" if value == "co" else "relocation_unclear"
            row, errors = labels.validate_label(r, body)
            assert not errors
            row.update(labeler=who, guideline_version="4.0", uid=who, seconds=120,
                       worksheet_sha256=labels.worksheet_sha256(r))
            result[r["lineage_id"]] = row
        return result
    va = ["co", "co"] + ["khong"] * 8
    vb = ["khong_chac", "co"] + ["khong"] * 8
    a, b = own("A", va), own("B", vb)
    report = labels.agreement_report(records, a, b)
    metric = report["metrics"]["q4"]
    assert metric["p_neg"] == 1
    assert metric["negative_category"] == ["co", "khong_chac"]
    assert metric["ac1"] == labels.gwet_ac1(va, vb) < 1
    assert metric["category_agreement"]["co"] == pytest.approx(2 / 3)
    assert metric["category_agreement"]["khong_chac"] == 0
    assert metric["gate"] == "pass"
    assert report["disagreements"] == ["0"]
    # All disagreement between the adverse levels still lowers three-level AC1.
    low = labels.agreement_report(records, own("A", ["co"] * 10), own("B", ["khong_chac"] * 10))
    assert low["metrics"]["q4"]["p_neg"] == 1
    assert low["metrics"]["q4"]["gate"] == "not_met"
    # Different favourable/adverse answers lower p_neg and fail the gate.
    split = labels.agreement_report(records, a, own("B", ["khong"] * 10))
    assert split["metrics"]["q4"]["p_neg"] == 0
    assert split["metrics"]["q4"]["gate"] == "not_met"


def test_worksheet_rejects_duplicates_and_missing_question(tmp_path, record):
    f = tmp_path / "worksheet.jsonl"
    f.write_text(json.dumps(record) + "\n" + json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="trùng"):
        labels.load_worksheet(f)
    f.write_text(json.dumps({**record, "question": None}), encoding="utf-8")
    with pytest.raises(ValueError, match="thiếu"):
        labels.load_worksheet(f)


def test_changed_question_rejects_stale_labels_on_read_save_and_report(tmp_path, record, valid):
    path = tmp_path / "test2_A.tsv"
    assert not labels.save_label(path, [record], "A", record["lineage_id"], valid)["errors"]
    changed = {**record, "question": "Cơ quan nào được phép tiếp nhận hồ sơ?"}
    with pytest.raises(ValueError, match="không khớp"):
        labels.state([changed], path, "A")
    result = labels.save_label(path, [changed], "A", changed["lineage_id"], valid)
    assert "không khớp" in " ".join(result["errors"])
    own = labels.read_labels(path)
    with pytest.raises(ValueError, match="không khớp"):
        labels.agreement_report([changed], own, {})
    assert own[record["lineage_id"]]["worksheet_sha256"] == labels.worksheet_sha256(record)


def test_pilot_deterministic_strata_and_release_only(tmp_path, record):
    import collections
    import hashlib
    quota = {'T2': 10, 'T2 gần giống': 5, 'T3': 5, 'T6 đích danh': 7, 'T6 cấp trên': 3}
    pool = [{**record, 'lineage_id': f'{tier}:{i}', 'stratum': tier,
             'group': 'T6' if tier.startswith('T6') else tier[:2],
             'review': {'verdict': 'secret'}} for tier, count in quota.items() for i in range(count + 2)]
    source, release, out = (tmp_path / n for n in ('source.jsonl', 'release.jsonl', 'pilot.jsonl'))
    source.write_text(''.join(json.dumps(r) + '\n' for r in pool))
    allowed = pool[1:]  # an eligible-looking question absent from the release must stay out
    release.write_text(''.join(json.dumps({'lineage_id': r['lineage_id']}) + '\n' for r in allowed))
    first = labels.pilot(source, release, out)
    before = out.read_bytes(), out.with_suffix('.manifest.json').read_bytes()
    assert labels.pilot(source, release, out) == first
    assert before == (out.read_bytes(), out.with_suffix('.manifest.json').read_bytes())
    rows = labels.load_worksheet(out)
    assert len(rows) == 30 and {r['batch'] for r in rows} == {0}
    assert collections.Counter(r['stratum'] for r in rows) == quota
    assert pool[0]['lineage_id'] not in {r['lineage_id'] for r in rows}
    assert first['output_sha256'] == hashlib.sha256(before[0]).hexdigest()
    assert first['inputs_sha256'][str(source)] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert 'secret' not in before[0].decode()


def test_web_and_worksheet_allowlist_excludes_all_advice(record):
    import re
    poisoned = {**record, 'review': {'verdict': 'SECRET_REVIEW'}, 'labeler': 'SECRET_PERSON',
                'question_source': {'note': 'SECRET_GENERATOR'}, 'system_result': 'SECRET_RESULT',
                'filter_result': 'SECRET_FILTER', 'note': 'SECRET_ADVICE'}
    poisoned['rows'] = [{**r, 'review': 'SECRET_ROW', 'question_source': 'SECRET_SOURCE',
                         'short_answer_source': 'SECRET_SHORT', 'source_missing': ['SECRET_MISSING'],
                         'target': {'lead_in': '<script>30 ngày', 'note': 'SECRET_TARGET'}} for r in record['rows']]
    poisoned['sources'] = {'base': {'passage': 'Văn bản nguyên gốc', 'note': 'SECRET_BASE'},
                           'actors': [{'passage': 'Tác động nguyên văn', 'review': 'SECRET_ACTOR'}]}
    clean = labels.unlabelled_record(poisoned)
    page = labels.web_page([poisoned])
    embedded = json.loads(re.search(r'const embedded=(.*?);\n', page)[1])
    for forbidden in ('review', 'verdict', 'labeler', 'question_source', 'short_answer_source',
                      'filter_result', 'system_result', 'source_missing', 'SECRET_'):
        assert forbidden not in json.dumps(embedded['questions']) and forbidden not in json.dumps(clean), f'C4 blind boundary leaked {forbidden}'
    assert 'SECRET_' not in page
    assert 'Văn bản nguyên gốc' in page and 'Tác động nguyên văn' in page
    assert r'\u003cstrong>' in page
    assert page.startswith('<title>Gán nhãn ViLexTime</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n<style>')
    assert not re.search(r'<(?:!doctype|html\b|head\b|body\b)', page, re.I)
    assert 'fetch(' not in page and '/api/' not in page
    assert not re.search(r'\b(?:alert|confirm|prompt)\s*\(', page)
    assert 'claude.use("db")' in page and 'claude.use("user")' in page
    assert ':root:not([data-theme="light"])' in page and ':root[data-theme="dark"]' in page
    assert 'minmax(min(100%,330px)' in page and 'focus-visible' in page
    assert 'top:env(safe-area-inset-top, 0px)' in page
    assert labels.doc_id('provision:p#x/%') == labels.doc_id('provision:p#x/%')
    assert re.fullmatch(r'[A-Za-z0-9_-]+', labels.doc_id('provision:p#x/%'))


def test_pull_validates_every_document_and_reports_bad_json(tmp_path, record, valid, monkeypatch):
    dump = tmp_path / 'dump'
    dump.mkdir()
    records = [{**record, 'lineage_id': f'p{i}'} for i in range(3)]
    def document(i, **overrides):
        r = records[i]
        return {'id': r['lineage_id'], 'lineage_id': r['lineage_id'], 'who': 'A', 'guideline': '4.0',
                'worksheet_sha256': labels.worksheet_sha256(r), 'label': valid,
                'uid': 'u_a', 'seconds': 42, **overrides}
    docs = [document(0), document(1, label={**valid, 'quote': ''}), document(2, seconds=-1)]
    for i, d in enumerate(docs):
        (dump / f'{i}.json').write_text(json.dumps({'data': d}))
    (dump / 'broken.json').write_text('{')
    calls, original = [], labels.save_label
    def spy(*args):
        calls.append(args[3])
        return original(*args)
    monkeypatch.setattr(labels, 'save_label', spy)
    path = tmp_path / 'test2_A.tsv'
    count, errors = labels.pull(path, dump, records, 'A')
    assert count == 1 and len(errors) == 3
    assert calls == ['p0', 'p1', 'p2']
    assert any('1.json' in e and 'quote:' in e for e in errors)
    assert any('2.json' in e and 'seconds:' in e for e in errors)
    assert any('broken.json' in e for e in errors)
    saved = labels.read_labels(path)
    assert set(saved) == {'p0'} and saved['p0']['uid'] == 'u_a' and float(saved['p0']['seconds']) == 42
    (dump / '0.json').write_text(json.dumps(document(0, uid='u_b')))
    assert any('uid:' in e for e in labels.pull(path, dump, records, 'A')[1])
    (dump / '0.json').write_text(json.dumps(document(0, worksheet_sha256='stale')))
    assert any('không khớp' in e for e in labels.pull(path, dump, records, 'A')[1])
    (dump / '0.json').write_text(json.dumps(document(0, who='B')))
    assert any('sai thẻ' in e for e in labels.pull(path, dump, records, 'A')[1])


def test_report_timing_uid_independence_and_batch(record, valid):
    records = [{**record, 'lineage_id': str(i)} for i in range(4)]
    good, _ = labels.validate_label(record, valid)
    a = {str(i): {**good, 'labeler': 'A', 'guideline_version': '4.0', 'uid': 'u_same',
                  'seconds': t, 'worksheet_sha256': labels.worksheet_sha256(records[i])}
         for i, t in enumerate([5, 29, 30, 180])}
    b = {k: {**r, 'labeler': 'B'} for k, r in a.items()}
    report = labels.agreement_report(records, a, b, batch=1)
    assert report['people']['A'] == {'questions': 4, 'median_seconds': 29.5, 'under_30_seconds': 2,
                                     'missing_seconds': 0, 'uid_count': 1, 'missing_uid': 0}
    assert report['people']['B']['uid_count'] == 1
    assert report['uid_A_differs_B'] is False and report['shared_uid_count'] == 1
    assert report['gate'] == 'not_met'
    for row in b.values():
        row['uid'] = 'u_b'
    assert labels.agreement_report(records, a, b)['uid_A_differs_B'] is True
    for row in b.values():
        row.pop('uid')
        row.pop('seconds')
    old = labels.agreement_report(records, a, b)
    assert old['people']['B']['median_seconds'] is None
    assert old['people']['B']['missing_uid'] == old['people']['B']['missing_seconds'] == 4
    assert not old['uid_A_differs_B']
    assert labels.agreement_report(records, a, b, batch=0)['people']['A']['questions'] == 0


# Minimal DOM/db doubles execute the actual generated page's script offline.
# The capability double deliberately exposes ONLY claude.use(), per the host contract.
NODE_DOM = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const nodes=new Map(), events={}, store=new Map();let now=0,reads=[],writes=[],database={},identity='u_a',available=true;
class El {
 constructor(tag='div'){this.tag=tag;this.children=[];this.value='';this.textContent='';this.hidden=false;this.checked=false;this.disabled=false;const set=new Set();this.classList={add:x=>set.add(x),remove:x=>set.delete(x),contains:x=>set.has(x),toggle:(x,b)=>b?set.add(x):set.delete(x)}}
 set id(x){this._id=x;nodes.set(x,this)}get id(){return this._id}
 append(...xs){this.children.push(...xs)}replaceChildren(...xs){this.children=xs}
 get firstChild(){return this.children[0]}get options(){return this.children}
 setAttribute(k,v){this[k]=v}scrollIntoView(){}
}
const document={hidden:false,getElementById:id=>{if(!nodes.has(id)){const e=new El();e.id=id}return nodes.get(id)},
 createElement:tag=>new El(tag),createTextNode:t=>({textContent:t}),addEventListener:(k,fn)=>events[k]=fn,
 querySelector:s=>{const name=s.match(/name="(.*?)"/)[1];return [...nodes.values()].find(e=>e.name===name&&e.checked)}};
const db={collection:name=>{reads.push(name);return {get:async()=>({docs:Object.values(database[name]||{}).map(d=>({data:()=>d}))}),doc:id=>({get:async()=>({exists:!!database[name]?.[id],data:()=>database[name]?.[id]}),set:async d=>{writes.push({name,id,d});(database[name]||={})[id]=d}})}}};
const window={claude:{use:async name=>available?(name==='db'?db:{id:async()=>identity}):null},addEventListener:(k,fn)=>events[k]=fn};
const localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)};
const context=vm.createContext({document,window,localStorage,performance:{now:()=>now},setInterval:()=>{},URL,console});
vm.runInContext(SCRIPT,context);
const run=code=>vm.runInContext(code,context);
function choose(q,value){for(const e of nodes.values())if(e.name===q)e.checked=e.value===value;run(`reasonOptions('${q}')`)}
(async()=>{ TEST_BODY })().catch(e=>{console.error(e);process.exitCode=1});
'''


@pytest.fixture
def run_ui(tmp_path, record):
    import re
    import subprocess
    def execute(body, records=None):
        page = labels.web_page(records or [record])
        script = re.search(r'<script>\s*(.*?)</script>', page, re.S)[1]
        source = 'const SCRIPT=' + json.dumps(script) + ';\n' + NODE_DOM.replace('TEST_BODY', body)
        path = tmp_path / 'ui-test.cjs'
        path.write_text(source, encoding='utf-8')
        result = subprocess.run(['node', str(path)], capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stdout + result.stderr
    return execute


def test_web_uid_guard_null_capabilities_and_only_selected_collection(run_ui):
    run_ui(r'''
const r=run('state.questions[0]');database.gan_A={[r.doc_id]:{uid:'u_other',label:{quote:'PRIVATE_OTHER_LABEL'}}};
await run('openSheet("A")');assert.equal(run('ready'),false);assert.equal(run('blocked'),true);
assert.ok(nodes.get('identity-error').textContent.includes('sai tên'));
assert.ok(nodes.get('sheet').classList.contains('hide'));assert.equal(nodes.get('quote').value,'');
assert.deepEqual([...new Set(reads)],['gan_A']);
database={};available=false;await run('openSheet("B")');
nodes.get('quote').value='DRAFT_PRESERVED';run('changed("quote")');
await run('openSheet("B")');assert.equal(nodes.get('quote').value,'DRAFT_PRESERVED');
assert.equal(run('ready'),false);assert.ok(nodes.get('sync').textContent.includes('db'));
available=true;await run('openSheet("B")');assert.equal(run('ready'),true);
assert.equal(nodes.get('quote').value,'DRAFT_PRESERVED');
assert.ok(!nodes.get('quote').value.includes('PRIVATE_OTHER_LABEL'));
identity=null;await run('openSheet("B")');assert.equal(run('ready'),false);
assert.equal(nodes.get('quote').value,'DRAFT_PRESERVED');
identity='u_a';localStorage.getItem=()=>{throw Error('storage denied')};localStorage.setItem=()=>{throw Error('storage denied')};
await run('openSheet("B")');assert.equal(run('ready'),true);
''')


def test_web_save_uid_timer_visibility_and_load_own_labels(run_ui):
    run_ui(r'''
await run('openSheet("A")');const r=run('state.questions[0]');
choose('q1','dung');choose('q2','co');choose('q3','co');choose('q4','khong');
nodes.get('quote').value='Bãi bỏ Điều 2 của Nghị định này.';nodes.get('search_log').value='Đã đọc văn bản gốc';
run('changed("quote")');now=12000;document.hidden=true;events.visibilitychange();
now=72000;document.hidden=false;events.visibilitychange();now=80000;
await nodes.get('form').onsubmit({preventDefault(){}});
assert.equal(writes.length,1);assert.equal(writes[0].name,'gan_A');assert.equal(writes[0].d.uid,'u_a');
assert.equal(writes[0].d.seconds,20);assert.equal(writes[0].d.label.quote,'Bãi bỏ Điều 2 của Nghị định này.');
assert.equal(writes[0].id,r.doc_id);assert.ok(!('seconds' in writes[0].d.label));
run('answers={};sessions.A=answers');await run('openSheet("A")');
assert.equal(nodes.get('quote').value,'Bãi bỏ Điều 2 của Nghị định này.');
assert.ok(nodes.get('status').textContent.includes('1/1'));
now=85000;await nodes.get('form').onsubmit({preventDefault(){}});
assert.equal(writes.length,2);assert.equal(writes[1].d.seconds,25);
identity='u_b';await run('openSheet("A")');assert.equal(run('blocked'),true);assert.equal(writes.length,2);
''')


def test_web_missing_actor_passage_or_link_is_explicit(run_ui):
    run_ui(r'''
const warning="Chưa trích được đoạn này. Mở văn bản gốc theo tên.";
const text=e=>[e.textContent||'',...e.children.map(text)].join(' ');
for(const src of [
 {document:'53/2015/TT-BGTVT',passage:'',in_force:'Hiệu lực từ 2015',source_url:'https://example.org/law'},
 {document:'78/2026/TT-BTC',passage:'Đoạn sửa đổi'},
 {document:'Văn bản có đường dẫn hỏng',passage:'Đoạn sửa đổi',source_url:'javascript:void(0)'}
]){
 const box=run('sourceBlock('+JSON.stringify(src)+',"Văn bản tác động")');
 assert.ok(text(box).includes(warning));assert.ok(text(box).includes(src.document));
 if(src.passage)assert.ok(text(box).includes(src.passage));
}
const complete=run('sourceBlock({number:"Văn bản đầy đủ",passage:"Lời văn gốc",source_url:"https://example.org/law"},"Văn bản tác động")');
assert.ok(!text(complete).includes(warning));
''')


def test_web_guideline_renders_current_markdown_structure(record, run_ui):
    import re
    from pathlib import Path
    page = labels.web_page([record])
    embedded = json.loads(re.search(r'const embedded=(.*?);\n', page)[1])
    rendered = embedded['card_html']
    source = (Path(labels.__file__).resolve().parents[2] / 'docs/vilextime-annotation.md').read_text()
    assert len(re.findall(r'<h[1-6]>', rendered)) == len(re.findall(r'^#{1,6} ', source, re.M))
    assert rendered.count('<table>') == 3
    assert all(tag in rendered for tag in ('<ul>', '<ol>', '<strong>', '<th>', '<td>'))
    assert 'Phiên bản 4.0' in rendered and 'bảy yếu tố' in rendered
    assert '<pre id="card-text">' not in page
    run_ui(r'''
assert.equal(nodes.get('card-text').innerHTML,run('state.card_html'));
assert.ok(nodes.get('card-text').innerHTML.includes('<table>'));
document.getElementById('card').hidden=true;nodes.get('card-toggle').onclick();
assert.equal(nodes.get('card').hidden,false);assert.equal(nodes.get('card-toggle')['aria-expanded'],'true');
''')


def test_web_validation_matches_python_card_rules(run_ui, record, valid):
    cases = [valid, {**valid, 'quote': ''}, {**valid, 'search_log': ''},
             {**valid, 'q1_reason': 'other'}, {**valid, 'q2_reason': 'rename_only'},
             {**valid, 'q2': 'khong', 'q2_reason': 'relocated'},
             {**valid, 'q3': 'khong'}, {**valid, 'q1': 'unknown'}]
    for q, choices in labels.REASONS.items():
        for value, reasons in choices.items():
            for reason in reasons:
                base = {**valid, q: value, q + '_reason': reason}
                cases.extend([base, {**base, 'note': 'Ghi rõ chỗ mới hoặc ý thiếu'}])
    matrix = [{'value': v, 'valid': not labels.validate_label(record, v)[1]} for v in cases]
    run_ui('const cases=' + json.dumps(matrix) + ';for(const c of cases){assert.equal(run("Object.keys(validation(state.questions[0],"+JSON.stringify(c.value)+")).length===0"),c.valid,JSON.stringify(c.value))}')


def test_silver_stops_over_ten_percent_missing_sources(tmp_path, monkeypatch):
    import subprocess
    import test2_prepare as prepare
    data = tmp_path / 'data'
    pub = data / 'vilextime_dataset'
    pub.mkdir(parents=True)
    for name in ('vilextime.jsonl', 'vilextime_meta.jsonl'):
        (pub / name).write_text('')
    rows = [{'id': f'r{i}', 'lineage_id': f'l{i}', 'group': 'T2' if i < 137 else 'T3',
             'as_of_strategy': 'ranh_gioi', 'question': 'Câu hỏi?', 'version_id': f'v{i}',
             'answer': 'Đáp án ngắn'} for i in range(168)]
    source, release, out = (tmp_path / n for n in ('silver.jsonl', 'test2.jsonl', 'out.jsonl'))
    source.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    release.write_text('')
    raw = {r['lineage_id']: [{**r, 'target': {'document_id': 'non-dev'}}] for r in rows}
    monkeypatch.setattr(prepare, 'lineage_rows', lambda *args: raw)
    monkeypatch.setattr(prepare, 'published_scope', lambda *args: (set(), set()))
    def extract(command, **kwargs):
        from pathlib import Path
        Path(command[-1]).write_text('')
    monkeypatch.setattr(subprocess, 'run', extract)
    monkeypatch.setattr(prepare, 'source_links', lambda *args, **kwargs: None)
    def assembly(*args, **kwargs):
        assert kwargs == {'strict': False}
        return [], [{'lineage_id': f'l{i}', 'field': 'sources'} for i in range(17)]
    monkeypatch.setattr(prepare, 'prepare_records', assembly)
    with pytest.raises(ValueError, match='17/168.*>10%'):
        labels.silver_worksheet(data, source, release, out)
    assert not out.exists()
    manifest = json.loads(out.with_suffix('.manifest.json').read_text())
    assert manifest['status'] == 'stopped_missing_sources_over_10_percent'
    assert len(manifest['thieu']) == 17
