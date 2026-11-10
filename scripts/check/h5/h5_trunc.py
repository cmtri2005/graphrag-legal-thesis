"""E5: văn bản nút bị cắt khi data/provisions dùng align_by_marker (không nối đoạn tiếp nối). CHỈ ĐỌC.
Heuristic: nút có text == đúng một đoạn <p> và đoạn kế tiếp không gắn id, không phải đánh số/đầu đề => nghi thiếu câu."""
import json, re, sys, glob, os, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from h5_rows import load_rows
from vilexgraph.build.provisions.text import parse_paragraphs
MARK = re.compile(r"^(?:\d{1,3}\s*\.\s+\S|[a-zđ]\s*\)\s+\S|Điều\s|Chương\s|Mục\s|Phần\s|[IVXL]+\s*\.\s)", re.I)
rows = load_rows()
need = collections.defaultdict(set)
for r in rows: need[r[5]].add(r[2])
def check(doc_id):
    p = json.load(open(f"data/provisions/{doc_id}.json"))
    if p["method"] == "id": return p["method"], {}, 0, 0
    html = (json.load(open(f"data/raw/{doc_id}.json")).get("documentContent") or {}).get("content") or ""
    paras = parse_paragraphs(html); idx = {}
    for i, q in enumerate(paras): idx.setdefault(q.text, i)
    trunc = {}; total = 0
    for nid, n in p["nodes"].items():
        if n["level"] not in ("Clause", "Point"): continue
        total += 1
        i = idx.get(n["text"])
        if i is not None and i + 1 < len(paras):
            nx = paras[i + 1]
            if nx.node_id is None and nx.text and not MARK.match(nx.text) and len(nx.text) > 20: trunc[nid] = nx.text[:80]
    return p["method"], trunc, total, len(trunc)
# 1) toàn corpus (chỉ văn bản dùng marker)
tot = collections.Counter(); docs_with = 0
if "--corpus" in sys.argv:
    for f in sorted(glob.glob("data/provisions/*.json")):
        d = os.path.basename(f)[:-5]
        m, t, n, k = check(d); tot[m] += 1
        if m != "id": tot["nodes_Clause_Point"] += n; tot["nghi_cat"] += k; docs_with += bool(k)
    print("corpus:", dict(tot), "văn bản có nút nghi cắt:", docs_with)
# 2) dòng benchmark
hit = collections.defaultdict(set); hr = collections.Counter(); hl = collections.defaultdict(set)
for d, lins in need.items():
    doc_id = d.split(":")[1]
    if not os.path.exists(f"data/provisions/{doc_id}.json"): continue
    m, t, n, k = check(doc_id)
    for l in lins:
        if l.split(":")[1] in t: hit[l] = t[l.split(":")[1]]
for r in rows:
    if r[2] in hit: hr[r[0]] += 1; hl[r[0]].add(r[2])
print("lineage benchmark nghi bị cắt:", len(hit), "| dòng theo tập:", dict(hr), "| lineage theo tập:", {k: len(v) for k, v in hl.items()})
for l, s in list(hit.items())[:6]: print("  ", l, "|", s)
