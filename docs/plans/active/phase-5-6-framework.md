# Execution Plan: Framework GraphRAG — Giai đoạn 5 + 6

Date: 2026-10-01

## Status

Active

## Outcome

Một pipeline duy nhất mà mọi đường cơ sở B1–B7+ và mọi ablation A1–A7 là **cùng
một đoạn code chạy với một cấu hình khác**, nhận `data/derived/vilextime/release.jsonl`
và sinh `predictions.jsonl` đúng hợp đồng của `scripts/eval/score_vilextime.py`.

Observable: `run_vilextime.py --system <tên> --split dev` → `score_vilextime.py`
in ra bảng metric. Khi bộ dữ liệu được gán nhãn xong, không dòng code nào đổi.

## Context

- Authority: [ADR 0001](../../decisions/0001-neo4j-milvus-la-kho-dan-xuat.md)
  (§3 method A, Milvus lọc → Neo4j xác nhận top-k), [ADR 0002](../../decisions/0002-pham-vi-neo-thoi-gian-va-du-lieu-dan-xuat.md)
  (chỉ QPPL trung ương được truy xuất theo t), [ADR 0003](../../decisions/0003-schema-bo-du-lieu-vilextime.md)
  (§7 chỉ `test` được chấm mặc định; dev chỉ để tinh chỉnh).
- Lý thuyết: `docs/graph_justification.md` §3 (Định nghĩa 1, Mệnh đề 1 — biểu
  diễn đủ), §6 (ba vai trò của đồ thị), §7 (H1–H4).
- Tiến độ: [master plan](master-plan.md) §6 (P5.*), §7 (P6.*), §8 (A1–A7).
- Đã có: corpus hai lớp `data/derived/corpus/`, release 2.481 dòng, scorer
  (P5.4/P5.5 ✅), lõi thời gian `src/vilexgraph/build/temporal/`, `llm.py`.
- Chưa có: toàn bộ phần truy xuất và sinh. Milvus chưa bao giờ giữ vector thật;
  volume Docker đã mất, graph phải nạp lại.

## Scope

In scope:

- P5.1–P5.3, P5.6–P5.13b (B1–B7+), P6.1–P6.6 (L4–L5), A1–A7 dưới dạng cờ.
- `src/vilexgraph/framework/` (7 module), `scripts/eval/{index_corpus,run_vilextime,judge_vilextime}.py`.

Out of scope:

- P6.7 giao diện chọn mốc t → Giai đoạn 9 cùng demo.
- Fine-tune model (master plan §14). Sửa scorer. Gán nhãn người (J6/J7).

## Approach

**Kết quả chính là thang đủ của biểu diễn.** Mệnh đề 1 nói ρ không đủ nếu
ρ(u) = ρ(u') mà valid(u,t) ≠ valid(u',t). Biến thành bốn điểm đo trên cùng một
retriever, cùng generator, cùng prompt, cùng k — chỉ đổi ρ:

| Tier | ρ(u) | Hệ | 
|---|---|---|
| 1 `none` | text | B2/B3/B4 |
| 2 `document` | text + ngày hiệu lực văn bản | **B7** (đối chứng chính) |
| 3 `version` | text + khoảng **cục bộ** của phiên bản | **B7+** |
| 4 `propagated` | text + khoảng giao với mọi tổ tiên, công thức (3) | **đề xuất** |

Thứ tự: P0 quyết định + đo · P1 harness + B1 (mốc sẵn sàng) · **P2 thang bốn
tier = bảng chính, không cần embedding** · P3 Verifier + abstention → RQ3 ·
P4 dense + B3/B4 · P5 𝓔_rel + B5/B6 + ablation + judge.

P1 và P2 không cần Docker: cả bốn tier phân giải được từ file corpus + SQLite.
Neo4j vào ở P3/P5 cho bước xác nhận top-k của ADR 0001 §3.

## Risks And Recovery

- **Lấy sai khoảng → tier 3 ≡ tier 4, và lỗi im lặng.**
  `effective_intervals_by_version` đã giao với cửa sổ văn bản *và* coverage mọi
  tổ tiên, nên `corpus/versions.jsonl.effective_intervals` là khoảng
  **propagated**. Khoảng **cục bộ** phải lấy từ chuỗi phiên bản
  (`VersionChain.local_at`, quyết định C5). Mitigation: test ca tổ tiên bị bãi
  bỏ, assert `local` → valid, `propagated` → invalid.
- Neo4j 4g + Milvus 4g > 7 GB RAM máy dev. Lúc index chỉ bật Milvus; lúc chạy
  chỉ cần Neo4j xác nhận top-20 nên heap nhỏ đủ.
- Milvus 2.4.15 không có BM25 native (có từ 2.5). Đo trước ở P0; fallback
  SQLite FTS5. ADR 0001 Follow-Up đã yêu cầu đúng phép kiểm này.
- LightRAG không index nổi 1,5M đơn vị (trích thực thể bằng LLM từng chunk).
  B5 chạy trên tập con, ghi rõ corpus bị thu hẹp.
- Vòng tuần hoàn gold (JUDGE N1): gold layer B sinh từ chính chuỗi L2–L3 mà
  tier 3/4 dùng. Framework phải đọc được cả hai cột gold (J7).
- Recovery: mọi index là dẫn xuất, xóa và dựng lại từ `data/` (ADR 0001 §2).

## Progress

- [ ] P0.1 ADR 0004 + amendment ADR 0001 ghi quyết định M4
- [ ] P0.2 nạp lại Neo4j, `verify_graph_stack.py` + parity 200/200 — **chưa cần cho P1/P2**
- [x] P0.3a engine BM25: **SQLite FTS5 đo được, chạy thật** trên 2.978.024 đơn vị, giữ dấu
      (`unicode61 remove_diacritics 0`), 0 dependency mới. Một bảng FTS hai cột (`ctx`,`body`)
      nên B2 (lọc cột + trọng số 0) và B2+ctx dùng chung một lần dựng.
      Milvus 2.4.15 trong compose **không có** hàm BM25 native (có từ 2.5) → chưa đo 2.5;
      Milvus vẫn là kho vector cho P4 theo ADR 0001.
- [ ] P0.3b đo lại RAM khi Milvus có vector thật (P4)
- [x] **P1 xong — mốc "sẵn sàng nhận dataset" đã đạt.** `rag/corpus.py`, `systems.py`,
      `generate.py`, `run_vilextime.py`. Chứng minh: `run_vilextime.py --system b1 --split dev`
      → `score_vilextime.py` in bảng metric (B1: F1 0,061 trên 5 dòng, TVER(ng) 1,000 vì
      không trích dẫn). Index: 2,6 GB, đếm khớp corpus manifest (17.307 VB · layer A
      1.503.700 · layer B 1.474.324 · 48.328 lệnh · 1.474.184 khoảng propagated).
- [ ] P2 `retrieve.py` lexical + `temporal.py` bốn tier xong; index BM25 dựng xong
      (2.978.024 đơn vị, các stage đều `done`). **Chưa chạy bảng chính** (b2ctx, b7, b7plus, proposed
      trên dev): b7/b7plus/proposed khai báo `dense=True` nên cần `--no-dense` cho tới khi P4 xong.
      Còn thiếu: đối chiếu tier `propagated` với `ValidityService` trên ≥200 cặp.
      11/10: đã đối chiếu, 485 cặp trên 135 văn bản đích của T6, 0 lệch (`runs/E0/`). Thang 5 nấc
      chạy chỉ truy xuất trên dev (`runs/E1_ladder/dev/`).
- [x] P3 `verify.py` (off|warn|reject, sinh lại 1 lần, abstain có nguyên nhân), nối vào
      `run_vilextime.py` (ghi `verification` từng dòng). 7 test. Với hệ đề xuất Verifier là
      no-op theo cấu trúc (retrieval và expansion đã dùng cùng tier) — báo cáo phải nói thẳng.
- [ ] P4 embedding + Milvus + B3/B4 — **chưa viết**: máy dev không GPU, 4 CPU, 7 GB RAM, chưa cài
      torch/numpy/pymilvus; còn phải chốt cách Milvus lọc 𝒰ₜ (ADR 0001 §3: ghi khoảng propagated vào
      Milvus, một dòng cho mỗi khoảng) và ngân sách RAM.
- [x] P5 (một phần) `graphx.py`: mở rộng 1 bước `part` (cha + con, B6) và `rel` (lệnh sửa/bãi bỏ
      nhắm vào điều khoản, B5/đề xuất), tôn trọng tier của hệ; đọc `temporal.sqlite` + index, không cần
      Neo4j. 5 test, chạy thật trên index. SEEDS=5, FANOUT=3 chưa tinh chỉnh (chỉ tinh trên dev).
- [x] P5.6 `scripts/eval/judge_vilextime.py` (judge / sample / agree): hàng unanswerable chấm theo
      luật của scorer, hàng còn lại do judge đọc, rào đón luôn sai. **Chưa hiệu chuẩn**: cần người
      gán nhãn 100 mẫu (`sample` → điền cột `human` → `agree`).
- [ ] P5 còn lại: A1–A7 chạy thật, B5 trên tập con (LightRAG), phân tích kết quả
- [x] 11/10 hạ tầng thực nghiệm: `runs/` kèm sổ chạy; runner ghi `<out>.run.json`; scorer có
      `wrong_version` (B5), `--ci` (bootstrap theo lineage), chấm nhiều file một lần kèm hiệu ghép cặp
      và p; `confirm_vilextime.py` tính XN1–XN9 cùng Holm theo ADR 0005 (Proposed); cache truy xuất bỏ
      ngày khỏi khóa khi hệ không lọc và không mở rộng; `check_tier_windows.py` (E0).

## Decisions

- 2026-10-11: **Thang 5 nấc** `b2ctx → b7 → b7v → b7plus → b7pp` (K-07, MASTER_RESEARCH_GUIDE §7.4):
  trên truy xuất từ vựng, hai nấc liền nhau khác đúng một trường; `proposed` = `b7pp` cộng mở rộng và
  Verifier. `b7v` tách lời văn đã hợp nhất khỏi cửa sổ phiên bản, `b7pp` tách lan truyền khỏi
  thành phần trực tuyến.
- 2026-10-11: **Cột kết quả chính và LLM giám khảo không thuộc họ Claude và không thuộc
  họ DeepSeek** (CMT, ADR 0004 §3). DeepSeek viết 225/653 lineage câu hỏi, gần như cả H3
  (144/150), nên dùng nó làm thí sinh chính sẽ biến thiên lệch "tự viết, tự trả lời"
  thành khác biệt giữa các nhóm. Hai họ này chỉ chạy ở bảng phụ, tách theo `question_source`.
- 2026-10-02: **Verifier: cấu hình chính là `reject` với một lần sinh lại; A3 là `off`** (CMT, ADR 0004 §5).
  Abstain trả `answerable=True` với câu trả lời rỗng + nguyên nhân trong `verification`, không bao giờ
  `answerable=False` (ADR 0003 §3). `graphx.expand` áp tier của hệ lên cả láng giềng (công thức 4),
  nên Verifier chỉ là lưới an toàn.
- 2026-10-02: **Embedding: cài đặt thường, có thể embed local** (CMT). Chưa chọn model; xem ADR 0004 §4.

- 2026-10-01: **Quyết định M4 (đến sớm 2 tháng) — đồ thị tạo ra biểu diễn.**
  Giá trị của đồ thị nằm ở việc kiến tạo 𝒰ₜ ở tầng offline (L2 + L3), không ở
  việc duyệt nó lúc truy vấn. B7+ không phải baseline không-đồ-thị; nó là hệ đề
  xuất khi tháo phần đồ thị online. Đối chứng chính chuyển thành B7 (siêu dữ
  liệu cấp văn bản). Bằng chứng — năm phép đo trên release.jsonl + corpus:

  | # | Phép đo | Kết quả |
  |---|---|---|
  | 1 | câu hỏi T2 khác nhau giữa hai mốc? | 200/200 lineage giống từng byte → độ liên quan là hằng số, chỉ `t` phân biệt |
  | 2 | gold có phải lời văn như công bố? | ordinal 1→1.326, 2→720, 3→134, 4→8, abstain→293; **862 dòng gold ≠ lời văn gốc** |
  | 3 | bề mặt vế đệ quy (3) | ancestor-repeal 48 dòng toàn bộ, **24 trên bảng chính, 24 lineage** |
  | 4 | bề mặt bao đóng (2) | 974 dòng có lệnh sửa đổi làm bằng chứng; **970/974 văn bản tác động vẫn còn hiệu lực tại `as_of`** |
  | 5 | ngữ cảnh cấu trúc biến thiên theo t? | nút mang ngữ cảnh có >1 phiên bản: **1.397/265.635 = 0,53%**; Chương/Mục 7/41.648 |

  Số nền: độ phủ token câu hỏi bởi text của chính đơn vị 0,555 → cộng tổ tiên
  và tiêu đề văn bản 0,740 (+33,2%); tiêu đề góp token ở 75,1% dòng. Duplication
  layer A: 1.455.372 đơn vị / 1.247.953 text phân biệt; 79.850 text xuất hiện ở
  ≥2 văn bản khác nhau. Probe `nearest` đã đạt 0,772 T2 / 0,713 T3.

- 2026-10-01: **H3 không được kiểm vì không đủ lực thống kê** — 24 dòng /
  24 lineage, và CI bootstrap-theo-lineage (datasheet §4) trên 24 lineage là vô
  nghĩa. Báo số và nói thẳng, không chạy phép thử yếu rồi diễn giải.

- 2026-10-01: **Đường cơ sở được cấp ngữ cảnh cấu trúc.** Phép đo 5 cho thấy
  +0,185 là mẹo chunk-header phổ thông, không phải đóng góp của đồ thị. Thêm
  trục `context` (`none | static`); báo B2/B3/B4 ở cả hai dạng để không bị phản
  biện "baseline không dùng header".

- 2026-10-01: **Thang bốn tier lồng nhau, đã kiểm trên corpus thật.** `assert_monotone`
  chứng minh 𝒰ₜ(propagated) ⊆ 𝒰ₜ(version) ⊆ 𝒰ₜ(document) tại 2005/2015/2020/2024/2026 trên
  mẫu rải đều 5.000 đơn vị. Kích thước 𝒰ₜ trên toàn bộ 1.474.324 đơn vị layer B:

  | as_of | none | document | version | propagated |
  |---|---:|---:|---:|---:|
  | 2016-01-01 | 1.474.324 | 475.830 | 468.903 | 467.469 |
  | 2020-01-01 | 1.474.324 | 595.188 | 582.121 | 577.879 |
  | 2024-05-01 | 1.474.324 | 673.017 | 656.621 | 650.119 |
  | 2026-09-13 | 1.474.324 | 761.528 | 746.271 | 735.891 |

  Khoảng cục bộ khác khoảng propagated trên **790.025/1.595.823 phiên bản (49,5%)**, trong đó
  759.571 bị thu hẹp thật. Hai cột nguồn: `valid_from`/`valid_to` của
  `data/derived/versions.jsonl` (cục bộ) và `effective_intervals` của
  `corpus/versions.jsonl` (propagated).

- 2026-10-01: **`answerable=false` chỉ được sinh từ một khẳng định.** Khi chỉ có hai trạng
  thái, gpt-oss-120b dùng "HIỆU LỰC: không" để nói "tôi không biết" (TRẢ LỜI rỗng), và như
  vậy B1 sẽ được chấm **đúng** trên cả 293 dòng unanswerable vì một lý do sai hoàn toàn.
  Thêm trạng thái thứ ba "không rõ" → `answerable=true` với câu trả lời rỗng (bị chấm sai,
  đúng bản chất). Lý do là thứ benchmark đang đo (ADR 0003 §3).

- 2026-10-01: **Bảng kết quả chính không cần embedding.** Bốn tier dùng chung
  một retriever, biến thiên duy nhất là bộ lọc → chạy thang bằng BM25 là hợp lệ.
  Embedding 1,5M đơn vị rời khỏi đường găng; quy mô model thành A6.

## Validation

- Focused proof: `python3 -m pytest`; mỗi module mới có `tests/test_rag_*.py`.
  Test quan trọng nhất: (a) tier `local` ≠ tier `propagated` trên ca tổ tiên bị
  bãi bỏ; (b) runner không đọc trường gold nào ngoài `id`, `question`, `as_of`.
- Integration/end-to-end: `run_vilextime.py --system b1 --split dev` →
  `score_vilextime.py` in bảng metric.
- Trần oracle là bẫy tự động: `score_vilextime.py --probes` (oracle F1 ≈ 0,589,
  TV-Recall@1 = 1,0). Hệ nào vượt oracle là rò rỉ gold.
- Tier `propagated` đối chiếu `ValidityService` trên ≥200 cặp (nút, ngày), gồm
  ca bãi bỏ tổ tiên và nút không text (D12) — đúng kiểu C4/D5.
- Repository-required: `python3 -m pytest`, `scripts/check/verify_pipeline.py`.

## Result

Chưa hoàn thành.
