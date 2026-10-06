# ViLexTime 1,500 lineages (300 × 5 groups) by 16/11/2026 — repository feasibility dossier

Scope: read-only analysis of the repository at `/home/trica/UIT_Thesis/graphrag-legal-thesis` on 02/10/2026.
Sources are given as repo-relative paths (links are relative to this notes file). Numbers marked
**[computed]** were measured by me with read-only Python over the data files. The method is described in
the "How the numbers were computed" subsection of Q1. Everything else is quoted from repo documents.

Vocabulary: *lineage* = one provision + its version chain = one distinct question (the question has no date
in it, so it serves every `as_of`). *Boundary row* (`ranh_gioi`) = one (question, as_of) next to a version switch.
*Twin* (`giua_khoang`) = the same question asked mid-interval (the headline table). *After-expiry row*
(`sau_het_hieu_luc`) = asked after the target document ended (no answer).

---

## Q1. Supply per group: is 300 lineages reachable, from how many documents, and where are the bottlenecks?

### Takeaway
At 300 lineages per group, T1, T2, T4 and T6 have enough supply, with hundreds of distinct source documents
each. **T5 cannot reach 300.** Every T5 candidate in the corpus comes to 194 lineages, from 17 target documents
and 8 acting documents. Only 148 of them are clean "stated retroactive" candidates, and those come from 4 acting
documents. **T3 cannot reach 300 *substantive* chains either.** There are 386 chains with ≥3 versions (346 clean,
in 122 documents), but only ~249 have ≥2 non-cosmetic amendments by a liberal heuristic, and ~130 by a strict
one (73 documents). The strict figure matches the ~64% `group_mismatch` rate that the LLM pre-label pass reported.
T6 can reach 300 in both sub-modes, but the ancestor mode is held back by a hard-coded cap of 300 candidates in the
pool builder, not by the data.

### Cited Findings

**Current release (what already exists)**
- The release has 2,481 rows: 1,150 boundary rows (T1 251 · T2 400 · T3 199 · T4 150 · T5 38 · T6 112), 1,150 twins and 181 after-expiry rows. That is 666 lineages on 517 target documents (dev 131 / test 535 lineages) — [docs/vilextime-datasheet.md §8](../../docs/vilextime-datasheet.md); [docs/plans/active/phase-4-vilextime.md (J4)](../../docs/plans/active/phase-4-vilextime.md)
- **[computed]** Release lineages per group, from `data/derived/vilextime/release.jsonl`:

  | Group | Lineages | Boundary | Twin | After-expiry |
  |---|---:|---:|---:|---:|
  | T1 | 251 | 251 | 251 | 78 |
  | T2 | 200 | 400 | 400 | 61 |
  | T3 | 65 | 199 | 199 | 15 |
  | T4 | 75 | 150 | 150 | 20 |
  | T5 | 19 | 38 | 38 | 7 |
  | T6 | 56 | 112 | 112 | 0 |

  The distinct target documents per group in the release are T1 245 · T2 176 · T3 50 · T4 63 · T5 10 · T6 47.

**Candidate pool (`data/derived/vilextime_pool.jsonl`, 9,818 lineages, built 29/09)**
- The pool builder caps every group except T5 at `QUOTA × --per-group-cap` (default 10). That gives T1 2,500 · T2 4,000 · T3 2,000 · T4 1,500 · T6 1,000. T6 "ancestor" candidates are separately capped at `ANCESTOR_CAP = 300`, while 10,249 exist. So the pool is a **seeded sample** for T1/T2/T4/T6, and it is **exhaustive** for T3 (386 < 2,000) and for T5 — [scripts/pipeline/build_question_pool.py lines 55–61, 330–380](../../scripts/pipeline/build_question_pool.py)
- The builder assigns a provision to exactly one group, scarcest first: T5, then T3 → T6 → T4 → T2 → T1. A chain with ≥3 dated versions is always T3. A 2-version chain whose texts have difflib ratio ≥0.90 is T4, otherwise T2. A chain whose dates give identical answers is dropped — [build_question_pool.py `classify`, `flush`](../../scripts/pipeline/build_question_pool.py)
- The uncapped totals were measured 20/09, before the J3 rebuild: T1 1,435,086 · T2 10,194 · T3 331 · T4 5,390 · T6 2,218 (direct). T2 had 15,070 nodes with ≥2 versions in 1,442 documents. T4 had 5,149 pairs with similarity ≥0.9 — [phase-4 plan, "Đo trữ lượng ứng viên" + B2](../../docs/plans/active/phase-4-vilextime.md). The T6 ancestor supply is 10,249 provisions in 487 documents (28/09) — same plan, V1–V2 progress.
- **[computed]** Supply per group. "Clean" means no structural `flags` in `data/derived/vilextime/T*.jsonl` and not in `data/vilextime/dropped.jsonl`. The cap columns give how many lineages can be taken if each document contributes at most 2 or 3. The current sampler uses `PER_DOCUMENT = 2`.

  | Group | Pool lineages | Pool docs | Clean lineages | Clean docs | Cap @2/doc | Cap @3/doc | Top-10 docs share (clean) | 300 reachable? |
  |---|---:|---:|---:|---:|---:|---:|---:|---|
  | T1 | 2,500 (capped) | 1,896 | 1,975 | 1,553 | 1,851 | 1,929 | 56/1,975 (2.8%) | yes |
  | T2 | 3,956 (capped) | 1,064 | 3,619 | 1,019 | 1,680 | 2,131 | 280/3,619 (7.7%) | yes |
  | T3 | 386 (exhaustive) | 126 | 346 | 122 | 188 | 226 | 116/346 (33.5%) | only by taking ~all chains at ≥3/doc, and see substantive analysis below: **no** |
  | T4 | 1,482 (capped) | 578 | 1,313 | 543 | 784 | 921 | 183/1,313 (13.9%) | yes |
  | T5 | 194 (exhaustive) | 17 | 184 | 16 | 30 | 44 | 167/184 (90.8%) | **no** |
  | T6 all | 1,300 (capped) | 514 | 1,116 | 470 | 675 | 800 | 171/1,116 (15.3%) | yes |
  | T6 direct | 1,000 (capped) | — | 852 | 386 | 551 | — | — | yes |
  | T6 ancestor | 300 (capped) | — | 264 | 146 | 192 | — | — | not from the current pool (cap 300); yes if `ANCESTOR_CAP` is raised (10,249 exist) |

  Across the whole clean pool there are 2,628 distinct documents.
- **[computed, uncapped, on the current `versions.jsonl`]** I re-ran the builder's own logic (`classify`, `build_row`, `build_t5_row`, `repealed_by_ancestor` imported from `build_question_pool.py`, `--today 2026-09-20`, same eligibility and T5-first exclusion), with no caps and no writes. Structural flags are not applied here.

  | Group | Lineages | Docs | Cap @2/doc | Cap @3/doc |
  |---|---:|---:|---:|---:|
  | T1 | 1,434,735 | 17,091 | 34,080 | 50,373 |
  | T2 | 10,155 | 1,445 | 2,516 | 3,370 |
  | T3 | **386** | **126** | **199** | **240** |
  | T4 | 5,530 | 998 | 1,662 | 2,142 |
  | T6 direct | 2,213 | 663 | 1,014 | 1,250 |
  | T6 ancestor | **10,055** | **484** | — | — |
  | T5 | **194** | **17** | — | — |

  The T3 row confirms the pool is exhaustive for T3. The T6-ancestor provisions are, by `classify`, also T1 candidates (one version, no ending event of their own). In the real builder T1 is sampled down to 2,500, so almost all of them stay free for T6. With 484 documents, at most 2 per document allows up to 968 ancestor lineages. T5 splits into 154 `stated_retroactive`, 39 `guidance_in_sync` and 1 `correction`. Lineages dropped because their answers are identical at the asked dates: T4 1,947 and T3 72. 140 provisions have undated versions.
- **[computed]** Structural flags that remove lineages from the pool (lineage counts):

  | Group | `answer_in_children` | `not_a_provision` | `heading_only` | `cosmetic_change` | `untitled_ancestor` |
  |---|---:|---:|---:|---:|---:|
  | T1 | 483 | 50 | 30 | — | 6 |
  | T2 | 329 | 1 | — | — | — |
  | T3 | 20 | — | — | 6 | — |
  | T4 | 133 | — | — | 49 | — |
  | T5 | 9 | — | — | 1 | — |
  | T6 | 183 | — | — | 1 | 1 |

- **[computed]** Question-generation pass rate in `data/vilextime/questions.jsonl`, i.e. passed C2 `validate()` out of written. The extra passed lineages not used in the release (passed minus in release) are T1 12, T2 14, T3 19, T4 8, T5 11, T6 41.

  | Group | Passed / written | Rate | Rejection reasons |
  |---|---:|---:|---|
  | T1 | 263/338 | 78% | 65 `insufficient_context`, 10 `copies_the_answer` |
  | T2 | 214/260 | 82% | 28 `insufficient_context`, 18 `copies_the_answer` |
  | T3 | 84/85 | 99% | — |
  | T4 | 83/106 | 78% | — |
  | T5 | 30/33 | 91% | — |
  | T6 | 97/129 | 75% | 28 `insufficient_context` |

- **[computed]** 32 lineages were dropped after labelling (`dropped.jsonl`): T3 14 (8 `group_mismatch`, 3 `gold_wrong`, 2 `question_ambiguous`, 1 `other`), T1 8, T2 8, T4 2.
- About 7.3% of T2 lineages (18/247 read by hand) join two different provisions that share a number (L2 mis-join). No machine signal separates them, so they are caught only while writing questions — [phase-4 plan, 24/09](../../docs/plans/active/phase-4-vilextime.md)

**T3 (≥3 versions): substantive vs cosmetic amendments**
- **[computed]** In the pool, T3 has 386 chains in 126 documents: 369 chains of 3 versions, 16 of 4 and 1 of 5. The clean set has 346 chains (331×3, 14×4, 1×5) in 122 documents. Using all clean chains would give 1,054 boundary rows.
- **[computed]** I classified the 790 consecutive-version transitions of the 386 chains:
  - `format`: case or punctuation only — 6;
  - `org_rename`: every changed span is ≤12 tokens per side and an organisation or administrative keyword appears within 3 tokens of it (Bộ, Tổng cục, Cục, Sở, Ủy ban, huyện, xã, tỉnh, …) — 139;
  - `substantive`: everything else — 645.

  So 145/790 (**18.4%**) of transitions are cosmetic. Separately, 285/790 (36.1%) transitions have a character similarity ≥0.90, the T4 "near-identical" threshold.
- **[computed]** Chains with ≥2 substantive transitions:

  | Set | Liberal: `substantive` | Strict: `substantive` and similarity <0.90 |
  |---|---|---|
  | All 386 chains | 272 (117 docs; cap@2/doc 168; cap@3/doc 194) | 140 |
  | Clean 346 chains | **249** (112 docs; cap@2 159; cap@3 185) | **130** (73 docs; cap@2 99; cap@3 112) |
  | Release 65 chains | 50 | 27 |

  In the full pool, 30 chains have 0 substantive transitions and 84 have exactly 1. So 114/386 = **30%** of T3 candidates are cosmetic-only beyond one real change by the liberal heuristic, and 246/386 = **64%** by the strict one.
- **[computed]** On the 16 T3 lineages in the D4 cross-check set (`crosscheck_A.tsv`), 11/16 pass the liberal test and only 3/16 pass the strict one. The caller's reported 64% `group_mismatch` from the LLM pre-label pass therefore lies between my two bounds. I did not find that pass's output file in the repo; `crosscheck_A.tsv` and `crosscheck_B.tsv` still have 0/300 verdicts.
- **[computed]** The heuristic does **not** explain every `group_mismatch`. The 7 T3 lineages that model labels in `labels.tsv` mark `group_mismatch`, and the 8 T3 lineages dropped for `group_mismatch`, all have 2 substantive transitions. There the question touched only one of two real changes. Conversely, 11 of the 53 all-`dat` labelled T3 lineages have only 1 substantive transition. Text diffs give an upper bound. Whether a question separates every date is a property of the question.
- **[computed]** The actors behind `org_rename` transitions:

  | Actor | Rename transitions |
  |---|---:|
  | 286/2025/NĐ-CP | 20 |
  | 171/2024/NĐ-CP | 13 |
  | 10/2025/TT-BNNMT | 12 |
  | 15/2024/TT-BTC | 11 |
  | 12/2024/TT-BNNPTNT | 11 |
  | 39/2026/NĐ-CP | 8 |
  | 09/2025/TT-BXD | 7 |
  | 38/2025/TT-BCT | 6 |

  56/139 rename transitions come from acts effective in 2025, which fits the 2025 restructuring. 31/139 come from acts whose title matches "phân định thẩm quyền | phân quyền | phân cấp | sắp xếp | tổ chức bộ máy | chính quyền địa phương". Spot checks of `org_rename`: "Trạm Thú y → Cơ quan quản lý chuyên ngành thú y", "huyện → xã", "Cục Con nuôi → Bộ Tư pháp", "Hội đồng ↔ Chủ tịch Ủy ban". Spot checks of `substantive` with similarity ≥0.95 show the liberal class still contains near-cosmetic edits ("Bán → Buôn bán", "+ Việt Nam", typo fixes "hợp → họp", "Vụ → Cục"), so the liberal count is an over-estimate.
- The plan already flagged T3 as the binding risk. On 20/09 there were "321 chuỗi ≥ 3 phiên bản, trong 100 VB … 1,6×" for 200 rows. Its fallback, if T3 stays under 300 chains, is to lower T3 and move rows to T2 (Q4). T3 supply depends on L2 recall (62.2%) and on supplement and replace events, which are not applied: "BỔ SUNG 0%", "100% transition là `amend`" — [phase-4 plan Q4 + Risks](../../docs/plans/active/phase-4-vilextime.md); [JUDGE N4](../../docs/reports/JUDGE_DATASET.md)

**T5 (retroactive: effective date before signing date)**
- **[computed]** The pool has 194 T5 lineages. They come from 17 target documents and 8 acting documents:

  | Acting document | Kind | Retroactive window | Lineages |
  |---|---|---:|---:|
  | 119/2026/NĐ-CP | `stated_retroactive` | 92 days | 59 |
  | 65/2025/TT-BQP | `stated_retroactive` | 2 days | 55 |
  | 12/2015/NĐ-CP | `stated_retroactive` | 42 days | 37 |
  | 26/2015/TT-BTC | `guidance_in_sync` | 57 days | 31 |
  | 130/2016/TT-BTC | `guidance_in_sync` | 42 days | 8 |
  | 96/2002/QĐ-BTC | `stated_retroactive` | — | 2 |
  | 123/2003/QĐ-BTC | `stated_retroactive` | — | 1 |
  | 2714/QĐ-BTC | `correction` | — | 1 |

  Clean `stated_retroactive` candidates come to 148 lineages in 11 target documents from 4 acting documents. With at most 2 per document that is only 30 lineages, and 44 with 3. The release T5 has 19 lineages from 3 acting documents: 65/2025/TT-BQP 10, 12/2015/NĐ-CP 7, 119/2026/NĐ-CP 2.
- The legal adviser excluded corrections and guidance in sync. 12/2015/NĐ-CP "hướng dẫn Luật thuế sửa đổi mà tên không nêu số hiệu … luật sư xét". 97/2026/NĐ-CP and 80/2025/TT-NHNN turned out not to be retroactive and were removed 25/09 — [phase-4 plan 25/09](../../docs/plans/active/phase-4-vilextime.md). If 12/2015 is ruled out, at most ~111–148 clean T5 lineages remain (an inference from the counts above).
- The `LUẬT SƯ:` columns of all 8 rows in `data/review/t5_documents.tsv` are empty [computed]. The adviser has not yet ruled on any T5 document.
- T5 "chỉ ở mức minh họa": the 19 lineages come from 3 acting documents, and one of them does not state the retroactive date. Ten lineages have a 2-day window, so their mid-interval twin cannot sit mid-interval — [JUDGE N3, N4](../../docs/reports/JUDGE_DATASET.md); [datasheet §5](../../docs/vilextime-datasheet.md)
- Decision Q3 (20/09): T5 follows Art. 152 strictly. "Số câu T5 là số ca cố vấn xác nhận được, không đặt trước. Phần thiếu so với 50 chuyển sang T6 … Không nới định nghĩa T5 để lấp cho đủ số" — [phase-4 plan Decisions](../../docs/plans/active/phase-4-vilextime.md)

**T6 (Clause or Point ended while its document is in force)**
- **[computed]** The pool has 1,000 `direct` lineages, capped (852 clean in 386 documents), and 300 `ancestor` lineages, capped (264 clean in 146 documents). All 1,000 direct pool rows carry a non-empty `evidence` sentence. The release T6 has 44 direct and 12 ancestor lineages.
- **[computed]** `data/review/crosscheck_evidence.jsonl`, the output of the current evidence builder, has 300/300 rows (T2 50 · T3 50 · T4 50 · T5 38 · T6 112), and every row has an empty `missing` list. The "88 direct repeals without evidence" problem does not appear in the current file.
- Corpus-wide there are 14,157 units invalid only through an ancestor's repeal, against 6,001 units repealed directly (2.4×) — [paper/problem_statement.md, Bảng A rows 9–10](../../paper/problem_statement.md)

**How the numbers were computed (read-only)**
- Pool stats: I streamed `data/derived/vilextime_pool.jsonl`. I joined lineage `flags` from `data/derived/vilextime/T{1..6}.jsonl`, excluded `data/vilextime/dropped.jsonl`, joined `data/vilextime/questions.jsonl` (`rejected_reason`) and `release.jsonl`, and counted distinct `document_id`. The cap@k columns are Σ_doc min(k, lineages in doc).
- T3 classification: for each pool chain, `difflib.SequenceMatcher` over word and punctuation tokens of consecutive `versions[].text`, with the org-keyword rule above. The character ratio is `SequenceMatcher(None, a, b).ratio()`. Actor law ids and dates come from `derivation.transitions` in `T3.jsonl`, and actor titles from `data/temporal.sqlite` (opened read-only). Both scripts lived in the session scratchpad and wrote nothing into the repo.

### Inferences
- **T5 is infeasible at 300 (and at 250) under the Art. 152 definition the adviser imposed.** Every candidate in the corpus comes to 194, with 154 `stated_retroactive`. Even taking every lineage gives ≤148 clean, concentrated in 4 acting documents, so any statistic on T5 is effectively n≈3–4 documents. Reaching 300 would need either a broader definition, which Q3 forbids, or new documents.
- **T3 is infeasible at 300 if T3 must test ≥2 substantive amendments.** The realistic ceiling is ~130 strict and ~250 liberal. Before question-level `group_mismatch`, the per-document concentration is about 3 chains per document. Under the current `PER_DOCUMENT = 2`, the clean ceiling is 188 (all chains) or 159 (liberal).
- T6 ancestor is the most abundant "hard" phenomenon: 10,055 candidates in 484 documents (10,249 in 487 documents in the 28/09 count). At present only the cap in code (`ANCESTOR_CAP = 300`) holds it to 264 clean lineages.
- T1, T2 and T4 are limited by labelling time, not by supply.

### Gaps
- The uncapped recount does not apply structural flags. The clean share in the capped pool runs from 80% (T1) to 91% (T2), so the clean uncapped supply is roughly 0.8–0.9× the counts in the uncapped table. This is an extrapolation and was not measured.
- I could not locate the output of the "LLM pre-labelling pass on 300 rows" (64% T3 `group_mismatch`; 88 T6 direct without evidence) in the repo. `crosscheck_A.tsv` and `crosscheck_B.tsv` have 0 verdicts. Per the user's memory note, it is probably a `crosscheck_A.model.tsv` built outside the repo on Colab.
- The cosmetic/substantive split is a lexical heuristic I have not validated by hand. It over-counts substantive changes (see the spot checks).

---

## Q2. Which 5-group option best serves the paper and thesis claims?

### Takeaway
The submitted outline promises six groups with fixed roles. T1 is "Đối chứng", T2 is the core TCS group, T3 "Đo lợi ích của đồ thị", T4 citation trap, T5 "Trường hợp khó", T6 clause-level validity. The paper's argument (RQ1–RQ3, representation-sufficiency ladder I1–I3) leans hardest on T2 (TCS), T3 (I1/I3) and T6, especially the ancestor mode (I2 = formula (3), the propagated tier). It barely uses T5, and the paper explicitly puts retroactive *application* out of scope. Data supply rules out T5 at 300 under any option. The fact pattern favours an "other" option: keep T1 (smaller is fine) as the outline's control, keep T2/T4, cap T3 at what the data supports, grow T6 (with explicit direct/ancestor strata), and keep T5 as a small, separately reported illustrative set. A strict 5×300 has to drop or merge T5 and still cannot fill T3 with substantive chains.

### Cited Findings

**Outline (UIT-submitted `docs/DeCuongKLTN_23521635_23521643_UIT.docx`, text extracted from word/document.xml)**
- Bảng 1 lists six groups:

  | Group | Description | Role | Planned |
  |---|---|---|---:|
  | T1 | tra cứu một phiên bản | Đối chứng | 250 |
  | T2 | cặp tương phản | Nhóm cốt lõi | 400 (200 cặp) |
  | T3 | chuỗi A→B→C | Đo lợi ích của đồ thị | 200 |
  | T4 | bẫy thời gian, phiên bản cũ rất giống | Đo ảo giác trích dẫn | 150 |
  | T5 | "Hiệu lực trở về trước có lợi cho đối tượng áp dụng" | Trường hợp khó | 50 |
  | T6 | Hết hiệu lực một phần ở cấp khoản, điểm | Đánh giá hiệu lực ở cấp điều khoản | 100 |
  | Total | | | 1,150 |

  The objective is "khoảng 1.100–1.300 câu hỏi". The hypothesis reads: "mô hình hóa chuỗi phiên bản và hiệu lực ở cấp cấu trúc pháp lý sẽ cải thiện khả năng truy xuất đúng phiên bản so với chỉ lọc theo ngày hiệu lực ở cấp văn bản". The metrics are TVER, VCR and TCS ("cặp câu hỏi tương phản") — [docs/DeCuongKLTN_23521635_23521643_UIT.docx](../../docs/DeCuongKLTN_23521635_23521643_UIT.docx)
- The submitted UIT version cannot be changed any more. Deviations have to be disclosed in the thesis through the datasheet's "Chỗ lệch với đề cương" table — [master-plan.md P1.2](../../docs/plans/active/master-plan.md); [datasheet §6](../../docs/vilextime-datasheet.md)

**Paper (`paper/problem_statement.md`)**
- RQ1 measures TVER and VCR of no-retrieval and flat RAG. RQ2 measures the change in TVER, VCR and TCS, with bootstrap CIs by provision chain. RQ3 uses four representation levels: "không gì cả, ngày của văn bản, khoảng hiệu lực riêng của đơn vị, và khoảng được lan truyền qua mọi đơn vị cấp trên theo (3)". The required information is I1 version chains, I2 ancestor chain and I3 transitive closure of acting documents — [paper/problem_statement.md §2.3–2.4](../../paper/problem_statement.md)
- Scope excludes "điều khoản chuyển tiếp …, xung đột …, và việc áp dụng hồi tố vượt ra ngoài ngày có hiệu lực do văn bản tác động nêu" — [problem_statement §2.5 item 2](../../paper/problem_statement.md). T5 as built (effective date stated before signing) is still within *de jure* scope, but the paper never names retroactivity as a claim.
- The framework plan (01/10) makes the main result "thang đủ của biểu diễn": tiers none / document (B7) / version (B7+) / propagated (proposed). It also records "H3 không được kiểm vì không đủ lực thống kê — 24 dòng / 24 lineage" — [docs/plans/active/phase-5-6-framework.md, Approach + Decisions 01/10](../../docs/plans/active/phase-5-6-framework.md). The propagated-versus-version difference is exactly the T6 `ancestor` phenomenon.
- `build_question_pool.py` labels T1 "control", T2 "core group", T3 "where the graph should pay" and T4 "the citation trap" — [module docstring](../../scripts/pipeline/build_question_pool.py)

**How each group discriminates (current release)**
- B7-trap share of the main table, i.e. rows where as-published text ≠ gold while the document is in force — [JUDGE §5 C2](../../docs/reports/JUDGE_DATASET.md):

  | T1 | T2 | T3 | T4 | T5 | T6 |
  |---:|---:|---:|---:|---:|---:|
  | 0% | 49.7% | 67.5% | 49.7% | 55.3% | 50.9% |

- Probes on the test split, `giua_khoang` table — [datasheet §8](../../docs/vilextime-datasheet.md):

  | Probe | T1 | T3 |
  |---|---:|---:|
  | latest | 1.000 | 0.325 |
  | nearest-date | 1.000 | 0.713 |

  T1 does not discriminate between version pickers. It is a sanity and "no regression" control.
- The scorer computes TCS on T2 pairs only, not on T4 — [JUDGE §8 Mục F](../../docs/reports/JUDGE_DATASET.md). Dropping or shrinking T2 removes TCS power.
- The plan's cut order if work runs late is: "giảm T3 … → giảm T4 → **không cắt** T2 … và **không cắt** D4" — [phase-4 plan, Lịch 8 tuần](../../docs/plans/active/phase-4-vilextime.md)
- Earlier decision (20/09): the T5 shortfall goes to T6 "vì T6 dư trữ lượng … và phục vụ trực tiếp giả thuyết H2 — phép thử quyết định với đường cơ sở B7" — [phase-4 plan Decisions](../../docs/plans/active/phase-4-vilextime.md)

**Option-by-option facts** (option labels from the caller)

**(a) T2–T6, without T1**
- For:
  - T1 has a 0% B7 trap and 1.000 on every version probe, so it adds nothing to the RQ1–RQ3 contrasts.
  - All five remaining groups carry temporal signal.
- Against:
  - **T5 cannot supply 300** (≤194 total, ≤148 clean).
  - **T3 cannot supply 300 substantive chains** (130–249).
  - It removes the outline's only "Đối chứng" group, a disclosed deviation.
  - Without static questions, nobody can show that the temporal filter or Verifier does not hurt plain lookups. The framework adds `answerable`/abstain behaviour, and T1 is where false abstention would show.

**(b) T1–T5, with T6 merged into T5**
- For:
  - It keeps the control group.
  - A combined "hard cases" group reaches 300 easily thanks to T6 (852 direct + 264 ancestor clean in the pool).
  - It follows the precedent "T6 nhận phần thiếu của T5".
- Against:
  - It mixes two unrelated phenomena: an effective date before signing, and a partial repeal or ancestor repeal.
  - T5 would be ≤~148 of 300, from 3–4 acting documents.
  - Per-phenomenon reporting needs sub-labels: `retroactive` vs `repeal_mode` already exist as fields.
  - T3 is still the bottleneck.

**(c) Six groups at 250**
- For:
  - It keeps the outline's six-group structure.
  - 1,500 lineages total.
- Against:
  - T5 at 250 is infeasible (≤194).
  - T3 at 250 is infeasible under the strict test (130) and marginal under the liberal one (249 clean, at ≥3 chains per document).

**(d) Other: an inference built from these facts**
- The shape:
  - T1 (control, can stay ~250–300);
  - T2 300;
  - T3 capped at ~130–250 depending on the substantive rule, with a lower per-document cap waived;
  - T4 300;
  - T6 ≥300, stratified direct/ancestor so that H3 gets real power;
  - T5 as an un-quota'd illustrative set (19 existing, at most ~148 candidates, lawyer-gated), reported separately.
- The shortfall from T3 and T5 goes to T6-ancestor or T2. This is the existing plan's own fallback logic (Q3, Q4).

### Inferences
- The paper's strongest claim, RQ3 via the four-tier ladder, needs **many T6-ancestor lineages**. The framework plan currently cannot test H3 with 24 rows. A 300-lineage T6 with, say, ≥150 ancestor lineages would turn H3 from "minh họa" into a testable claim. Supply supports this (10,055 candidates in 484 documents).
- T5 is "essential" only in the sense that the outline lists it. Neither the paper's RQs nor its formal model (formulas 1–4) needs it, and the data cannot give it statistical weight. Keeping it as a small illustrative stratum honours the outline without spending ~600 labelled rows that cannot exist.
- T1 matters as a control for the thesis structure (outline Bảng 1) and for regression checks of the proposed filter and Verifier. It is not needed for any RQ contrast. Dropping it is defensible for the paper but is a deviation for the thesis.

### Gaps
- I found no repo document in which the team itself has weighed 5×300. The options above rest only on the existing plans and decisions.
- The outline's "1.100–1.300 câu hỏi" target: 1,500 lineages (1,500 distinct questions) exceeds that range. Whether the faculty accepts an upward deviation is not documented.

---

## Q3. Current pipeline: what builds, samples, generates, enriches, checks and releases, and what can be reused for 1,500 lineages?

### Takeaway
The whole chain exists, is deterministic and is re-runnable. Gold is derived from version chains and questions are generated per lineage. Scaling to 1,500 lineages is mostly parameter changes, but there are specific hard-coded quotas. Quotas are counted in **rows**, not lineages. T6-ancestor has a hard cap. Sampling allows at most 2 lineages per document. The D4 scope is fixed at 300 rows. The labelling and evidence tooling (crosscheck build/kappa, Excel export/import, evidence builder, labels.py audit, t5_worksheet) is reusable as is.

### Cited Findings
- The build order recorded after the 29/09 review is `build_versions` → pool → `build_vilextime` → `--select` → `enrich` → `build_corpus` — [JUDGE §7.2](../../docs/reports/JUDGE_DATASET.md)
- Scripts and what each does or needs changed (from module docstrings):

  | Script | Role | Change needed for 1,500 lineages |
  |---|---|---|
  | [`scripts/pipeline/build_question_pool.py`](../../scripts/pipeline/build_question_pool.py) | Pool. `QUOTA = {T1 250, T2 400, T3 200, T4 150, T5 50, T6 100}`, `PRIORITY`, `NEAR_IDENTICAL = 0.90`, `SEED`, `ANCESTOR_CAP = 300`, `--per-group-cap 10`, `--today 2026-09-20`. `stable_sample` keeps already-ranked lineages when rebuilding. | Quotas, `ANCESTOR_CAP` |
  | [`scripts/pipeline/build_vilextime.py`](../../scripts/pipeline/build_vilextime.py) | Pool rows → per-(provision, `as_of`) records in `data/derived/vilextime/T*.jsonl`, with structural `flags` | — |
  | [`scripts/pipeline/sample_vilextime.py`](../../scripts/pipeline/sample_vilextime.py) | Ranked lineages: `QUOTA` in rows (T6 150), `OVERSAMPLE` (T3 ×3, others ×2), **`PER_DOCUMENT = 2`**; skips flagged lineages; `--select` walks the ranks, skips `dropped.jsonl`, uses subset-sum for T3 | Quotas, `PER_DOCUMENT` |
  | [`scripts/pipeline/generate_questions.py`](../../scripts/pipeline/generate_questions.py) | One question per lineage; `validate()` with 9+ rejection codes; append-only `data/vilextime/questions.jsonl`; `--revalidate` | — |
  | [`scripts/pipeline/enrich_vilextime.py`](../../scripts/pipeline/enrich_vilextime.py) | Twins, after-expiry rows, `changed_span`, `evidence_set`, `accepted_evidence`, domain, `retrieved_at`, `split` (sha1 by document, T5 → test), `legal_markers`, `short_answer` | — |
  | [`scripts/check/check_release.py`](../../scripts/check/check_release.py) | Invariants and `--manifest` | — |
  | [`scripts/check/check_validity.py`](../../scripts/check/check_validity.py) | Detector → `data/review/validity_queue.tsv` (31–37% precision) | — |
  | [`scripts/check/measure_gold_uniqueness.py`](../../scripts/check/measure_gold_uniqueness.py) | BM25 check that no other in-force provision also answers the question | — |
  | [`scripts/review/crosscheck.py`](../../scripts/review/crosscheck.py) | D4 `build`/`kappa` (κ, AC1, % agreement, per lineage). Scope fixed at 300 rows: all T5 and T6 plus 50 each of T2/T3/T4 | D4 scope |
  | [`scripts/review/crosscheck_xlsx.py`](../../scripts/review/crosscheck_xlsx.py) | Locked Excel with dropdowns, import refuses edited cells | — |
  | [`scripts/review/crosscheck_evidence.py`](../../scripts/review/crosscheck_evidence.py) | Untracked. Cuts the base Article/Clause and each actor's acting passage, transitional provisions and entry-into-force article from **raw** `data/raw/<doc>.json`, so the check is not circular | Make it iterate over the labelled set, not only `crosscheck_A.tsv` |
  | [`scripts/review/labels.py`](../../scripts/review/labels.py) | `add`, `import-excel`, `report`, `mark-audit`, `audit-sheet`, `import-audit`; human auditor enforced | — |
  | [`scripts/review/t5_worksheet.py`](../../scripts/review/t5_worksheet.py) | Lawyer sheets | — |
  | [`scripts/eval/judge_vilextime.py`](../../scripts/eval/judge_vilextime.py) | LLM-as-judge with calibration (`sample` / `agree`) | — |

- The 24/09 decision fixed the quota unit: "quota đếm theo dòng QA, tổng 1.150 dòng … T3 200 dòng ≈ 55–65 chuỗi. Không cắt một lineage giữa các mốc" — [phase-4 plan, Decisions đã chốt](../../docs/plans/active/phase-4-vilextime.md); [ADR 0003 Follow-Up](../../docs/decisions/0003-schema-bo-du-lieu-vilextime.md). Counting 300 *lineages* changes that unit.
- Caveat: "`sample_vilextime.py` (không kèm `--select`) giữ thứ tự cũ nhưng **đánh số hạng lại** khi có lineage rời nhóm" — [phase-4 plan J4](../../docs/plans/active/phase-4-vilextime.md)
- Under ADR 0003 §8, changing gold or moving items between splits is a MAJOR change. v1.0 is not frozen yet — [ADR 0003 §7–8, Follow-Up](../../docs/decisions/0003-schema-bo-du-lieu-vilextime.md)
- The questions are written by a Claude Code session (`provider: claude-code`, `model: claude-opus-5-5`, `--answers`), because the free Groq tier was limited to ~75 questions/day — [phase-4 plan 24/09](../../docs/plans/active/phase-4-vilextime.md)

**Known open issues**
- [JUDGE](../../docs/reports/JUDGE_DATASET.md):
  - C1 twin-row gold errors (1.18% lower bound) → J2/J3 fixed the known ones;
  - C2, C3 scorer → J1 fixed;
  - C4: no human checking yet;
  - C5 packaging → partly done;
  - N1: gold and KG share a source (circular), L2 recall 62.2%;
  - N2: B7 vs B7+;
  - N3: boundary dates leak; T3 boundary moved 29/09, T1 still at start+1;
  - N4: only `amend`/`repeal` transitions; H3 12 lineages; T5 from 3 actors;
  - N5: domain labels;
  - N6: deviations from the outline;
  - V5: transitional provisions;
  - V6: "cấp huyện" after 01/07/2025.
- Still open for people (J6/J7) — [phase-4 plan, "Còn lại cho người"](../../docs/plans/active/phase-4-vilextime.md):
  - D4 κ on 300 rows;
  - audit of 490 labels;
  - the lawyer's T5 ruling;
  - 26 `sau_D4` flags;
  - `cap_huyen` flags;
  - ~120 independent-gold rows.
- **[computed]** `data/review/validity_queue.tsv` has 186 lines. Pending:
  - 31 `sau_D4`: 18 `missed_event`, 8 `document_ended`, 3 `cap_huyen`, 2 `effectivity_clause`;
  - 8 `cap_huyen` with no decision.

  The rest are decided: 107 `bao_dong_gia`, 36 `loi` (now inactive or fixed).

### Inferences
- About 80% of the work for 1,500 lineages is re-parameterising and re-running these scripts:
  - change `QUOTA` in two files to lineage-based or larger row quotas;
  - raise `ANCESTOR_CAP`;
  - relax `PER_DOCUMENT` for T3 and T5;
  - widen the D4 scope in `crosscheck.py`;
  - make `crosscheck_evidence.py` iterate over the labelled set, not only `crosscheck_A.tsv`.
- Gold derivation needs no new code. A T3 "substantive" filter, though, would be new logic in `build_question_pool.classify` or in the sampler.
- New questions are the main generation cost. Using the current pass rates (75–99% at C2, then post-label drops) on top of the release, roughly another ~1,000 lineages need questions:

  | Group | Release lineages | Still needed for 300 |
  |---|---:|---:|
  | T1 | 251 | +49 |
  | T2 | 200 | +100 |
  | T3 | 65 | +235 |
  | T4 | 75 | +225 |
  | T5 | 19 | +281, impossible |
  | T6 | 56 | +244 |

  About 105 lineages already have passed questions outside the release.

### Gaps
- I did not run any script, by the read-only constraint, so the end-to-end runtime of a rebuild is not measured here. The pool builder streams the ~1.1 GB `versions.jsonl`. The plan notes RAM limits ("bị kill khi RAM trống ~1 GB").

---

## Q4. Workload: rows to label for 1,500 lineages, and which existing labels can be reused

### Takeaway
At 300 lineages per group, every 5-group option means about 3,000–3,300 boundary rows, roughly 2.6–2.9× today's 1,150. Doubling for mid-interval twins and adding about 350 after-expiry rows gives ~6,400–7,000 rows whose gold is checked at some date. With 2 annotators each labelling every boundary row, that is ~6,000–6,600 human judgements in 45 days (~67–73 boundary rows per annotator per day, before twins and after-expiry checks). No existing *human* label covers T3–T6. Only 210 human (Excel) labels exist (T1/T2), none audited, and the D4 cross-check has 0/300 verdicts.

### Cited Findings
- **[computed]** Rows per lineage:
  - T1: 1 boundary row;
  - T2, T4, T5, T6: 2;
  - T3: as many as versions — 3.047 on average in the pool (1,176 rows / 386 chains), 3.06 in the release (199/65).
- **[computed]** Every boundary row has one twin (1,150 twins for 1,150 boundary rows). After-expiry rows exist only where the target document ended:

  | Group | After-expiry rows / lineages | Share |
  |---|---:|---:|
  | T1 | 78/251 | 31% |
  | T2 | 61/200 | 31% |
  | T3 | 15/65 | 23% |
  | T4 | 20/75 | 27% |
  | T5 | 7/19 | 37% |
  | T6 | 0/56 | 0% (its documents are in force by construction) |

- **[computed]** Arithmetic per option at 300 lineages per group, from the per-lineage factors above. After-expiry rows are estimated from the release shares.

  | Option | Boundary rows | Twins | After-expiry (est.) | Total rows | Annotator judgements on boundary rows (×2) |
  |---|---:|---:|---:|---:|---:|
  | (a) T2–T6 | 600+914+600+600+600 = **3,314** (T5 not fillable) | 3,314 | ≈351 | ≈6,980 | ≈6,630 |
  | (b) T1–T4 + T5∪T6 | 300+600+914+600+600 = **3,014** | 3,014 | ≈334 | ≈6,360 | ≈6,030 |
  | (c) 6 × 250 | 250+500+762+500+500+500 = **3,012** (T5 not fillable) | 3,012 | ≈371 | ≈6,400 | ≈6,020 |
  | (d) T1, T2, T3, T4, T6 at 300 + T5 illustrative | **3,014** + T5 2 rows per lineage | — | — | — | — |

- Current guideline v1.2: annotators label boundary rows only, and the twin shares the *question* label. **Gold does not carry over** to the twin. The audit checks validity "ở **mọi** ngày" (twins, after-expiry): (a) no amendment or repeal before the date, (b) the document has not ended, (c) no transitional provision — [docs/vilextime-annotation.md §5.1, §6.3](../../docs/vilextime-annotation.md). Twin and after-expiry rows therefore add checking effort, not extra κ rows.
- **[computed]** `data/review/labels.tsv` has 1,133 labels:

  | Labeler | Group | `dat` | `khong_dat` | No verdict |
  |---|---|---:|---:|---:|
  | `claude-opus-5-5` (923) | T1 | 256 | 4 | — |
  | | T2 | 364 | 6 | — |
  | | T3 | 164 | 25 | — |
  | | T4 | 102 | 2 | — |
  | `human:excel` (210) | T1 | 134 | 7 | 43 (meta only) |
  | | T2 | 26 | — | — |

  Guideline versions are 1.1 for 893, excel for 210 and 1.2 for 30. `audit_required = có` on 490 labels, and **0 audited**. There are no T5/T6 labels, because all of them are in the κ set.
- **[computed]** `crosscheck_A.tsv` and `crosscheck_B.tsv` have 300 rows each (T2 50, T3 50, T4 50, T5 38, T6 112), and both have **0** filled verdicts. `crosscheck_evidence.jsonl` has evidence for all 300 rows.
- Model–human agreement so far is 86.8% on 159 co-labelled rows, and T1 86.5% on 141 rows — [phase-4 plan V3, 28/09](../../docs/plans/active/phase-4-vilextime.md)
- Per the user's memory note (02/10), D4 annotator A is now treated as an LLM jury (3 models via the HF router on Colab) and B stays human. The repo guideline §6.1 still says D4 is human-only. The caller's brief says "2 annotators + a legal advisor", by hand, which conflicts with this note. Output goes to `crosscheck_A.model.tsv` (not in the repo) — user memory `d4-annotator-a-is-model.md`.

### Inferences
- If the human labels must cover every boundary row twice, about 6,000+ judgements are needed. The only directly reusable human effort is the 210 Excel labels (T1/T2, not blind). The 923 model labels can serve as pre-labels or a third opinion, but not as human labels (guideline §6.4: the model's `dat` rate is an upper bound).
- A cheaper design, consistent with the current plan: one human labels every row with model pre-labels and audit rules, and κ comes from a doubly labelled stratified subset. That would cut human judgements to ~3,000 plus the κ subset. This is a design option, not a repo decision.
- The lawyer's load depends on documents, not rows. T5 is 8 acting documents in `t5_documents.tsv`. T6 is reviewed under Q2 "toàn bộ T5 và T6" in κ. At 300+ T6 lineages, "all of T6 in κ" (≥600 rows) would by itself exceed the current 300-row κ scope.

### Gaps
- The repo has no measurement of human labelling time per row (searched the plans and guideline). Any person-hour estimate needs an assumed rate. For example, at 2 min per boundary row per annotator, 3,014 rows ≈ 100 h per annotator; this is an assumption, not a measured value.
- I do not know how many model-jury labels for D4 already exist outside the repo.

---

## Q5. Deadline constraints and competing work (M3 16/11/2026)

### Takeaway
There are 45 calendar days from 02/10 to 16/11. The same two people own M2 (26/10: 100 hand-checked snapshot queries, E2–E3, not started). They also owe the v1.0 human backlog: κ 300 rows, audit of 490 labels, lawyer T5, 31 `sau_D4` flags, ~120 independent-gold rows. The framework and baseline phase is already running against the 1,150-row release. The plan itself scheduled weeks 1–4 as "scripts and paperwork only" because people were busy with phase 3 until M2. A 1,500-lineage manual relabel therefore competes directly with M2 for the first 3.5 weeks.

### Cited Findings
- M3 (16/11) is "ViLexTime đủ 1.150 câu; Cohen κ ≥ 0,6 trên 300 câu". M2 (26/10) is "`snapshot(u,t)` đúng trên 100 truy vấn đối chiếu tay" and is still ⬜. M4 is 30/11 in the master plan — [master-plan.md, Mốc kiểm tra](../../docs/plans/active/master-plan.md). M4 was decided early on 01/10 — [phase-5-6-framework.md](../../docs/plans/active/phase-5-6-framework.md)
- M2 needs P3.18: E2 (100 stratified hand queries) and E3 are not done — "Không cắt E2, vì đó là điều kiện của M2" — [phase-3-kg-l0-l3.md](../../docs/plans/active/phase-3-kg-l0-l3.md). The outline assigns CMT to L0–L2 and NMT to L3 and snapshot verification — [master-plan §4](../../docs/plans/active/master-plan.md)
- The outline schedule puts GĐ4 ViLexTime at 24/10–13/11, GĐ5 systems at 14/11–04/12, GĐ6 experiments at 05/12–14/12, and completion on 26/12/2026. "Master plan còn theo lịch đề cương cũ (đến 01/02/2027)" — [phase-4 plan 28/09](../../docs/plans/active/phase-4-vilextime.md); [outline docx](../../docs/DeCuongKLTN_23521635_23521643_UIT.docx)
- The original 8-week plan said: "Hai người vẫn đang chạy Giai đoạn 3 tới M2 (26/10), nên bốn tuần đầu chỉ nhận phần việc script và giấy tờ, không nhận phần cần ngồi kiểm tay hàng trăm câu." D4 was planned for 03–09/11 and fixes plus split for 10–16/11 — [phase-4 plan, Lịch 8 tuần](../../docs/plans/active/phase-4-vilextime.md)
- The framework plan ingests `release.jsonl` ("Khi bộ dữ liệu được gán nhãn xong, không dòng code nào đổi"). Its remaining items are P2 BM25 four-tier, P4 embedding + Milvus ("chưa viết", no GPU, 4 CPU, 7 GB RAM), A1–A7 and B5 — [phase-5-6-framework.md, Outcome + Progress](../../docs/plans/active/phase-5-6-framework.md)
- Plan roles: NMT leads the diff-driven pipeline, and CMT does the cross-check and works with the legal adviser. A = CMT, B = NMT — [phase-4 plan Context; V-plan item 4](../../docs/plans/active/phase-4-vilextime.md)
- The legal adviser is the longest-wait dependency: "D1 (liên hệ cố vấn luật ngay, đây là việc có thời gian chờ dài nhất)". The T5 sheets are still unfilled 12 days after the 20/09 consultation — [phase-4 plan](../../docs/plans/active/phase-4-vilextime.md); [computed] empty `LUẬT SƯ:` columns

### Inferences
- The real labelling window is ~26/10–16/11, about 3 weeks, unless M2 is de-prioritised. At ~6,000 boundary-row judgements, that comes to ~140–150 per annotator per working day for both annotators, on top of D4 adjudication and validity checks at twin dates. That is implausible without model pre-labels and audit sampling, or without fewer doubly labelled rows.
- A rebuild invalidates part of the current κ set if lineages change (the J5 precedent: 3 replaced lineages, 50 T3 ids changed). Freezing the κ set first, or rebuilding before D4 starts, avoids redoing blind labels.
- Any dataset change after GĐ5 starts (14/11) forces the baselines to be re-run. The framework is built to accept that ("không dòng code nào đổi"), but compute (BM25/embedding over 1.5M units) is the limit, not code.

### Gaps
- Who exactly is "the 2 annotators" for the 1,500-lineage relabel: CMT and NMT, or other people? This is not documented. If it is CMT and NMT, they are also the M2 owners.
- The legal adviser's availability and turnaround are not recorded in the repo.
