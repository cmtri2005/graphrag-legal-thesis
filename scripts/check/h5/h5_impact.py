"""H5: đếm lỗi đồ thị và dòng benchmark bị ảnh hưởng. CHỈ ĐỌC. Chạy: PYTHONPATH=src .venv/bin/python <file>"""
import json, re, sqlite3, sys, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from h5_rows import load_rows, rd
C = collections.Counter
rows = load_rows()
print("== kích thước tập ==")
print(sorted(C(r[0] for r in rows).items()))
print("lineage:", {s: len({r[2] for r in rows if r[0] == s}) for s in sorted({r[0] for r in rows})})
ev = rd("data/derived/provision_events.jsonl")
db = sqlite3.connect("file:data/temporal.sqlite?mode=ro", uri=True)
by_lin = collections.defaultdict(list)
for r in rows: by_lin[r[2]].append(r)
by_doc = collections.defaultdict(list)
for r in rows: by_doc[r[5]].append(r)

def impact(label, hits):
    """hits: list of (event, affected_lineage_set | None, doc|None). Dòng bị ảnh hưởng: as_of >= effective_on."""
    seen = {}
    for e, lins, doc in hits:
        cand = [r for l in (lins or ()) for r in by_lin.get(l, ())] if lins else by_doc.get(doc, [])
        for r in cand:
            if r[3] >= e["effective_on"]:
                seen[(r[0], r[1])] = (r, e["effective_on"])
    tot = C(); ans = C(); lin = collections.defaultdict(set)
    for (s, _), (r, _) in seen.items():
        tot[s] += 1; ans[s] += bool(r[4]); lin[s].add(r[2])
    print(f"[{label}] dòng bị ảnh hưởng theo tập (tổng / đang có đáp án / lineage):")
    for s in sorted(tot): print(f"   {s:14s} {tot[s]:4d} / {ans[s]:4d} / {len(lin[s]):3d}")
    if not tot: print("   (không có)")
    return seen

# ---- E1: bãi bỏ một phần bị đóng cả nút ----
app = [e for e in ev if e["operation"] == "repeal" and e["status"] in ("auto_accepted", "verified") and e["locator"]]
print("\n== E1 repeal đã áp dụng:", len(app), "theo cấp locator:", dict(C(e["locator"][-1][0] for e in app)))
print("   repeal bị giữ vì partial_repeal:", sum(1 for e in ev if e["status_reason"] == "partial_repeal"))
g108 = [e for e in app if e["actor_number"] == "16/2026/TT-BXD" and e["document_number"] == "12/2017/TT-BXD"]
print("   E1a xác nhận (TT 16/2026 -> TT 12/2017):", len(g108), "sự kiện,", len({p for e in g108 for p in e["affected_provision_ids"]}), "nút bị đóng")
seen = impact("E1a", [(e, set(e["affected_provision_ids"]), None) for e in g108])
for k, (r, d) in sorted(seen.items()): print("      ", k[0], r[1][-50:], r[3], "answerable=", r[4])
loc = re.compile(r"(?i)^\W*(?:\d+[.)]\s*)?(?:(?:các|những)\s+)?(?:điều|khoản|điểm|chương|mục|tiểu mục|tiết|phần|phụ lục|[a-zđ]\))\b")
cand = [e for e in app if not re.search(r"(?i)bãi bỏ|hủy bỏ|\bbỏ\b", e["evidence"] or "") and not loc.search(e["evidence"] or "")]
print("   E1b ứng viên (evidence mất động từ 'bãi bỏ' và là mô tả, không bắt đầu bằng locator):", len(cand), "sự kiện,", len({e['evidence'] for e in cand}), "câu khác nhau")
seen_b = impact("E1b (bao gồm E1a)", [(e, set(e["affected_provision_ids"]), None) for e in cand])
for k, (r, d) in sorted(seen_b.items()): print("      ", k[0], r[1][-50:], r[3], "answerable=", r[4])

# ---- E2: repeal/replace cấp văn bản không áp dụng, văn bản đích còn effective_to rỗng ----
docs = {i: (n, t, s) for i, n, t, s in db.execute("select id,number,effective_to,raw_status_code from documents")}
wd = re.compile(r"(?i)^\W*(?:thông tư(?: liên tịch)?|nghị định|luật|pháp lệnh|quyết định|nghị quyết|bộ luật)\s+(?:số\s+)?\d")
ds = [e for e in ev if e["code"] == "resolved_document" and e["operation"] in ("repeal", "replace") and e["status_reason"] == "document_scope"]
print("\n== E2 sự kiện cấp văn bản (repeal+replace, document_scope):", len(ds))
whole = [e for e in ds if wd.search(e["evidence"] or "") and e["effective_on"]]
print("   evidence mở bằng tên văn bản (nhiều khả năng cả văn bản):", len(whole), "| còn lại (danh sách điều/khoản, chưa trích):", len(ds) - len(whole))
kind = C()
gap = []
for e in whole:
    t = docs.get(e["target_document_id"])
    if t is None: kind["đích không có trong sqlite"] += 1; continue
    if t[1] is None: kind["effective_to rỗng (HỞ)"] += 1; gap.append(e)
    elif t[1] == e["effective_on"]: kind["effective_to = ngày sự kiện (khớp)"] += 1
    elif t[1] > e["effective_on"]: kind["effective_to SAU ngày sự kiện"] += 1; gap.append(e)
    else: kind["effective_to TRƯỚC ngày sự kiện"] += 1
print("  ", dict(kind))
gdocs = {e["target_document_id"] for e in gap}
print("   văn bản đích bị hở:", len(gdocs), "| trạng thái vbpl thô của chúng:", dict(C(docs[d][2] for d in gdocs)))
# ngày sớm nhất mỗi văn bản
first = {}
for e in gap:
    if e["target_document_id"] not in first or e["effective_on"] < first[e["target_document_id"]]["effective_on"]: first[e["target_document_id"]] = e
seen2 = impact("E2", [(e, None, d) for d, e in first.items()])
print("   riêng document:31760:", sorted((r[0], r[3], r[4], r[1][-45:]) for (k, (r, d)) in seen2.items() if r[5] == "document:31760"))
print("   ví dụ 8 hở:", [(docs[d][0], first[d]["actor_number"], first[d]["effective_on"], docs[d][2]) for d in list(first)[:8]])

# ---- E3: sqlite cũ so với versions.jsonl ----
sq = {i: t for i, t in db.execute("select id,valid_to from versions")}
stale = set(); miss = 0; tot = 0
for l in open("data/derived/versions.jsonl", encoding="utf-8"):
    h = l[:80]; vid = h.split('"id":"')[1].split('"')[0]; tot += 1
    if vid not in sq: miss += 1; continue
    if sq[vid] is None and '"valid_to":null' not in l[:l.find('"effective_interval_count"')]: stale.add(vid)
print("\n== E3 sqlite cũ: versions.jsonl", tot, "| thiếu trong sqlite", miss, "| sqlite mở còn derived đã đóng", len(stale))
tot3 = C(); lin3 = collections.defaultdict(set)
for r in rows:
    if r[6] in stale: tot3[r[0]] += 1; lin3[r[0]].add(r[2])
print("   dòng có version_id nằm trong tập sqlite-mở/derived-đóng:", dict(tot3), {s: len(v) for s, v in lin3.items()})

# ---- E4: NĐ 209/2013 Đ3 k11 v1 thiếu câu ----
L = "provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0"
print("\n== E5 NĐ 209/2013 Đ3 k11:", dict(C(r[0] for r in by_lin.get(L, []))), sorted((r[0], r[3]) for r in by_lin.get(L, [])))

print("\n== chi tiết E2 ==")
for k, (r, d) in sorted(seen2.items()):
    e = first[r[5]]
    print(k[0], r[1][-60:], r[3], "answerable=", r[4], "| doc", docs[r[5]][0], docs[r[5]][2], "| sự kiện:", e["actor_number"], e["effective_on"], e["operation"], "|", (e["evidence"] or "")[:150].replace("\n", " "))
# E1c: cue mạnh cho bãi bỏ một phần khi evidence mất động từ
strong = re.compile(r"(?i)(^\W*(?:các\s+)?nội dung\s+(?:liên quan|sau|dưới đây|về)\b|gạch đầu dòng|cụm từ|[“\"][^”\"]{3,}[”\"]\s*(?:tại|ở)\b)")
c1 = [e for e in app if not re.search(r"(?i)bãi bỏ|hủy bỏ|\bbỏ\b", e["evidence"] or "") and strong.search(e["evidence"] or "")]
print("\n== E1c cue mạnh (nội dung liên quan/sau, gạch đầu dòng, cụm từ, cụm trích dẫn):", len(c1), "sự kiện; theo cấp:", dict(C(e['locator'][-1][0] for e in c1)))
print("   theo văn bản đích:", dict(C(e['document_number'] for e in c1).most_common(10)))
impact("E1c", [(e, set(e["affected_provision_ids"]), None) for e in c1])
