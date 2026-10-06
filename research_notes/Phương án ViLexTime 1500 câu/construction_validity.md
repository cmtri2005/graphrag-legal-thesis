# Construction and validity of a temporal legal QA benchmark (ViLexTime 1,500-lineage rebuild)

Scope: design rules and decision criteria for question authoring, category taxonomy, per-category sample size,
artifacts/shortcuts, contamination, splits, baselines and metric validity, applied to ViLexTime
(6 candidate groups T1–T6, plan = 300 lineages × 5 groups, 2 annotators + legal advisor, deadline 16 Nov 2026).

Provenance notes for the report writer:
- Numbers marked **[computed]** were computed by me in this session (Python, normal/Wilson formulas); they are not
  quoted from a paper. Formulas: Wilson score interval; Connor-style McNemar sample-size approximation; two-proportion
  z-test; design effect 1+(m−1)ρ; large-sample SE of Cohen's κ.
- Card et al. 2020 and Bowyer et al. 2025 numbers were read from the PDF text directly. Details marked
  **(tool summary)** came from a WebFetch summariser and should be spot-checked in the PDF before quoting verbatim.
- Repo facts come from `docs/reports/JUDGE_DATASET.md` (critique dated 29/09/2026) and `paper/problem_statement.md`.

---

## Q1. What do construct-validity and benchmark-quality papers recommend, with numbers?

### Takeaway
The quality literature agrees on four rules: define the construct narrowly and show that each item measures it;
make the labels correct; size the test set by a power analysis rather than convention; and publish
partial-input and trivial baselines to show the benchmark cannot be gamed. Most published benchmarks fail the
statistics and reproducibility items. For example, 14/24 benchmarks audited by BetterBench report no
significance or uncertainty.

### Cited Findings
- BetterBench scores benchmarks against 46 best practices across the benchmark life cycle (design, implementation,
  documentation, maintenance). It finds large quality differences, with the highest quality at design and the lowest
  at implementation. It is a NeurIPS 2024 D&B Spotlight — [BetterBench, Reuel et al. 2024](https://arxiv.org/abs/2411.12990); [Stanford HAI brief](https://hai.stanford.edu/policy/what-makes-a-good-ai-benchmark)
- BetterBench design criteria include defining the tested capability and how it maps to tasks, involving domain
  experts, choosing suitable metrics, and including reference points such as human or random baselines.
  Implementation criteria include evaluation code, replication scripts, and contamination safeguards (unique
  identifiers or encryption). Documentation criteria include construction process, limitations, statistical
  significance and licence (tool summary) — [BetterBench](https://arxiv.org/html/2411.12990v1)
- "14 out of 24 benchmarks did not perform multiple evaluations of the same model or report statistical
  significance or uncertainty"; "17 out of 24 … do not provide easy-to-run scripts"; only about 2/24 use
  contamination safeguards (tool summary) — [BetterBench](https://arxiv.org/html/2411.12990v1)
- Raji et al. 2021 frame benchmark over-claiming as a **construct-validity** problem. A benchmark can be well
  defined while what it measures is not what the community claims it measures — [Raji et al., NeurIPS 2021 D&B](https://arxiv.org/abs/2111.15366)
- Saxon et al. 2024 call for "model metrology": benchmarks should reflect concrete real-world measurement needs
  rather than fixed generic problem sets, and should move toward dynamic benchmarks — [Benchmarks as Microscopes](https://arxiv.org/abs/2407.16711)
- Bowman & Dahl 2021 set four criteria for NLU benchmarks: (1) validity, meaning good benchmark performance should
  imply robust in-domain task performance; (2) reliable annotation, meaning labels are correct and reproducible;
  (3) statistical power, meaning the benchmark can detect meaningful differences; (4) handling of social bias. They
  argue that adversarial data collection does not meaningfully address the causes of these failures — [Bowman & Dahl, NAACL 2021](https://aclanthology.org/2021.naacl-main.385); [arXiv](https://arxiv.org/abs/2104.02145)
- **Annotation artifacts:** a hypothesis-only text classifier labels about 67% of SNLI and 53% of MultiNLI
  correctly without seeing the premise. Negation and vagueness cues correlate with labels — [Gururangan et al., NAACL 2018](https://aclanthology.org/N18-2017/)
- **Partial-input baselines:** question-only and passage-only models "often perform surprisingly well". On 14/20
  bAbI tasks, passage-only models exceed 50%. In CBT, only the last of 20 sentences is needed. SQuAD and CNN looked
  better constructed — [Kaushik & Lipton, EMNLP 2018](https://aclanthology.org/D18-1546/)
- Simple unigram/bigram features of the prompt predict correct answers on several multiple-choice LLM benchmarks,
  with evidence that some LLM families exploit them (the "Clever Hans" effect) — [Pacchiardi et al. 2024](https://arxiv.org/abs/2410.11672)
- **Adversarial or difficulty filtering:** across 18 adversary models, AFLite filtering, TextFooler perturbation and
  model-in-the-loop collection (ANLI, AdversarialQA) all make sets harder. However, the resulting model rankings
  are unstable and highly sensitive to the choice of adversary. AFLite also oversamples items with low annotator
  agreement, so comparisons hinge on the items humans find most contentious — [Phang et al., DADC 2022](https://aclanthology.org/2022.dadc-1.8)
- Dynabench uses human-and-model-in-the-loop creation: annotators write items that fool a target model but not
  another person — [Kiela et al., NAACL 2021](https://arxiv.org/abs/2104.14337)
- Case study of filtering against frontier models: Humanity's Last Exam kept only questions that stumped frontier
  LLMs (about 13k of more than 70k submissions passed) before expert review. A FutureHouse audit then reported that
  about 29% of the chemistry/biology answers were wrong or misleading. The HLE team's own follow-up put the share
  of problematic questions in a Bio/Chem subset at about 18%. Both are secondary reports, and the exact figures are
  contested — [FutureHouse](https://www.futurehouse.org/research/hle-exam); [The Decoder](https://the-decoder.com/nearly-29-percent-of-humanitys-last-exam-questions-are-wrong-or-misleading/)
- Label errors are pervasive in popular benchmarks (GLUE, SQuAD, GSM8K): mislabelled, contradictory, ambiguous and
  ill-posed items. "Platinum" re-curation exposes frontier-model failures that the errors had hidden — [Vendrow et al. 2025](https://arxiv.org/abs/2502.03461)
- **Aggregating across categories:** mean-of-scores aggregation is sub-optimal. Social-choice rules are more robust
  and can handle missing scores — [Vote'n'Rank, Rofin et al., EACL 2023](https://aclanthology.org/2023.eacl-main.48)

### Inferences
- **Construct statement for ViLexTime.** Claim one narrow construct: "selecting the provision version in force at
  `as_of` and abstaining when none is". Do not claim "temporal legal reasoning". This follows Raji et al. Each group
  T2–T6 then needs a written *failure hypothesis*, the specific mechanism it isolates. A group with no distinct
  hypothesis is padding. Draft hypotheses:
  - T2: picks the wrong version when two versions clearly differ.
  - T3: cannot place `as_of` inside a chain of ≥3 *answer-changing* versions. A middle version is neither the
    latest nor the earliest.
  - T4: cannot discriminate versions that differ by a small span (lexical-similarity trap).
  - T5: ignores retroactive effect (effective date earlier than issue or publication).
  - T6: ignores unit-level repeal, so it should abstain or answer "no longer in force".
- **Required trivial baselines as validity checks.** The literature calls these partial-input and trivial-heuristic
  baselines. The repo already has some as "probes":
  - "latest version", "earliest version" and "closest date" ([JUDGE_DATASET.md §5 C3](../../docs/reports/JUDGE_DATASET.md));
  - an **`as_of`-blind** baseline: the same system, with the date removed from the question. This is the
    analogue of a question-only baseline and directly measures date dependence;
  - "print all versions" (hedging) and "always abstain".
  
  A group is valid only if these baselines score clearly below a real system. The repo's earlier measurement showed
  the closest-date probe solving 100% of T3 boundary rows (JUDGE N3), which is exactly the Gururangan / Kaushik &
  Lipton failure pattern.
- **Clever-Hans check.** Fit a logistic regression on question n-grams + `as_of` features to predict "gold = latest
  version vs not". Above-chance accuracy indicates a cue leak, for example the LLM drafter phrasing
  post-amendment questions differently.
- **Do not difficulty-filter against the evaluated models** (Phang et al.; HLE). If a filter is used, use a model
  family not among those evaluated, and report the unfiltered set as well.

### Gaps
- I did not fetch the full 46-item BetterBench checklist. Item wording above is from a tool summary. Use the
  checklist PDF at betterbench.stanford.edu when citing specific items.
- I found no paper that quantifies a "minimum number of categories" or "minimum items per category" as a rule. The
  statistics section below derives sizes from power instead.

---

## Q2. Statistical power: CIs at n = 50/150/300/1,500, paired tests, minimum detectable difference

### Takeaway
At n = 300 per group, a single system's accuracy is pinned to about ±5–6 pp (95% Wilson). A paired comparison of
two systems can detect only differences of about 5–10 pp, depending on how often the systems disagree. Comparing
groups with each other within one system (e.g. "T4 is harder than T2") needs gaps of about 11 pp. At n = 50, every
one of these numbers is 2–3× worse. Because ViLexTime rows cluster by lineage and by amending document, the
effective n is smaller than the row count, so the unit of resampling must be the lineage, or the document for T5.

### Cited Findings
- Card et al. 2020 recommend running a power analysis before experiments. If the expected improvement is below the
  minimum detectable effect (MDE), choose a larger dataset or retire the task. Their Table 2 (MDE for 80% power,
  McNemar, using agreement estimated from real GLUE submissions, all at SOTA accuracy ≥ 91.7%):
  - WNLI n = 147: MDE +5.26 pp (mean reported gain 1.72);
  - MRPC n = 1,725: +1.62 pp;
  - SST-2 n = 1,821: +1.02 pp;
  - RTE n = 3,000: +1.23 pp;
  - QNLI n = 5,463: +0.55 pp.
  
  "The mean reported effect size is well below the estimated MDE for the three smallest test sets". MDE grows when
  model agreement is lower. — [Card et al., EMNLP 2020](https://arxiv.org/abs/2010.06595)
- Card et al.: McNemar's test is "the standard statistical test for comparing classifiers on paired data". It uses
  only the items where the two models disagree. Further findings: only 46% of reported improvements they examined
  would have been predicted to have adequate power; MT test sets of 2,000 sentences have about 75% power to detect
  1 BLEU; and human evaluations with 3 workers × 100 items are underpowered unless the effect is ≥ 0.2 on a [0,1]
  scale — [Card et al. 2020](https://arxiv.org/abs/2010.06595)
- Bowyer, Aitchison & Ivanova 2025 (ICML position paper) show that CLT intervals undercover when there are fewer
  than "a few hundred" items. At N = 100, nominal 95% CLT intervals achieved only 92.5% coverage (IID setting).
  Wilson score intervals and Beta-Bernoulli Bayesian credible intervals keep near-nominal coverage at small N.
  Clopper-Pearson is overly conservative. Bootstrap is also flagged as failing coverage at small N. In the clustered
  setting, neither simple nor clustered CLT gives correct coverage at small N. For paired model comparison they
  recommend a paired Bayesian method; unpaired Bayes is an acceptable simpler alternative. They note that
  FrontierMath has about 300 problems across 23 categories, some with fewer than 3 samples — [Bowyer et al., ICML 2025](https://arxiv.org/abs/2503.01747); [PMLR](https://proceedings.mlr.press/v267/bowyer25a.html)
- Miller 2024 (Anthropic) recommends the following (tool summary):
  - CLT standard errors.
  - **Clustered standard errors** when questions come in related groups. Reported clustered/naive SE ratios are
    DROP 3.05×, RACE-H 1.10× and MGSM 1.88×.
  - Analysis of question-level **paired differences**. With a between-model correlation of 0.5, this cuts variance
    by about 1/3.
  - A power formula n = (z_{α/2}+z_β)²(ω²+σ²_A/K_A+σ²_B/K_B)/δ². Worked example: detecting δ = 3 pp at 80% power
    needs about 969 independent questions.
  - Resampling answers to reduce within-question variance.
  
  — [Miller, "Adding Error Bars to Evals", 2024](https://arxiv.org/abs/2411.00640)
- Dror et al. 2018 give a protocol for choosing significance tests in NLP, with an appendix of recommended tests per
  evaluation measure (parametric and non-parametric, e.g. bootstrap and McNemar) — [Dror et al., ACL 2018](https://aclanthology.org/P18-1128/); [appendix](https://arxiv.org/abs/1809.01448)
- Temporal-legal precedent: FiscalQA Pro reports cluster-aware bootstrap CIs (10,000 resamples, **articles as the
  resampling unit**) plus per-model McNemar tests (tool summary) — [Cymbler et al. 2026](https://arxiv.org/abs/2608.09393)
- The German statutory benchmark (312 items) used Welch t-tests (tool summary). One between-condition difference
  was only marginally significant (p = 0.048). This illustrates the low power of n ≈ 100 per category — [Prior et al. 2026](https://arxiv.org/abs/2605.23497)

### Computed tables [computed]
**Table A. 95% Wilson CI half-width (± pp) for one system's accuracy, rows treated as independent**

| n \ accuracy | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|
| 12 (current H3) | ±24.6 | ±24.2 | ±23.1 | ±21.0 | ±17.7 |
| 38 (current T5 rows) | ±15.2 | ±14.9 | ±14.0 | ±12.4 | ±9.8 |
| 50 | ±13.4 | ±13.1 | ±12.3 | ±10.9 | ±8.5 |
| 100 | ±9.6 | ±9.4 | ±8.8 | ±7.8 | ±6.0 |
| 150 | ±7.9 | ±7.7 | ±7.3 | ±6.4 | ±4.8 |
| 300 | ±5.6 | ±5.5 | ±5.2 | ±4.5 | ±3.4 |
| 600 | ±4.0 | ±3.9 | ±3.7 | ±3.2 | ±2.4 |
| 1,500 | ±2.5 | ±2.5 | ±2.3 | ±2.0 | ±1.5 |

**Table B. Paired MDE (pp) between two systems on the same items.** McNemar, α = 0.05 two-sided, power 0.8, normal
approximation. p_d is the fraction of items where the two systems disagree.

| n \ p_d | 0.1 | 0.2 | 0.3 | 0.4 |
|---|---|---|---|---|
| 50 | ≈10* | 17.3 | 21.2 | 24.5 |
| 150 | 7.2 | 10.1 | 12.4 | 14.4 |
| 300 | 5.1 | 7.2 | 8.8 | 10.2 |
| 600 | 3.6 | 5.1 | 6.3 | 7.2 |
| 1,500 | 2.3 | 3.2 | 4.0 | 4.6 |

\* At n = 50 and p_d = 0.1 there are only about 5 discordant items, so the normal approximation is invalid. Use
exact McNemar or Bayesian paired intervals (Bowyer et al.).

**Table C. Unpaired MDE (pp) between two groups of size n each.** This applies to within-system statements such as
"T4 accuracy < T2 accuracy". α = 0.05, power 0.8.

| n per group | base acc 0.5 | 0.7 | 0.9 |
|---|---|---|---|
| 50 | 26.7 | 27.5 | 22.7 |
| 150 | 15.9 | 15.6 | 11.8 |
| 300 | 11.3 | 10.9 | 7.9 |

**Table D. Clustering design effect.** DEFF = 1 + (m−1)ρ for 300 lineages with m rows each (e.g. boundary +
mid-interval rows), where ρ is the intra-lineage correlation of correctness.

| m | ρ = 0.3 | ρ = 0.5 | ρ = 0.8 |
|---|---|---|---|
| 2 (600 rows) | n_eff ≈ 462 | ≈ 400 | ≈ 333 |
| 3 (900 rows) | n_eff ≈ 562 | ≈ 450 | ≈ 346 |

**Table E. Approximate 95% half-width of Cohen's κ** (inter-annotator agreement), large-sample formula

| n items | p_o = 0.9, p_e = 0.5 (κ = 0.80) | p_o = 0.8, p_e = 0.5 (κ = 0.60) | p_o = 0.9, p_e = 0.7 (κ = 0.67) |
|---|---|---|---|
| 100 | ±0.12 | ±0.16 | ±0.20 |
| 150 | ±0.10 | ±0.13 | ±0.16 |
| 300 | ±0.07 | ±0.09 | ±0.11 |

### Inferences
- **n = 300 per group is the smallest size at which per-group claims of about 10 pp are defensible.** With n = 150,
  per-group paired MDEs are about 10–14 pp. With n = 50, any per-group comparison short of about 20 pp is noise.
  If the thesis wants per-group statements like "GraphRAG beats flat RAG on T4", 300 is justified. If only pooled
  claims matter, 150 per group (750 total, pooled ±3.6 pp) would suffice.
- **Use the lineage as the analysis unit.** Bootstrap by lineage, as RQ2 in `paper/problem_statement.md` already
  plans. For T5, resample by **amending document**. Today's 19 T5 lineages come from only 3 amending documents
  (JUDGE N4), so T5's effective n is closer to 3 than to 38 rows. No sample-size claim for T5 holds unless T5 spans
  many amending documents.
- **Pre-register the comparisons.** State before seeing results which comparisons will be tested (e.g. B-graph vs
  B-flat per group, and pooled), the test (paired bootstrap by lineage or McNemar on lineage-level outcomes), and a
  multiplicity correction (Holm across groups). Per-group CIs should be Wilson or Bayesian Beta (Bowyer), not
  normal-approximation intervals.
- **κ at n = 300 gives about ±0.07–0.11**, enough to show κ ≥ 0.6 with margin if observed κ ≈ 0.75. Annotator A in
  the D4 cross-check is now an LLM jury (project decision 2026-10-02). The resulting agreement is therefore
  model–human agreement and must be reported as such, not as inter-human κ.

### Gaps
- Real values of p_d (system disagreement) and ρ (intra-lineage correlation) for ViLexTime are unknown until
  baselines run. Tables B and D bracket plausible ranges. Re-estimate them from a pilot of about 100 lineages on the
  dev split, then redo the power analysis (Card et al.'s recommended workflow).
- Miller's DROP/RACE/MGSM ratios and the 969-question example came via tool summary. Verify in the PDF before
  quoting.

---

## Q3. How do recent temporal / knowledge-update benchmarks make answers depend on the date, and how do they guard against version-invariant questions?

### Takeaway
The closest prior work is three 2026 temporal-legal benchmarks (French tax, German statutes, Chinese civil law)
plus HoH, SituatedQA and FreshQA. They make date dependence an explicit acceptance test:
- the gold value must differ between versions, checked automatically;
- questions are built from programmatic diffs;
- reviewers reject editorial-only changes;
- results are reported split by "old-version gold" vs "new-version gold", the axis where models fail most.

### Cited Findings
- **FiscalQA Pro (French tax law, 2026).** Details below are from a tool summary.
  - Corpus of 32,436 article-versions spanning 1938–2031, including future-effective versions. The temporal track
    R3 has 221 curated questions over 33 articles and 7 sub-domains, of which 209 are scored.
  - Candidate "drift points" (value transitions between consecutive versions) are surfaced programmatically. Humans
    write the question text and verify answers. A qualified tax professional reviewed all items, and no
    LLM-generated questions remain.
  - Two filters guard date dependence. (1) A **current-version divergence filter**: the gold date-anchored value
    must not appear in the in-force text. It is absent for 208/209 questions. (2) A **parametric "all-model-hard"
    filter**: any question that any of the 11 evaluated models answered correctly without retrieval, across 4
    draws, was excluded.
  - Conditions: LLM-only, static RAG over a current-only corpus, oracle version, end-to-end. Mean strict accuracy
    was 3.0% / 2.7% / 99.1% / 98.3%, and static RAG retrieved the date-applicable version 0% of the time.
  
  — [Cymbler, Guez & Fabre 2026](https://arxiv.org/abs/2608.09393)
- **German statutory QA (TUM, 2026).** Details below are from a tool summary.
  - 312 pairs in three categories: post-cutoff amendment (115), pre-amendment (113) and multi-provision
    pre-amendment (84).
  - Generated by Gemini 3 Pro Preview. Two senior law students and a lawyer reviewed **697 generated pairs and
    accepted 312 (≈45%)**. Rejections included **editorial-only changes**, multiple independent sub-questions, and
    legal errors.
  - Post-cutoff amendments were chosen after the models' training cutoffs to isolate parametric staleness.
  - Perfect-score rates were 0–5.2% for vanilla models vs 71–87% for RAG.
  - A recency advantage of about 0.20–0.24 appeared only with web search.
  
  — [Prior, Schultz & Grabmair 2026](https://arxiv.org/abs/2605.23497)
- **Chinese temporal legal reasoning (2026).** About 26k civil judgments, split into cases governed by pre-Civil-Code
  statutes and cases under the Civil Code. Models scored 0.01–0.24 on old-version cases vs 0.70–0.84 on new-version
  cases, and 69–94% of errors were "Old→New" misapplications. Models nevertheless memorised the old statutes well
  (> 0.75 similarity), so the failure is in reasoning, not knowledge (tool summary) — [Huang et al. 2026](https://arxiv.org/abs/2608.14610)
- **HoH (ACL 2025)** builds QA from token-level diffs between Wikipedia snapshots combined with LLM pipelines. It is
  a continuously updated QA set. Outdated passages in the retrieval pool cut RAG accuracy and can mislead models even
  when current information is present — [HoH, ACL 2025](https://aclanthology.org/2025.acl-long.301); [arXiv](https://arxiv.org/abs/2503.04800)
- **SituatedQA** found that about 16.5% of NQ-Open questions have context-dependent answers. It crowdsourced
  alternative temporal/geographic contexts with their answers. Models showed a drop of roughly 15 points on
  present-day answers even with updated evidence — [Zhang & Choi, EMNLP 2021](https://arxiv.org/abs/2109.06157)
- **FreshQA** has four categories: never-changing, slow-changing, fast-changing and **false-premise**. For a
  false-premise question, the model must point out the false premise to get credit. Under STRICT evaluation, *all*
  information in the answer must be accurate and up to date — [Vu et al., Findings ACL 2024](https://arxiv.org/abs/2310.03214)
- **CRAG** (NeurIPS 2024 D&B) has 4,409 QA pairs across 5 domains, 8 question types (including false-premise) and
  temporal-dynamism strata from "static" to seconds — [Yang et al. 2024](https://arxiv.org/abs/2406.04744)

### Inferences
Concrete date-dependence rules for ViLexTime. Each is mechanically checkable, in the spirit of FiscalQA's
divergence filter.
- **R1 "answer-changing transition".** For every pair of `as_of` dates in a lineage that the group claims differ,
  the gold short answer of version i must not be contained in version j, after normalisation. This fixes "two dates,
  same answer".
- **R2 "count only answer-changing versions".** For T3, the chain length is the number of versions whose gold short
  answers differ pairwise for *this question*. Agency renaming or purely cosmetic edits do not count. This mirrors
  the German benchmark's "editorial-only" rejection reason. A chain with fewer than 3 answer-distinct versions is
  reclassified to T2 or dropped.
- **R3 "unique target".** The question must be answerable by exactly one unit among the article's siblings (list
  items, points). Annotators check against the full article, not only the gold unit.
- **R4 "no presupposition from one version".** The question must be well posed at every `as_of` in the lineage.
  Otherwise it becomes an explicit false-premise / no-answer item, as in FreshQA and CRAG.
- **R5 "no version cues".** The question must not contain document numbers, amendment dates, "mới/cũ/sau khi sửa
  đổi", or agency names that changed in the chain.
- **Report the old-vs-new gold axis.** Prior work shows the dominant effect is old-version gold vs current-version
  gold (0.01–0.24 vs 0.70–0.84 in the Chinese study). Every ViLexTime table should therefore cross the T-groups with
  "gold is latest version / not latest".
- **FiscalQA's all-model-hard filter is a cautionary example.** It guarantees near-zero LLM-only accuracy by
  construction, which inflates the RAG-vs-LLM gap. Use the divergence filter (R1), not the parametric filter.

### Gaps
- I did not re-verify TimeQA, TempLAMA, StreamingQA or VersionRAG/VersionQA construction details in this session.
- Venue status of the three 2026 legal papers is unknown (arXiv). Treat them as recent preprints.

---

## Q4. LLM-drafted questions: acceptable verification and editing protocol, and what must be disclosed (self-preference)

### Takeaway
Top-venue practice accepts LLM-drafted items only when each one is reviewed by a qualified human under explicit
rejection criteria, with a sizeable rejection rate (German benchmark: 45% accepted). Purely human-written questions
built from programmatic diffs (FiscalQA) are the cleaner option. Two evidence lines make same-family evaluation
risky: LLM-generated test sets favour the generator, and LLM judges favour their own outputs. Disclosure of the
model's role is mandatory under ACL/ARR rules.

### Cited Findings
- German benchmark protocol: an LLM generated 697 pairs, 3 legal reviewers (2 senior law students + 1 lawyer)
  accepted 312, and rejection reasons were recorded (tool summary) — [Prior et al. 2026](https://arxiv.org/abs/2605.23497)
- FiscalQA Pro: drift points were surfaced programmatically, humans wrote the question text, a professional reviewed
  every item, and "no synthetic or LLM-generated questions survive" (tool summary) — [Cymbler et al. 2026](https://arxiv.org/abs/2608.09393)
- LLM-generated benchmarks "systematically favor the model that created the benchmark" (translation tasks). The bias
  comes from both the generated test data and the LLM evaluator, and combining them amplifies it. Low diversity of
  generated source texts drives the bias, and increasing diversity partly mitigates it — [Xu et al. 2025, "Deconstructing Self-Bias in LLM-generated Translation Benchmarks"](https://arxiv.org/abs/2509.26600)
- LLM evaluators recognise and favour their own generations. Self-recognition ability correlates linearly with the
  strength of self-preference (GPT-4, Llama 2) — [Panickssery, Bowman & Feng, NeurIPS 2024](https://arxiv.org/abs/2404.13076)
- ACL Rolling Review's Responsible NLP Checklist asks authors to disclose AI assistance (scope included) and requires
  a Limitations section. Generative AI cannot be an author — [ARR checklist examples, ACL 2026](https://aclanthology.org/attachments/2026.acl-long.752.checklist.pdf); [AI disclosure overview](https://aicards.uni-goettingen.de/ai-disclosure-nlp-research/)
- Repo fact: in the current draft, one model (claude-opus-5-5) wrote 2,273/2,297 questions and 1,137/1,137 short
  answers, assigned 893 labels, and made 20/20 exclusion decisions. 5 opening templates cover 55% of questions — [JUDGE_DATASET.md items 7, C4, V4](../../docs/reports/JUDGE_DATASET.md)

### Inferences
Recommended protocol for "LLM-draft + human edit". It is defensible if every step is logged.
1. Questions are generated *from the diff*: the changed span is given to the drafter, which must target it.
2. Automatic gates R1–R5 from Q3 run before any human sees the item.
3. Every item gets one human editor, using a checklist: touches changed span, unique target, no presupposition, no
   cues, natural phrasing. Record accept / edit / reject with a reason code, as the German benchmark did.
4. A double-annotated subset of ≥ 300 items yields κ (Table E). The legal advisor adjudicates disagreements and all
   T5 items.
5. Report the acceptance rate, edit rate and reason distribution in the datasheet.

Other points:
- **Template vs human vs LLM.** Templates maximise control but create lexical artifacts (V4 already shows 55% from 5
  openings). Pure human writing is the most credible but slowest. LLM-draft + human edit is acceptable when steps
  2–3 are enforced and provenance is stored per item (`question_source`: human / llm_edited / llm_unedited).
- **Self-bias controls.**
  - Evaluate at least one non-Claude model family as the headline LLM baseline.
  - Do not use a Claude model as the judge of Claude-drafted items.
  - Run a **provenance ablation**: compare per-model accuracy on human-written vs LLM-drafted subsets. A
    Claude-specific gain on the LLM-drafted subset would indicate generator bias.
  - Use multiple drafter models, or diversify prompts, to counter Xu et al.'s diversity mechanism.
- **What must be disclosed.**
  - The drafter model and version, and which fields it wrote (question, short answer, labels).
  - Acceptance and edit rates.
  - Whether any annotator was an LLM. This applies here: annotator A of D4 is now an LLM jury.
  - The judge model and its calibration.
  - The ACL/ARR AI-assistance checklist item.

### Gaps
- I found no venue rule specifying a minimum human-edit rate for LLM-drafted benchmark items. Acceptability is
  judged case by case by reviewers.
- No published measurement of self-preference bias exists for Vietnamese legal QA specifically.

---

## Q5. Scoring unanswerable / "no longer in force" items and hedging answers

### Takeaway
Score abstention as its own class, with a penalty for confident wrong answers. CRAG uses +1 / 0 / −1, and FreshQA's
STRICT mode requires every stated fact to be current. Report coverage/risk or answerable vs unanswerable accuracy
separately. Contrastive scoring (credit only if the answer excludes spans unique to other versions) closes the
"list all versions" loophole that currently earns 0.951 accuracy.

### Cited Findings
- CRAG scoring: perfect = 1, acceptable = 0.5, **missing ("I don't know") = 0**, incorrect/hallucinated = **−1**, so
  wrong answers are penalised below abstention — [CRAG, NeurIPS 2024](https://arxiv.org/abs/2406.04744)
- FreshQA STRICT mode gives no credit if *any* stated information is inaccurate or outdated. False-premise questions
  need the premise debunked — [Vu et al. 2024](https://arxiv.org/abs/2310.03214)
- SQuAD 2.0 added more than 50k unanswerable questions, written adversarially by crowdworkers to resemble
  answerable ones, so systems must abstain when no answer is supported (not re-fetched in this session) — [Rajpurkar, Jia & Liang, ACL 2018](https://aclanthology.org/P18-2124/)
- Selective QA (Kamath et al. 2020) defines a coverage–risk trade-off: coverage is the fraction answered, and risk is
  the error on answered items. Softmax-based abstention fails under domain shift, and a trained calibrator works
  better — [Kamath, Jia & Liang, ACL 2020](https://aclanthology.org/2020.acl-main.503)
- AbstentionBench covers 20 datasets, including **outdated information**, false premises and underspecification.
  Abstention is unsolved, scaling helps little, and reasoning fine-tuning degrades abstention by 24% on average — [Kirichenko et al., NeurIPS 2025](https://arxiv.org/abs/2506.09038)
- Repo facts:
  - A synthetic "print every version" submission scores Accuracy 0.951 and TCS 1.000.
  - "Always abstain" scores 0.049.
  - All no-answer rows are `provision_repealed` (112/2,297 = 4.9%).
  
  — [JUDGE_DATASET.md C2, §5 C3, D](../../docs/reports/JUDGE_DATASET.md)

### Inferences
- **Three-way outcome per item:** correct, abstain/"not in force", or wrong. Report:
  - (a) accuracy on answerable items;
  - (b) correct-abstention rate on no-answer items, i.e. abstention recall, plus precision of "not in force"
    claims;
  - (c) a CRAG-style truthfulness score (+1 / 0 / −1) as the headline, so confident use of repealed text costs more
    than abstaining.
- **Contrastive span accuracy for hedging.** An item is correct only if the answer contains the gold span **and**
  contains no span unique to another version of the same lineage. This is FreshQA STRICT applied to versions, and it
  is the fix JUDGE C2 proposes. Keep "print all versions" and "always abstain" as mandatory sanity probes. Both must
  score near the floor.
- **No-answer share.** At 4.9%, no-answer items are too few for a stable abstention metric. If T6 is a full group
  of 300 lineages with half its rows post-repeal, about 150 no-answer rows give ±8 pp on abstention recall
  (Table A).

### Gaps
- No source found on the best weighting for legal QA specifically (e.g. whether −1 is the right penalty). This is a
  policy choice and should be stated as such.

---

## Q6. Metric validity: LLM-as-judge calibration and human correlation

### Takeaway
Use deterministic contrastive span matching as the primary metric. The judge's own temporal bias is a direct
threat: FiscalQA avoided LLM judges for exactly this reason. If a judge is used, calibrate it on a stratified human
set, report κ (not percent agreement), and bias-correct accuracy with the judge's sensitivity and specificity.

### Cited Findings
- FiscalQA Pro deliberately uses deterministic matching and "never LLM-as-judge" because frontier models exhibit the
  temporal bias being measured (tool summary) — [Cymbler et al. 2026](https://arxiv.org/abs/2608.09393)
- Judging the Judges (13 judges, 9 exam-taker models) found the following:
  - Cohen's κ distinguishes judges better than percent agreement, and judges with high percent agreement can still
    assign very different scores.
  - Only the best and largest judges align reasonably with humans, and even they can be up to 5 points off.
  - The lexical "Contains" metric ranked models better than some well-aligned judges.
  
  — [Thakur et al., GEM 2025](https://arxiv.org/abs/2406.12624)
- Raw "fraction judged correct" is biased whenever the judge has imperfect sensitivity or specificity. A
  bias-adjusted estimator can correct it, using CIs that combine test-set and calibration-set uncertainty, and an
  adaptive allocation of calibration labels shortens the CIs — ["How to Correctly Report LLM-as-a-Judge Evaluations", arXiv 2511.21140, 2025 (authors not verified)](https://arxiv.org/abs/2511.21140)
- The German benchmark validated its Gemini judge on 48 expert ratings (κ = 0.751, r = 0.853) (tool summary) — [Prior et al. 2026](https://arxiv.org/abs/2605.23497)

### Inferences
- **Calibration set.** Use about 200–300 human-labelled responses, stratified by group, by gold position
  (latest / non-latest) and by response type. Response types must include hedged multi-version answers,
  abstentions and paraphrases. With 300 items, the judge's sensitivity and specificity are estimated within about
  ±5–6 pp (Table A).
- **Reporting.** Give κ, sensitivity and specificity per group. Apply the bias correction of arXiv 2511.21140 to reported
  accuracies. Do not use a Claude-family judge on Claude-family outputs (Panickssery et al.).
- **Judge recency-bias probe.** Feed the judge the "latest version" probe answers on items whose gold is an older
  version. Any credit it gives is a direct measure of the judge's recency bias.

### Gaps
- I did not verify which calibration sample size arXiv 2511.21140 recommends. Their method is adaptive.

---

## Q7. Contamination, held-out test and date-based splits

### Takeaway
Legal source texts are public and almost certainly in pretraining, so the protection that matters is (a) keeping
the *question–answer pairs* out of future training data, and (b) stratifying results by whether the governing
change came after a model's training cutoff. Standard tools are canary GUIDs, encrypted or no-derivatives release,
a private test split, and time-windowed analysis.

### Cited Findings
- Jacovi et al. 2023 recommend:
  - encrypting test data with a public key, or a password-protected archive, and releasing the key alongside;
  - a "No Derivatives" licence (e.g. CC BY-ND 4.0), so the data cannot be redistributed unencrypted;
  - avoiding non-key obfuscation, which crawler pipelines may automatically undo.
  
  — [Jacovi et al., EMNLP 2023](https://arxiv.org/abs/2305.10160)
- FiscalQA Pro embeds a BIG-bench-style canary GUID in benchmark files (tool summary) — [Cymbler et al. 2026](https://arxiv.org/abs/2608.09393)
- The German benchmark chose amendments after the evaluated models' training cutoffs to isolate staleness (a
  post-cutoff category) — [Prior et al. 2026](https://arxiv.org/abs/2605.23497)
- LiveBench replaces about 1/6 of its questions monthly and withholds new ones for a month. LiveCodeBench tags each
  problem with its date and evaluates only post-cutoff windows. Reported drops of 20–40% on post-cutoff problems for
  some models come from a secondary summary — [LiveBench repo](https://github.com/livebench/LiveBench); [LiveCodeBench overview](https://alphaxiv.org/overview/2403.07974v2)
- BetterBench lists contamination safeguards among its implementation criteria, and few benchmarks implement them — [BetterBench](https://arxiv.org/abs/2411.12990)

### Inferences
- Add a per-item field `change_after_cutoff[model]`: does the governing transition's effective date fall after that
  model's documented training cutoff? Report LLM-only accuracy split by it. This is the German "post-cutoff" design
  for free.
- Release the dev split openly. Release test as an encrypted archive with a canary GUID and CC BY-ND, or keep test
  gold private behind a scoring script.
- Drop or flag `as_of` dates after the corpus snapshot (JUDGE V2: 6 rows up to 2027-03-01). Future law can change
  before that date, so the gold is not yet fixed.

### Gaps
- No source quantifies how much Vietnamese legal text is in specific models' pretraining data.

---

## Q8. Split design (grouping, dev/test sizes, stratification)

### Takeaway
Split by **document**, so that every lineage of a target document, and for T5 every lineage of an amending
document, falls in one split. Stratify by group and `as_of` mode. Keep dev small but large enough for judge
calibration and prompt development, and keep test large enough for the power targets.

### Cited Findings
- Grouped resampling at the article level is used for CIs in FiscalQA (tool summary) — [Cymbler et al. 2026](https://arxiv.org/abs/2608.09393)
- Clustered items need clustered SEs; ignoring clustering can understate SE by up to about 3× (DROP) — [Miller 2024](https://arxiv.org/abs/2411.00640); [Bowyer et al. 2025](https://arxiv.org/abs/2503.01747)
- Repo plan: 20/80 dev/test by document, same lineage in the same split, T5 in test. 50/117 documents holding κ
  lineages also hold non-κ lineages — [JUDGE_DATASET.md §7.4](../../docs/reports/JUDGE_DATASET.md)

### Inferences
- With no model training, a 20% dev split (≈ 60 lineages/group at 300) suffices for prompt and threshold tuning
  plus part of the judge calibration. The 80% test split (≈ 240 lineages/group) gives about ±6 pp per group
  (between the 150 and 300 rows of Table A).
- Put the κ / double-annotated subset proportionally in both splits, or entirely in test. Never tune on items whose
  labels are still under adjudication.
- If T5 stays scarce, assign by amending document. Accept that T5 is test-only and reported with exact CIs.

### Gaps
- I found no authoritative source fixing a dev/test ratio for evaluation-only benchmarks. 20/80 is a convention.

---

## Q9. Choosing the 5 groups; handling a scarce category; keeping a non-temporal control

### Takeaway
Choose groups by four criteria: (1) a distinct failure hypothesis with a distinct trivial-baseline signature;
(2) supply that reaches the quota *without* padding from a few source documents; (3) legal validity confirmed by
the advisor; (4) comparability with prior work. On these criteria the recommended main five are **T1 (control),
T2, T3, T4, T6**, with **T5 as a separately reported challenge subset** (not padded, not merged into T6).

### Cited Findings
- Prior temporal benchmarks keep a stable or non-changing control alongside changing categories: FreshQA has
  never-changing vs slow- and fast-changing, and CRAG stratifies from static to seconds-level dynamism — [FreshQA](https://arxiv.org/abs/2310.03214); [CRAG](https://arxiv.org/abs/2406.04744)
- Prior legal-temporal benchmarks use few, sharply defined categories of unequal size: German 115/113/84, and
  FiscalQA's single temporal track of 209 scored items — [Prior et al. 2026](https://arxiv.org/abs/2605.23497); [Cymbler et al. 2026](https://arxiv.org/abs/2608.09393)
- Small categories are common and statistically fragile. FrontierMath has 23 categories, some with fewer than 3
  items, which motivates Bayesian or Wilson intervals rather than CLT — [Bowyer et al. 2025](https://arxiv.org/abs/2503.01747)
- Aggregation across categories should not rely on a naive mean alone — [Vote'n'Rank](https://aclanthology.org/2023.eacl-main.48)
- Repo facts:
  - T5 currently has 19 lineages / 38 boundary rows from **3 amending documents (10/7/2)**. One of these documents
    does not state a retroactive date in its effectiveness clause.
  - The T5 definition was changed to follow Article 152 (the "favourable" clause was dropped).
  - H3, loss of validity via a repealed parent, has only 12 lineages.
  - T1's latest/earliest probes score 1.000, as designed, since there is only one version.
  
  — [JUDGE_DATASET.md items 4–5, N4, §5 C3](../../docs/reports/JUDGE_DATASET.md)

### Inferences
Decision logic, criterion by criterion:
- **T1 control: keep it, possibly smaller.** It supplies *discriminant validity*. Without T1 you cannot tell whether
  a GraphRAG gain on T2–T6 is temporal or just better retrieval or QA. It is also the reference row for
  "temporal-error rate = accuracy(T1) − accuracy(Tk)". It needs no hard annotation, so it is cheap. If the
  annotation budget binds, T1 can drop to 150 lineages (±7.9 pp), because it serves as a baseline rather than a
  comparison target. That frees 150 lineages for T6 or T4. Do not drop it: comparability with FreshQA/CRAG-style
  stratification and the RQ3 ablations both rely on a non-temporal floor.
- **T5 retroactive: do not merge into T6.** Retroactivity (effective date before issuance) and partial repeal (unit
  invalid, no answer) are different capabilities with different correct outputs (a specific version vs abstention).
  Merging them would destroy construct validity for both. Reaching 300 T5 lineages from about 3 amending documents
  would be padding with near-duplicates whose effective n is about the number of documents (Table D logic).
  Recommendation:
  - Report T5 as a **challenge / diagnostic subset**: as many lineages as legally valid supply allows, ideally from
    ≥ 10 distinct amending documents, with every item signed off by the legal advisor.
  - Give Wilson or Bayesian CIs at document-cluster level, and label the result "illustrative".
  - Exclude T5 from the macro-average.
  
  The fifth main group then becomes **T6**, which has its own capability (unit-level repeal / abstention). T6
  supplies the no-answer rows that the abstention metric needs (Q5).
- **T3: keep, with the "answer-distinct versions ≥ 3" rule (R2).** This prevents cosmetic chains. Move boundary
  `as_of` dates off the version-start+1 position (JUDGE N3), because the closest-date probe solves them at 100%.
- **T4: keep, with a cap.** Its similarity range is 0.901–0.997 (median 0.957), so it is a real trap. It needs R1
  and contrastive scoring to be valid.
- **Quota vs CI.** The rule from the statistics literature is "power, not padding". A group that cannot reach its
  quota from enough independent source documents should be reported separately with honest CIs rather than filled
  with clustered near-duplicates.
- **Cross-cutting strata** to report in every table regardless of grouping:
  - gold version = latest vs older (the main effect in Huang et al. 2026);
  - `as_of` mode (boundary vs mid-interval);
  - transition after model cutoff (Q7).
- **Feasibility.** 1,500 lineages × (edit + check) by 16 Nov 2026 is about 33 lineages per calendar day. Double
  annotation of every item is unlikely. Double-annotate a stratified ≥ 300 subset for κ and single-annotate the
  rest with adjudication of flagged items. This inference is not sourced; I found no benchmark-specific norm for
  the fraction to double-annotate.

### Gaps
- The supply of T5 lineages under the Article 152 definition in the full corpus is unknown to me. The decision
  depends on a corpus count of distinct amending documents with retroactive effect.
- I found no published benchmark that explicitly pads vs separates a scarce category and compares the outcomes.
  The recommendation rests on the power and clustering arguments above.
