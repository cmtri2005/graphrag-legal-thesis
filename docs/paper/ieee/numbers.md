# Nguồn của mọi con số trong `main.tex`

Paper IEEE (tiếng Anh), dựng: `latexmk -xelatex main.tex`. Số chép từ file chạy, không tính lại tay. Nhãn mức: **XN** = họ F1–F7 (ADR 0006), **TD** = thăm dò hậu nghiệm, **MT** = mô tả.

| Số trong paper | Nguồn |
|---|---|
| 17.333 văn bản; 1.455.372 / 53.991 / 1.477.089 đơn vị | `docs/thesis/chuong-3-kho-van-ban-va-do-thi.md` §3.2 (manifest corpus) |
| 58/60 sự kiện đúng, Wilson [88,6; 99,1] | chương 3 §3.5 |
| 5.762/7.201 (80,0%) trên 51 văn bản | chương 3 §3.5 |
| 3.238/8.046 (40,2%); 1.109/2.846 | `docs/reports/g2-recall-m2-20261109.md` |
| 199/156 lineage, 318/361 dòng, 295 có đáp án, T2 127/254, T3 6/18, T6 23/46, T1 43, t2_near 38 | `data/vilextime_final/README.md`; ADR 0006 §1 |
| AC1 AI–AI 0,608 trên 314 lineage | ADR 0006 §1; `docs/reports/g2-co-mau-dong-thuan-20261109.md` |
| Ví dụ phạt 25.000.000 / 50.000.000 VND, mốc 2020-02-16 / 2022-07-19 | `data/vilextime_final/vilextime.jsonl`, lineage `0297fec0-31a0-11f1-ad11-4f6eee776099` |
| Cấu hình hệ, generator, embedding, k, RRF 60 | ADR 0006 §2; `src/vilexgraph/framework/systems.py` |
| Bảng V, Hình 3 (Accuracy, KTC, TV-R@1, TVER, WV) — MT | `runs/final_g4_20261112/r1/results.md` |
| Bảng VI F1–F7 lần 1/lần 2 — XN | `runs/final_g4_20261112/r1/confirm.json`; `r2/results.md`; `compare_runs.json` |
| MDE F7 ≈ 0,185 | chương 6 §6.6.1 |
| Hình 4: TV-R@1 48, 71, 58, 105, 105 /295 | tính lại từ `runs/final_g4_20261112/retrieval/*.jsonl`, `runs/posthoc_g4_20261113/retrieval/b7v.jsonl` bằng `score_vilextime.row_scores` (khớp hiệu trong `attribution.json`) |
| b7v−b7 −0,044; b7plus−b7v +0,159 — TD | `runs/posthoc_g4_20261113/attribution.json` (`ladder`) |
| proposed2−b7plus +0,013 / +0,016; −b7pp +0,006 / 0,000; T6 +0,174 — TD | `attribution.json` (`pairs`); chương 6 §6.6.3 |
| bvnone 0,311, bvdate 0,409; WV 0,317→0,064; b7plus−bvdate +0,245 / +0,230 — TD | `runs/posthoc_g4_20261113/test/{r1,r2}/baselines.*`; `REFACTOR_PLAN.md` |
| Bãi bỏ: 11 khẳng định, 7 đúng, Wilson; b2ctx 36/29; oracle 22/23 | `attribution.json` (`repeal_claims.r1`); `docs/reports/research-audit-20261113.md` |
| Hình 5: 102/107, 64/81, 26/36, 8/20, 1/3, 4/48; 46 sai trong 247 — TD | `attribution.json` (`rank_accuracy.r1`); chương 6 §6.6.3 |
| Người chấm 96/100, Wilson, κ 0,910; bản đầu 95/100, κ 0,888; 2/34, 10/33, 23/33 | `runs/posthoc_g4_20261113/human_score/agreement.json`; chương 6 §6.6.5 |
| Gold mù 24/156 lineage, 53 dòng; F5 +0,189 | `runs/posthoc_g4_20261113/gold_subset/confirm_r1.txt` |
| 220/318 dòng ngoài bốn miền | `docs/reports/research-audit-20261113.md` |

Tài liệu tham khảo: `references.bib` (chép từ `references.bib` gốc đã xác minh, bỏ trường `checked`), thêm `holm1979` (OpenAlex: Scand. J. Stat. 6:65–70, DOI 10.2307/4615733) và `cormack2009rrf` (Crossref: SIGIR 2009, tr. 758–759), xác minh ngày 14/11/2026.

## Bổ sung P0-1 ngày 15/11/2026 (chỉ đọc điểm G4 có sẵn)

| Số mới trong paper | File, key, lần chạy |
|---|---|
| Hybrid, r1, TCS 0.071 [0.031, 0.117] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `b4.giua_khoang.all.tcs` và `b4.giua_khoang.all.ci95.tcs`; G4 r1 |
| Hybrid, r1, MRR 0.445 [0.378, 0.512] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `b4.giua_khoang.all.mrr` và `b4.giua_khoang.all.ci95.mrr`; G4 r1 |
| Hybrid, r2, TCS 0.047 [0.016, 0.087] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `b4.giua_khoang.all.tcs` và `b4.giua_khoang.all.ci95.tcs`; G4 r2 |
| Hybrid, r2, MRR 0.445 [0.378, 0.512] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `b4.giua_khoang.all.mrr` và `b4.giua_khoang.all.ci95.mrr`; G4 r2 |
| +VersionFilter, r1, TCS 0.654 [0.570, 0.736] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `b7plus.giua_khoang.all.tcs` và `b7plus.giua_khoang.all.ci95.tcs`; G4 r1 |
| +VersionFilter, r1, MRR 0.456 [0.394, 0.517] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `b7plus.giua_khoang.all.mrr` và `b7plus.giua_khoang.all.ci95.mrr`; G4 r1 |
| +VersionFilter, r2, TCS 0.646 [0.562, 0.727] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `b7plus.giua_khoang.all.tcs` và `b7plus.giua_khoang.all.ci95.tcs`; G4 r2 |
| +VersionFilter, r2, MRR 0.456 [0.394, 0.517] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `b7plus.giua_khoang.all.mrr` và `b7plus.giua_khoang.all.ci95.mrr`; G4 r2 |
| Full config., r1, TCS 0.661 [0.577, 0.744] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `proposed2.giua_khoang.all.tcs` và `proposed2.giua_khoang.all.ci95.tcs`; G4 r1 |
| Full config., r1, MRR 0.453 [0.391, 0.513] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `proposed2.giua_khoang.all.mrr` và `proposed2.giua_khoang.all.ci95.mrr`; G4 r1 |
| Full config., r2, TCS 0.646 [0.562, 0.728] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `proposed2.giua_khoang.all.tcs` và `proposed2.giua_khoang.all.ci95.tcs`; G4 r2 |
| Full config., r2, MRR 0.453 [0.391, 0.513] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `proposed2.giua_khoang.all.mrr` và `proposed2.giua_khoang.all.ci95.mrr`; G4 r2 |
| Oracle (in force), r1, TCS 0.961 [0.924, 0.992] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `oracle.giua_khoang.all.tcs` và `oracle.giua_khoang.all.ci95.tcs`; G4 r1 |
| Oracle (in force), r1, MRR 1.000 [1.000, 1.000] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `oracle.giua_khoang.all.mrr` và `oracle.giua_khoang.all.ci95.mrr`; G4 r1 |
| Oracle (in force), r2, TCS 0.969 [0.935, 0.992] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `oracle.giua_khoang.all.tcs` và `oracle.giua_khoang.all.ci95.tcs`; G4 r2 |
| Oracle (in force), r2, MRR 1.000 [1.000, 1.000] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `oracle.giua_khoang.all.mrr` và `oracle.giua_khoang.all.ci95.mrr`; G4 r2 |
| Oracle (current), r1, TCS 0.000 [0.000, 0.000] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `oracle_now.giua_khoang.all.tcs` và `oracle_now.giua_khoang.all.ci95.tcs`; G4 r1 |
| Oracle (current), r1, MRR 1.000 [1.000, 1.000] — MT | `runs/final_g4_20261112/r1/test/all.score.json` → `oracle_now.giua_khoang.all.mrr` và `oracle_now.giua_khoang.all.ci95.mrr`; G4 r1 |
| Oracle (current), r2, TCS 0.000 [0.000, 0.000] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `oracle_now.giua_khoang.all.tcs` và `oracle_now.giua_khoang.all.ci95.tcs`; G4 r2 |
| Oracle (current), r2, MRR 1.000 [1.000, 1.000] — MT | `runs/final_g4_20261112/r2/test/all.score.json` → `oracle_now.giua_khoang.all.mrr` và `oracle_now.giua_khoang.all.ci95.mrr`; G4 r2 |

## Ví dụ W3/W8 — ca đã lưu, rút gọn và dịch

- W3 giữ minh họa: id `vilextime:T2:provision:0297fec0-31a0-11f1-ad11-4f6eee776099:2020-02-16`.
  - `runs/final_g4_20261112/r1/test/b4.jsonl:42`; key `id`, `answer, answerable, retrieved; G4 r1`.
  - `data/vilextime_final/vilextime.jsonl:89`; key `id`, `question, answer, context, as_of, version_id, accepted_evidence`.
  - `data/vilextime_final/vilextime_meta.jsonl:89`; key `id`, `near_identical, repeal_mode, repealed_by, target, no_answer_reason`.
- W3 giữ minh họa: id `vilextime:T2:provision:0297fec0-31a0-11f1-ad11-4f6eee776099:2022-07-19`.
  - `runs/final_g4_20261112/r1/test/b4.jsonl:45`; key `id`, `answer, answerable, retrieved; G4 r1`.
  - `data/vilextime_final/vilextime.jsonl:90`; key `id`, `question, answer, context, as_of, version_id, accepted_evidence`.
  - `data/vilextime_final/vilextime_meta.jsonl:90`; key `id`, `near_identical, repeal_mode, repealed_by, target, no_answer_reason`.
- W8 gần giống; 20%, 2016-09-08: id `vilextime:T2:provision:0bd8196a-df3f-11f0-8933-5bedca54c5c8#k2:2016-09-08`.
  - `runs/final_g4_20261112/r1/test/b4.jsonl:54`; key `id`, `answer, answerable, retrieved; G4 r1`.
  - `data/vilextime_final/vilextime.jsonl:110`; key `id`, `question, answer, context, as_of, version_id, accepted_evidence`.
  - `data/vilextime_final/vilextime_meta.jsonl:110`; key `id`, `near_identical, repeal_mode, repealed_by, target, no_answer_reason`.
- W8 bãi bỏ qua cha; 2020-08-30: id `vilextime:T6:provision:834d699a-df54-11f0-9a69-b14ee0870a7b:2020-08-30`.
  - `runs/final_g4_20261112/r1/test/proposed2.jsonl:341`; key `id`, `answer, answerable, retrieved; G4 r1`.
  - `data/vilextime_final/vilextime.jsonl:682`; key `id`, `question, answer, context, as_of, version_id, accepted_evidence`.
  - `data/vilextime_final/vilextime_meta.jsonl:682`; key `id`, `near_identical, repeal_mode, repealed_by, target, no_answer_reason`.
- W8 gold trong prompt; 2020-06-29, hạng 6, báo cáo 6 tháng/hàng năm; gold trước 01/02 năm sau: id `vilextime:T2:provision:1bd29b3e-df57-11f0-90b9-2b5fe92f1dbd#k3#c:2020-06-29`.
  - `runs/final_g4_20261112/r1/test/proposed2.jsonl:64`; key `id`, `answer, answerable, retrieved; G4 r1`.
  - `data/vilextime_final/vilextime.jsonl:130`; key `id`, `question, answer, context, as_of, version_id, accepted_evidence`.
  - `data/vilextime_final/vilextime_meta.jsonl:130`; key `id`, `near_identical, repeal_mode, repealed_by, target, no_answer_reason`.

W3: Hybrid r1 mốc đầu trả chuỗi rỗng; mốc sau trả công thức 50% khác gold. Không có dự đoán 50 triệu sai mốc như hình. Cả hai dòng đầu ra được ghi rõ là minh họa. W8 rank 6 là vị trí 1-based của version_id trong retrieved, không chạy lại truy xuất/sinh/chấm.

W5: cột Gen-TV-R@1 dùng 318 dòng và danh sách khi sinh; Hình 4 giữ TV-R@1 lexical với 295 dòng có đáp án. Không thay số.

## Bổ sung LightRAG ngày 15/11/2026 (P1-2, thăm dò, chưa qua evidence-gate)

Amendment: `docs/decisions/0006-ke-hoach-phan-tich-bo-test-cuoi.md`, mục "Amendment 2026-11-15: LightRAG thật". Mọi số dưới là lát `all`, chế độ `giua_khoang`, key `<hệ>.giua_khoang.all.{accuracy,wrong_version,tcs}` và `.ci95`; hiệu ở key `"<a> − <b>".giua_khoang.all`.

| Số mới trong paper | File, lần chạy |
|---|---|
| Bảng `tab:lightrag`: Hybrid, LightRAG, Full config. (Acc, WV, TCS) — TD | `runs/lightrag_20261113/test/{r1,r2}/lightrag_vs_b4_p.score.json` (`b4`, `lightrag`, `proposed2`) |
| Bảng `tab:lightrag`: Hybrid+AmendHop, +VersionFilter — TD | `runs/lightrag_20261113/test/{r1,r2}/lightrag_vs_b5_b7plus.score.json` (`b5`, `b7plus`) |
| LightRAG − Hybrid +0,022 [−0,037; +0,080] / +0,060 [+0,003; +0,117] — TD | `lightrag_vs_b4_p.score.json` → `lightrag − b4` |
| LightRAG − AmendHop: KTC chứa 0 cả hai lần (+0,035 [−0,022; +0,091] / +0,044 [−0,015; +0,102]) — TD | `lightrag_vs_b5_b7plus.score.json` → `lightrag − b5` |
| Hiệu WV LightRAG − Hybrid chứa 0 (+0,064 [−0,004; +0,132] / +0,057 [−0,011; +0,125]) — TD | `lightrag_vs_b4_p.score.json` → `lightrag − b4.wrong_version` |
| Full − LightRAG +0,321 [+0,249; +0,392] / +0,308 [+0,235; +0,382] — TD | `lightrag_vs_b4_p.score.json` → `proposed2 − lightrag` |
| VersionFilter − LightRAG +0,308 [+0,235; +0,381] / +0,292 [+0,218; +0,368] — TD | `lightrag_vs_b5_b7plus.score.json` → `b7plus − lightrag` |
| 608 văn bản; Qwen2.5-14B-Instruct; chế độ `mix` | `runs/lightrag_20261113/intake.json` (`build_done`, `modes`) |
| Ngữ cảnh trung vị ~99.000 ký tự; hệ khác 12.000–13.000 | `intake.json` → `context_chars.median` = 99.267; amendment ADR 0006 |
| 119/361 trích nhãn đoạn nội bộ (= 361 − `format_ok` 242, cả hai lần) | `runs/lightrag_20261113/test/{r1,r2}/lightrag.run.json` |

## Bổ sung 16/11/2026: generator mở Qwen3.8-27B (thăm dò, amendment 16/11 (b))
| Số trong paper | Nguồn |
|---|---|
| Qwen: P−b4 +0,324 [+0,272; +0,376] / +0,330; P−b5 +0,333 / +0,340; WV −0,306 [−0,353; −0,258]; F7 +0,087 [0; 0,217] | `runs/qwen_chutes_20261116/test/pairs/`, `NOTE_ket_qua.md` (evidence-gate 16/11) |
| Qwen: b7plus−bvdate +0,085 [+0,041; +0,132] / +0,082 [+0,041; +0,127]; WV −0,038 [−0,064; −0,015]; TCS +0,126 [+0,062; +0,194] | như trên |
| Qwen: P−lightrag +0,119 [+0,050; +0,187]; oracle 0,884 | như trên; `test/r1/all.score.json` |
| Lệch Chutes–vLLM ≤ 0,02 trên dev | `runs/qwen_chutes_20261116/dev/` |
| 0,245 trong tóm tắt là của GPT-4o mini | `runs/posthoc_g4_20261113/test/r1/` |
