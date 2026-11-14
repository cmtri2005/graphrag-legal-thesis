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
