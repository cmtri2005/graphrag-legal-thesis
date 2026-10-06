# Prior art for ViLexTime: how temporal and legal QA benchmarks were built, sized, annotated and validated

Scope note. These notes extend `research_notes/Schema bộ dữ liệu ViLexTime/temporal_qa_schemas.md` and
`.../legal_qa_schemas.md`. Those cover record-level field names. They are not repeated here. These notes
cover construction, size, annotation, verification and IAA. Numbers come from the papers' full text, read
on 02/10/2026 through arXiv HTML, ar5iv or PDF text extraction. Items marked **(search snippet)** came from
search-engine summaries and were not read in the primary text, so check them before quoting.
Items marked **(earlier notes)** are already verified in the two schema notes.

Session caveat: the web tools hit a usage limit partway through. Several datasets the brief listed
(Complex-TR, TimeBench details, TempLAMA size, LeCaRD/LeCaRDv2, CAIL, STARD, JEC-QA, LexGLUE, LEXam, COLIEE 2025)
were **not** re-read in this session. They appear only under Gaps.

---

## Q1. Temporal QA benchmarks: how they were built, how gold answers that change over time were verified, and whether IAA was reported

### Takeaway
Classic temporal QA sets (TimeQA, TempLAMA, TempReason, TemporalWiki, ArchivalQA, ChroKnowBench) build their gold
answers **automatically from a time-stamped KB or from diffs between snapshots**. Human checking, when there is any,
is a crowd pass over facts (TimeQA: 41.6% of segments revised) or a filter on generated questions (StreamingQA,
ArchivalQA). They almost never report an agreement coefficient. The sets that do report IAA are human-built:
SituatedQA (Fleiss κ 0.56–0.62) and FreshQA (99%/96% rater agreement). The most reusable time-sensitivity designs
are four: **same question asked at several dates** (SituatedQA, TempLAMA), **changed-vs-unchanged probes**
(TemporalWiki, ChroKnowBench), **explicit question date plus recent-vs-past split** (StreamingQA), and
**category by how fast the answer changes, with a false-premise class** (FreshQA, 125 test items per class).

### Cited Findings

**TimeQA (Chen et al., NeurIPS 2021 D&B)**
- Construction: about 150K time-evolving facts were mined from Wikidata using the qualifiers P580 (start), P582 (end) and P585 (point in time). They were aligned to Wikipedia by four rules: hyperlink, exact string match, TF-IDF > 40%, or else marked unanswerable. — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)
- Verification on AMT: workers needed >98% acceptance and >1,000 approved HITs, and were paid $1.0 per HIT (about 5 minutes). 5,500 fact–object pairs were submitted. Workers could correct objects and toggle answerable/unanswerable. "Roughly 41.6% of the segments are revised". Two HITs per batch were spot-checked, with an "overall acceptance rate … maintained between 85-90%". The release has 5,060 "golden" (text, fact) pairs. — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)
- Segment statistics: 12% "[unanswerable]", 7% multiple objects, 80% exactly one object, about 4 segments per fact, "over 60 different relations". This conflicts with the "70 relations" recorded in the earlier notes, so treat the relation count as unsettled. — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)
- Splits (easy/hard): train 14,308/14,681; dev 3,021/3,087; test 2,997/3,078. Humans also paraphrased 1,171 train and 989 test questions. — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)
- Human performance: easy 89.0 EM / 93.3 F1; hard 87.0 / 91.1. Best model (FiD): easy 60.5 / 67.9; hard 46.8 / 54.6. No κ is reported. Quality is stated only as an acceptance rate. — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)

**SituatedQA (Zhang & Choi, EMNLP 2021)**
- About 16.5% of NQ-Open questions turned out to be context-dependent. — [arXiv 2109.06157](https://arxiv.org/abs/2109.06157)
- Three crowdsourced stages:
  - Identification: 3-way yes/maybe/no labels, with "at least two" annotators required to agree.
  - Context/answer collection: for temporal questions, workers write a timeline with "the current answer, the previous answer, as well as the start and end transition timestamps".
  - Validation: a separate annotator marks each item correct or incorrect.
  - Pay: $0.15 per identification HIT and $0.40 per collection/validation HIT. — [ar5iv 2109.06157](https://ar5iv.labs.arxiv.org/html/2109.06157)
- Each answer yields three example types: **Start** (asked at the answer's first timestamp), **Sampled** (timestamps between the transitions, "a maximum of two" per answer) and **Static** (questions that do not depend on time). This is the closest classic analogue to ViLexTime's as_of sampling inside a version's validity interval. — [ar5iv 2109.06157](https://ar5iv.labs.arxiv.org/html/2109.06157)
- IAA (Fleiss κ): temporal identification 0.62; geographic identification 0.56; temporal context/answer 0.57; geographic context/answer 0.56. — [ar5iv 2109.06157](https://ar5iv.labs.arxiv.org/html/2109.06157)
- Sizes:
  - Temporal context/answer triples: 6,009 train / 3,423 dev / 2,795 test.
  - Geographic: 3,548 / 1,398 / 505.
  - Identification stage: temporal 4,438 / 2,572 / 1,962. — [ar5iv 2109.06157](https://ar5iv.labs.arxiv.org/html/2109.06157)
- Time-sensitivity evaluation: answers were re-annotated against the 20 Feb 2021 Wikipedia dump. Questions were split into "stable" (answer unchanged since 2018) and "updated". Models trained on 2018 data lose about 15 points on present-day answers. Metric: EM. Human performance was estimated on 100 samples. — [ar5iv 2109.06157](https://ar5iv.labs.arxiv.org/html/2109.06157); [arXiv 2109.06157](https://arxiv.org/abs/2109.06157)

**StreamingQA (Liška et al., ICML 2022)**
- Corpus: WMT English news 2007–2020, about 11M articles. Evaluation set: about 36.4K questions, of which "28k generated" and "8.8k human written". Train 100K, validation 10K. Each eval question has three reference answers. — [ar5iv 2205.11388](https://ar5iv.labs.arxiv.org/html/2205.11388)
- Human writers were native English speakers in the US or UK with a university education. Each wrote about 15 questions, phrased "as if they were asking another person". Question dates were sampled uniformly within ranges tied to the article date. — [ar5iv 2205.11388](https://ar5iv.labs.arxiv.org/html/2205.11388)
- Generated questions came from few-shot prompting of a large LM, conditioned on the article and an answer span. Two-stage human filter:
  1. Questions were kept as "factual, unambiguous, grammatical" only if "3 annotators … agree".
  2. Annotators then had to be able to answer the question from the passage. — [ar5iv 2205.11388](https://ar5iv.labs.arxiv.org/html/2205.11388)
- Evaluation: a recent subset (articles Dec 2019–2020) vs a past subset (2007 onward), evaluated quarterly through 2020. Metrics: F1 and EM. The per-record `written_or_generated` flag is in the earlier notes. — [ar5iv 2205.11388](https://ar5iv.labs.arxiv.org/html/2205.11388)

**FreshQA (Vu et al., FreshLLMs; ACL Findings 2024)**
- 600 questions in total: test 500 (**125 per category**) and dev 100 (25 per category), plus 15 few-shot demos. The four categories are never-changing, slow-changing, fast-changing and false-premise. Each has one-hop and multi-hop variants. — [ar5iv 2310.03214](https://ar5iv.labs.arxiv.org/html/2310.03214)
- Writers: "NLP researchers (including the authors and their colleagues) and online freelancers" from Upwork, paid $2 per example. Each answer records "the year the answer to the question last changed and an URL to a reputable website". Questions whose answer changes more often than weekly are excluded. The authors "commit to updating the dataset regularly". — [ar5iv 2310.03214](https://ar5iv.labs.arxiv.org/html/2310.03214)
- Evaluation modes:
  - RELAXED grades only the primary answer.
  - STRICT also requires "all of the facts in the answer" to be accurate, so a correct answer that contains an outdated or hallucinated fact fails.
  - Two authors rated 100 answers independently: 99% agreement under RELAXED, 96% under STRICT.
  - The automatic FreshEval agrees with humans 96.5% (RELAXED) and 96% (STRICT).
  - Over 50K human judgments were collected in total. — [ar5iv 2310.03214](https://ar5iv.labs.arxiv.org/html/2310.03214); [arXiv 2310.03214](https://arxiv.org/abs/2310.03214)

**RealTimeQA (Kasai et al., NeurIPS 2023 D&B)**
- Source: weekly news quizzes from CNN, USA Today and The Week, about 10 questions each, so about 30 per week. As of 2 June 2023 it had 1,470 real-time QA pairs plus 2,886 from earlier collection. Questions and answers are "human-written" by the news sites and scraped by script. — [ar5iv 2207.13332](https://ar5iv.labs.arxiv.org/html/2207.13332)
- Format: multiple choice in two settings, standard and **NOTA ("none of the above")**, plus a generation setting. Metrics: accuracy, EM and F1. About 12% of questions turned out not to need current information. Humans scored 96.7% on 300 sampled questions. When retrieval returns stale documents, GPT-3 "still generates an outdated answer". — [ar5iv 2207.13332](https://ar5iv.labs.arxiv.org/html/2207.13332)

**ArchivalQA (Wang, Jatowt, Yoshikawa, SIGIR 2022)**
- Source: NYT Annotated Corpus, 1 Jan 1987 – 19 Jun 2007. A T5-base model trained on SQuAD 1.1 generated 6,408,036 questions. A filtering cascade reduced them to 532,444 QA pairs from 88,431 articles:
  - syntactic and temporal rules;
  - a content-specificity classifier (RoBERTa, 84.49% accuracy);
  - a temporal-ambiguity classifier (BERT, 81.82%), trained on 5,500 hand-labelled questions;
  - a triple-based classifier (86.74% precision), trained on 10K hand-annotated samples. — [ar5iv 2109.03438](https://ar5iv.labs.arxiv.org/html/2109.03438)
- Human evaluation: 5K QA pairs rated by 10 graduate students on a 5-point scale. Fluency 4.80, answerability 4.57, relevance 4.79, non-ambiguity 4.60. No IAA reported. — [ar5iv 2109.03438](https://ar5iv.labs.arxiv.org/html/2109.03438)
- Splits: 425,956 / 53,244 / 53,244. Subsets: Easy and Hard (100K each); Time and NoTime (75K each). — [ar5iv 2109.03438](https://ar5iv.labs.arxiv.org/html/2109.03438)

**TemporalWiki (Jang et al., EMNLP 2022)**
- Built from monthly Wikipedia and Wikidata snapshots, Aug–Dec 2021. TWiki-Probes split facts into **Changed** and **Unchanged**. Per period, Unchanged/Changed: 0809 6,935/1,776; 0910 7,340/1,982; 1011 7,313/1,358; 1112 7,293/1,951. — [ar5iv 2204.14211](https://ar5iv.labs.arxiv.org/html/2204.14211)
- Quality control is automatic only: alignment checks plus heuristics (substring overlap, objects longer than 5 words, rebalancing). No manual verification is described. Stated limitation: "Not all Wikipedia/Wikidata updates equate to actual updates of world knowledge", and knowledge deletion is not covered. — [ar5iv 2204.14211](https://ar5iv.labs.arxiv.org/html/2204.14211)

**TempReason (Tan et al., ACL 2023)**
- Source: Wikidata dump of 20 Nov 2022. Sizes (train/dev/test): L1 400,000/4,000/4,000; L2 16,017/5,521/5,397; L3 13,014/4,437/4,426. Time span 634–2023. Three settings: closed-book, open-book and reasoning QA. Metrics: EM/F1. — [ar5iv 2306.08952](https://ar5iv.labs.arxiv.org/html/2306.08952)
- The paper "does not explicitly describe human verification procedures for the test set". — [ar5iv 2306.08952](https://ar5iv.labs.arxiv.org/html/2306.08952)

**MenatQA (Wei et al., EMNLP Findings 2023)**
- 2,853 samples derived from TimeQA:
  - scope 1,448 (extraction 998, reasoning 450);
  - order 857;
  - counterfactual 548.
- Annotators were "college students majoring in English-related fields", with "annotator training and two-round validation". No κ is reported. 85.7% of questions are answerable and 14.2% unanswerable. Primary metric: EM. — [ar5iv 2310.05157](https://ar5iv.labs.arxiv.org/html/2310.05157)

**ChroKnowledge / ChroKnowBench (Park et al., ICLR 2025)**
- Domains:
  - General: Wikidata 2010–2023, 8 relations, 8,330 dynamic / 8,302 static.
  - Biomedical: UMLS 2020–2024, 14 relations, 7,345 / 7,345.
  - **Legal: US Code of Federal Regulations 2010–2023, 6 relations, 3,142 dynamic / 3,142 static, QA-like format.**
  - Time-invariant: commonsense (CSKG) 24,788; math 2,585. — [arXiv html 2410.09870](https://arxiv.org/html/2410.09870)
- Gold answers: objects are tracked year by year by "de-duplication and strict exact string matching". Missing years are filled with the object from the earlier timestamp. Human verification "appears limited". Questions come in generation, 4-option MCQA and T/F templates, with fuzzy matching at token_set_ratio ≥ 70. Labels are Correct / Partial Correct / Incorrect, refined into Known / Partial Known / Cut-off / Unknown. — [arXiv html 2410.09870](https://arxiv.org/html/2410.09870)

**Other temporal sets**
- **Test of Time (ICLR 2025)**: fully synthetic graphs. tot_arithmetic 2,800 test; tot_semantic 1,850; tot_semantic_large 46,480; 7 question types. **(earlier notes)** — [HF baharef/ToT](https://huggingface.co/datasets/baharef/ToT/blob/main/README.md)
- **TRAM (Wang & Zhao, ACL Findings 2024)**: 10 tasks (order, arithmetic, frequency, duration, …), 526.7K multiple-choice questions. Best model is "significantly behind human performance". **(search snippet)** — [arXiv 2310.00835](https://arxiv.org/html/2310.00835v3)
- **HoH (2025)**: built from Wikipedia snapshots using "token-level diff algorithms combined with LLM pipelines". Outdated passages both distract the model and mislead it into harmful outputs. Stated limitation: outdated passages are historical versions of the *same* article, so they are very similar to each other. **This matches ViLexTime T4 (near-identical versions).** Size not verified. — [arXiv 2503.04800](https://arxiv.org/abs/2503.04800); limitation via **(search snippet)** of [arXiv 2503.04800](https://arxiv.org/pdf/2503.04800)
- **VersionQA (VersionRAG, arXiv 2510.08109)**:
  - 100 "manually curated" questions over 34 versioned technical documents (Apache Spark, Bootstrap, Node.js; more than 700 pages).
  - Six types: Content Retrieval (standard / complex / version-specific), Version Listing & Inquiry, and Change Retrieval (explicit / implicit).
  - 60% of the questions are version-sensitive. **(search snippet)** — [arXiv 2510.08109](https://arxiv.org/html/2510.08109v1)
- Survey verdict on the whole field: "minimal discussion of unanswerable-question handling". **(earlier notes)** — [arXiv 2505.20243](https://arxiv.org/html/2505.20243v1)

### Inferences
- In this literature, an automatically built gold is the norm, not a weakness reviewers punish. What reviewers do expect
  is a **quantified human check of the automatic gold**: TimeQA's 41.6% revision rate, ArchivalQA's 5K-item human rating,
  StreamingQA's 3-annotator filter. ViLexTime's "gold from the TKG plus human verification" fits that pattern. It should
  report the analogous number, i.e. the share of auto-gold that annotators had to correct, broken down by T-group.
- The SituatedQA Start/Sampled design maps directly onto as_of sampling. Use one as_of at the version start (boundary)
  and one or two strictly inside the validity interval. Report boundary items separately, because effective-date
  boundaries (same-day, off-by-one) are where KG-built gold is most likely wrong.
- FreshQA's STRICT mode is the general-domain counterpart of ViLexTime's TVER/VCR. An answer is wrong if it contains
  any outdated fact, even when the main answer is right.
- Almost none of the KB-derived temporal sets report κ. A 2-annotator verification with κ would put ViLexTime above
  TimeQA, TempReason, TemporalWiki, ChroKnowBench and ArchivalQA on this criterion.

### Gaps
- Complex-TR (Tan et al., 2023/2024), TimeBench (beyond the aggregator facts in the earlier notes), TempLAMA's exact size,
  TAQA, PAT-Questions, DynamicQA, EvolvingQA and UnSeenTimeQA: construction and sizes were not read this session.
- HoH size and human-verification figures: not obtained. The abstract page does not give them.
- VersionQA and TRAM figures come from search snippets only.

---

## Q2. Legal QA/IR benchmarks: those with time or versions, and how general legal benchmarks were built

### Takeaway
2025–2026 produced a cluster of **version-aware legal benchmarks**:
- German statutory QA: 312 items, ICAIL 2026.
- FiscalQA Pro: French tax, 221/209 items.
- TALD: Chinese civil-law applicable version.
- LexKairos: Chinese, 3,796 items, with "Effective Version Identification" and "Effective Status Verification" tasks.
- CALRK-Bench: Korean, 479 items.
- LawShift: Chinese LJP under 31 synthetic change types, NeurIPS 2025 D&B.
- LeKUBE: synthetic Chinese statute updates.
- ChroKnowBench: CFR yearly changes.

All of them build gold largely automatically from version histories or court-cited versions, or generate items with an
LLM, and then have a small expert check. **None reports a κ for that check.** The German set is the closest match to
ViLexTime's protocol: LLM-generated items reviewed by two senior law students and one lawyer, 697 → 312 accepted.
It reports κ only for its LLM judge against an expert (0.751). FiscalQA Pro is the closest match in gold construction:
versions from the official Légifrance API, transitions scanned automatically, every item reviewed by one tax
professional, and metrics separated into strict accuracy and *provenance*.

### Cited Findings

**"Asking For An Old Friend" — German statutory temporal QA (Prior, Schultz, Grabmair; ICAIL 2026, best-paper nominee)**
- Construction:
  - All 312 pairs were "constructed synthetically using Gemini 3 Pro Preview" from "prompt templates".
  - Source: buzer.de, "a privately operated resource offering unofficial consolidated versions of German federal law along with their in-force dates".
  - Six statutes: BGB, StPO, AO, EStG, BauGB, HGB.
  - Questions embed "a fact date within the older version's validity period" or a date after the model's cutoff. A regex extracts the as-of date at RAG time. — [arXiv html 2605.23497](https://arxiv.org/html/2605.23497)
- Validation:
  - Reviewers: "two senior law students and one fully-qualified lawyer".
  - 697 generated → 312 accepted, i.e. 44.8% acceptance (computed).
  - Rejection reasons: non-substantive edits, multiple independent sub-questions, "identical legal consequences regardless of version", and legal errors.
  - "Inter-annotator agreement: Not reported for the validation process itself." — [arXiv html 2605.23497](https://arxiv.org/html/2605.23497)
- Categories:
  - Post-Cutoff Amendment 115; Pre-Amendment 113; Multi-Provision Pre-Amendment 84.
  - 39 duplicates are kept on purpose for consistency checks.
  - No train/dev/test split. — [arXiv html 2605.23497](https://arxiv.org/html/2605.23497)
- Evaluation:
  - LLM-as-judge validated on 48 questions stratified by type and domain, giving 192 answers scored by an independent legal expert.
  - Overall r = 0.853, κ = 0.751, MAE = 0.123.
  - By criterion: **outcome κ = 0.860; legal-basis κ = 0.549**.
  - By question type: post-cutoff κ = 0.821; pre-amendment κ = 0.696.
  - Five LLMs × four settings (vanilla, web search, two RAG variants). — [arXiv html 2605.23497](https://arxiv.org/html/2605.23497); [arXiv abs](https://arxiv.org/abs/2605.23497)
- Limitations stated: "our evidence for recency bias is mixed"; a multi-provision "reasoning ceiling"; German civil law only. — [arXiv html 2605.23497](https://arxiv.org/html/2605.23497)

**FiscalQA Pro — "Temporal Misgrounding in Legal RAG: A Versioned-Corpus Benchmark for French Tax Law" (Cymbler, Guez, Fabre; arXiv 2608.09393, Aug 2026)**
- Corpus:
  - Built from the PISTE Légifrance API (`/consult/getArticleByCid` returns an article's full version history).
  - "32,436 article-versions across six tax codes", spanning 1938–2031.
  - 69,208 version-aware links from court decisions to specific article versions. — [arXiv html 2608.09393](https://arxiv.org/html/2608.09393)
- Item creation:
  - `r3_factory.py` "scans version histories for value transitions", i.e. automatic candidates.
  - The authors then "draft the question text, verify the value against the corpus version".
  - Every item was "reviewed for correctness by a qualified French tax professional", a single reviewer. No IAA.
  - Items carry an explicit date anchor, e.g. "fiscal years opening on or after 1 January 2018". — [arXiv html 2608.09393](https://arxiv.org/html/2608.09393)
- Size and exclusions:
  - 221 released, 209 scored ("expert-reviewed, all-model-hard"), over 33 articles.
  - The 12 excluded: 4 whose values are "annually INSEE-indexed", which were "conservatively excluded", and 8 "curation errors or ill-posed".
  - Single frozen eval set, no splits. — [arXiv html 2608.09393](https://arxiv.org/html/2608.09393)
- Results by condition:
  - Parametric: 3.0% strict.
  - Static RAG: 2.7% strict and **0% provenance**, i.e. it "never retrieves date-applicable version".
  - Versioned oracle RAG: 99.1%.
  - End-to-end versioned RAG: 98.3% strict, 99% provenance. — [arXiv html 2608.09393](https://arxiv.org/html/2608.09393)
- The fetched summary of the category breakdown (R1–R4) was internally inconsistent, so do not quote per-category counts. Stated limitations: French tax only; 221 items is small; only "current-law substitution" is fully exercised. — [arXiv html 2608.09393](https://arxiv.org/html/2608.09393)
- This paper is the primary source for the term **"temporal misgrounding"**, which `legal_qa_schemas.md` Q7 left unsourced. — [arXiv html 2608.09393](https://arxiv.org/html/2608.09393)

**TALD — "When Do LLMs Apply the Wrong Law?" (arXiv 2608.14610, 2026)**
- Data: 26,000 Chinese civil judgments from China Judgments Online, split into pre-Civil-Code (Property and Contract Law) and post-Code (Civil Code, 2021). Queries (facts and claims) and the gold law version were pulled out of the judgments by regex. "Two legal experts conducted cross-validation via random sampling". No IAA. — [arXiv html 2608.14610](https://arxiv.org/html/2608.14610)
- Each run evaluates a balanced 200-case test set (100 pre, 100 post). Two experts also wrote 16 either-or questions on the Civil Code's temporal-applicability rules. Finding: a "strong and systematic bias toward applying the most recently enacted law" **(search snippet)**. — [arXiv html 2608.14610](https://arxiv.org/html/2608.14610)

**LexKairos (Li et al., Tsinghua/Oxford; arXiv 2608.09106, Aug 2026)**
- 3,796 instances in total:
  - Statutory Temporal Knowledge: 1,417 — Effective Date Inquiry 485, **Effective Version Identification 452**, **Effective Status Verification 480**.
  - Case Temporal Modeling: 2,094 — 450 / 550 / 500 / 594.
  - Statute–Case Temporal Reasoning: 289 — Peremptory Period 180, Action Limitation 109. — [arXiv html 2608.09106](https://arxiv.org/html/2608.09106)
- Construction:
  - Task 1 is "rule-based … automatically synthesize[d]" from statutory metadata ("effective dates, promulgation dates, and all historical revisions"), followed by "a manual check alongside the removal of duplicates".
  - Task 2 uses DeepSeek-V3.2 event extraction plus SQL over the extracted events.
  - Task 3 is "submitted to legal experts for meticulous manual review".
  - No IAA. Metrics: accuracy, or F1 for two tasks. — [arXiv html 2608.09106](https://arxiv.org/html/2608.09106)
- Stated limitation: the 180 and 109 item tasks are small because expert verification is "highly labor-intensive". — [arXiv html 2608.09106](https://arxiv.org/html/2608.09106)

**CALRK-Bench (Korean; arXiv 2603.26332, Mar 2026)**
- 479 four-option MCQs:
  - TCR (temporal context recognition) 100: constitutional invalidation 44, **statutory amendment 8**, precedent change 48.
  - ISR (information sufficiency) 279: sufficient 49, insufficient 123, partial 107.
  - JSA (judgment shift attribution) 100: 28 / 28 / 26 / 18. — [arXiv html 2603.26332](https://arxiv.org/html/2603.26332)
- Process: seed cases picked by hand; GPT-5 filtered them and judged temporal applicability; researchers reviewed all LLM output; one law professor reviewed the task definitions. No IAA. Metric: accuracy. — [arXiv html 2603.26332](https://arxiv.org/html/2603.26332)

**LawShift (Han et al., NeurIPS 2025 D&B)**
- Legal judgment prediction under statute revisions, with "31 fine-grained change types". Articles are split into six components (subject, action, object, objective condition, subjective condition, sentence). Changes vary along three dimensions: scope, condition and sentence. The evaluation uses metamorphic relations rather than gold labels **(search snippet)**. — [NeurIPS 2025 D&B](https://papers.nips.cc/paper_files/paper/2025/hash/adf82a0a1d52d93961476458b9566a2b-Abstract-Datasets_and_Benchmarks_Track.html)

**LeKUBE (Wang et al., arXiv 2407.14192)**
- Updates are **synthetic**: annotators from law schools wrote "synthetic updates to the Chinese Criminal and Civil Code". There are 180 updated statutes plus 60 non-updated ones for locality testing. T/F questions: 642 on updated and 164 on non-updated statutes. MCQ: one per updated statute. — [arXiv html 2407.14192](https://arxiv.org/html/2407.14192)
- Quality: "Each data point is added … only after another annotator has checked and confirmed". Pay: 10 CNY per annotation pair at "4-5 annotations per hour", 3 CNY per evaluation. Five dimensions: accuracy, locality, generality, retainability, scalability. Corpus taken from STARD. — [arXiv html 2407.14192](https://arxiv.org/html/2407.14192)

**General legal benchmarks: construction and expert involvement**
- **LegalBench (NeurIPS 2023 D&B)**:
  - 162 tasks from 36 sources, written by legal academics and practitioners, either hand-crafted or reformatted.
  - Tasks per IRAC category: issue-spotting 16, rule-recall 5, rule-application 16, rule-conclusion 16, interpretation 119, rhetorical 10.
  - "All LegalBench tasks contain at least 50 samples, with an average task size of 563".
  - Tasks were "vetted for legal correctness"; rule-application answers are graded by "a law-trained individual" against an answer guide.
  - Metric: balanced accuracy. No IAA. Licence CC BY 4.0 overall, with per-task licences. — [arXiv html 2308.11462](https://arxiv.org/html/2308.11462)
- **LegalBench-RAG (2024)**: 6,858 query–answer pairs over more than 79M characters. Built by "retracing the context used in LegalBench queries back to their original locations". Claims to be "entirely human-annotated by legal experts" because it inherits CUAD, MAUD, ContractNLI and PrivacyQA spans. Has a mini version. CC BY 4.0. — [arXiv 2408.10343](https://arxiv.org/abs/2408.10343)
- **Bar Exam QA and Housing Statute QA (Zheng et al., CS&Law '25)**:
  - Bar Exam QA: 1,195 historical MBE questions plus 1,815 Barbri questions; corpus of about 900K passages. Law students annotated the gold passages by simulating legal research, which "took approximately 6 months". Authors "manually validated subsets". No IAA.
  - Housing Statute QA: 6,853 Y/N pairs over about 2M passages, adapted from the LSC Eviction Laws Database ("legally trained researchers and students"). **It pins statutes to "Justia's … statutes from the year 2021"**, or the latest available year. That is a frozen snapshot, not a versioned corpus.
  - Metric: Recall@10. — [arXiv html 2505.03970](https://arxiv.org/html/2505.03970v1)
- **CaseHOLD (ICAIL 2021)**: "over 53,000+" multiple-choice holding questions. Construction details not re-read this session. — [arXiv 2104.08671](https://arxiv.org/abs/2104.08671)
- **CLERC**: case-law citation retrieval plus generation. Zero-shot IR reaches 48.3% recall@1000. Sizes not read. — [arXiv 2406.17186](https://arxiv.org/abs/2406.17186)
- **COLIEE, BSARD, CUAD**: see `legal_qa_schemas.md` **(earlier notes)**. In brief: COLIEE pins the Civil Code "(updated in 2020)" in prose; BSARD used six jurists with no IAA and notes "outdated version of the Belgian law from May 2021"; CUAD had "each annotation … verified by three additional annotators".

### Inferences
- "Temporal legal QA" is no longer an open niche. Six or more benchmarks from 2025–2026 cover it. Two remain
  uncovered by any benchmark found:
  - **Sub-article partial repeal while the parent document stays in force** (ViLexTime T6). LexKairos "Effective Status Verification" is the nearest. Whether it works below statute level was not verified.
  - **Retroactive effect, where the effective date precedes signing** (ViLexTime T5). No benchmark found has a retroactivity category.
  T4 (near-identical versions) has a conceptual cousin in LawShift's minimal synthetic edits and in HoH's
  same-article-history distractors, but none uses *real* one-phrase amendments.
- Typical expert involvement in these legal-temporal sets is small: one professional (FiscalQA), two experts
  sampling (TALD), 2 students + 1 lawyer (German), one professor reviewing definitions (CALRK). Two annotators plus
  a legal advisor is therefore at or above the norm. Reporting κ would be **above** the norm, since none of the seven reports it.
- The German paper's κ split (outcome 0.860 vs legal basis 0.549) is a warning for ViLexTime's LLM judge. Checking
  "which version/basis was cited" is much harder to judge reliably than checking correctness. Validate the judge
  separately on the citation/version dimension (VCR), not only on overall correctness.
- FiscalQA Pro's "provenance" metric (did the system retrieve the date-applicable version?) is the same idea as
  ViLexTime's TV-Recall@1 and VCR. Cite it as the closest prior metric.
- Both the German set (buzer.de) and Housing Statute QA (Justia) rely on **unofficial** consolidations. vbpl.vn is the
  official national database, which is a defensible advantage. FiscalQA Pro (Légifrance API) is the official-source peer.

### Gaps
- LawShift's size, its real-vs-synthetic mix and its validation process: only the abstract and search snippets were seen.
- TALD's per-version counts and the experts' sample size for cross-validation: not reported in what was read.
- Whether LexKairos "Effective Status Verification" works at article/clause level or document level: not verified.
- LYNX legal KG, Akoma Ntoso-based or EUR-Lex consolidated-version QA datasets: **none found**. No benchmark found
  is built on EUR-Lex consolidated versions or AKN expressions. That is an observation of absence, not proof.
- LeCaRD/LeCaRDv2, CAIL2018, JEC-QA, STARD, LexGLUE, LEXam and COLIEE 2025 were not re-read. Do not quote sizes or IAA from memory.

---

## Q3. Vietnamese legal NLP datasets: who annotated, how, sizes, licences

### Takeaway
Vietnamese legal datasets fall into three tiers by annotation rigour:
1. **Lawyer-annotated with κ**: VLegal-Bench. 10,450 items, 3 senior plus 8 junior lawyers, κ = 0.89, blind batch cross-checking.
2. **Law-student double annotation with expert review**: VLQA. 3,129 items, 5 senior law students plus 1 expert; reports
   correction rates instead of κ.
3. **LLM-generated, then LLM-jury and/or human-checked**: VLSP 2025 LegalSLM (GPT-4.1 → 3-LLM jury → 2 annotators),
   ViBidLQA (Claude 3.5 Sonnet train / expert-written test), ViHERMES (LLM multihop → annotators for borderline items).

ALQAC and Zalo only state "verified by legal experts" or give nothing. No Vietnamese dataset evaluates point-in-time
validity. VLQA *removes* repealed articles. LegalSLM asks about "pháp luật hiện hành" (current law) without a date.
ViHERMES has amendment-tracing hops but no as_of.

### Cited Findings
- **VLQA (arXiv 2507.19995, 2025)**:
  - 3,129 questions over 59,636 articles from 2,162 documents in 27 domains.
  - Questions were drawn from about 430,000 lay questions on Vietnamese legal-advice sites.
  - Annotators: "five senior law students", plus "an experienced legal expert as a reviewer and supervisor". "Each question-answer pair is annotated independently by two annotators".
  - Expert review outcome: 74.18% exact match, 14.83% expert-modified articles, 3.8% modified answers, 7.19% both.
  - Split 7:1:2. Licence CC BY-NC-SA 4.0.
  - **Excludes "articles that were repealed by past laws"**.
  - Metrics: R@k, P@k, F2@k, MAP, MRR, NDCG; ROUGE and BERTScore for answers. — [arXiv html 2507.19995](https://arxiv.org/html/2507.19995v1)
- **VLegal-Bench / "VietLegal" (CMC; arXiv 2512.14554 v5, Apr 2026)**. Extends the earlier notes with construction details.
  - 10,450 samples across 22 tasks in 5 cognitive levels. Test sizes by level: 3,550 / 2,808 / 2,011 / 1,181 / 900. Per task: 161 (Conflict Detection) to 1,359 items.
  - Annotators:
    - 3 senior experts, each with "a valid Vietnamese lawyer's license with a minimum of five years of professional practice".
    - 8 juniors, either licensed lawyers or bar-passed graduates with 1–3 years of experience.
  - Process:
    - Two juniors "independently construct realistic legal scenarios", with the sample quota split between them.
    - Blind cross-verification every 100 samples; IAA computed before discussion: 92.39%, κ = 0.89.
    - 794 disputes: 683 settled by the juniors, 111 escalated to a senior. Residual hard tasks: 3.4 (31), 3.3 (27), 5.4 (22).
    - Two-day training on 50 pilot samples, with ≥85% agreement against pilot gold required.
    - Pay: 150,000 VND per hour.
  - Corpus: about 55,000 "currently effective" documents. Self-described as static. — [arXiv html 2512.14554v5](https://arxiv.org/html/2512.14554v5)
- **VLSP 2025 LegalSLM (Le et al., Ton Duc Thang Univ.)**:
  - 1,950 items: 800 MC, 850 NLI, 300 syllogism.
  - Seeds: QA pairs from the thuvienphapluat.vn forum, 2023–2025, chosen "to ensure the evaluation data remains current for 2025".
  - Generation: GPT-4.1 under rules — answers must cite an explicit clause/point, and "If no basis exists, the model must output 'insufficient basis'".
  - LLM jury: each item "independently reviewed by three LLMs (DeepSeek, Gemini, and GPT-4.1)", kept if ≥2 of 3 accept.
  - Human review: "each sample … reviewed by two trained annotators" for citation consistency and answer clarity. Disagreements needed "a written justification and was resolved through discussion". No κ.
  - Metrics: accuracy; an LLM judge for syllogism. Models limited to 1.7B–4B parameters.
  - Example question opens "Theo quy định pháp luật hiện hành…", i.e. implicitly anchored to the current date. — [ACL Anthology 2025.vlsp-1.21](https://aclanthology.org/2025.vlsp-1.21.pdf)
- **ViHERMES (Nguyen et al., URA/HCMUT; arXiv 2602.07361, Feb 2026)**:
  - Corpus: healthcare regulations crawled from the Ministry of Health portal.
  - Generation: an LLM writes multihop QA from tuples of contexts taken from different documents. "each hop corresponds to one legal dependency step, such as amendment tracing".
  - Checking: automatic structural validation, after which "ambiguous or borderline cases are further reviewed by annotators under expert supervision".
  - **Test split 1,560 = 312 per hop level × 5 levels (NoH 1–5)**. This is the same balanced 5 × ~300 design ViLexTime plans.
  - Metrics: token F1 plus LLM-as-judge. CC-BY 4.0. — [arXiv 2602.07361](https://arxiv.org/pdf/2602.07361)
- **ViBidLQA**: covers the Bidding Law 22/2023/QH15 and Decree 24/2024/NĐ-CP. Train 5,300, "automatically generated by Claude 3.5 Sonnet and validated by two legal experts". Test 1,000, "manually created by two Vietnamese legal experts". **(search snippet; secondary sources, primary paper not read)** — [HF ViBidLAQA_base](https://huggingface.co/ntphuc149/ViBidLAQA_base); [alphaneural preview](https://app.alphaneural.io/datasets/preview/ViBidLQA)
- **ALQAC 2021–2026**:
  - 2021: "The questions as well as the relevant articles are verified by legal experts". Task 1 metric is macro F2; Tasks 2–3 use accuracy; 5, 6 and 5 teams per task; data in Vietnamese and Thai. — [ar5iv 2204.10717](https://ar5iv.labs.arxiv.org/html/2204.10717)
  - 2023: three question types (true/false, multiple choice, free text); free-text answers judged by experts. — [ALQAC 2023](https://sites.google.com/view/ALQAC2023)
  - Lecturers and law students of Hanoi Open University were involved in validation and annotation **(search snippet; attribution to a specific ALQAC year unclear)**. — [search result: ALQAC 2023 site / arXiv 2604.16270](https://arxiv.org/pdf/2604.16270)
  - 2024: any LLM allowed; source code must be submitted. — [ALQAC 2024](https://sites.google.com/view/ALQAC-2024)
  - 2026: case-outcome prediction with evidence retrieval, 11–14 Nov 2026 (Kanazawa). No mention of temporal validity. — [ALQAC 2026](https://sites.google.com/view/alqac2026)
  - No year publishes question counts on its site.
- **Zalo AI 2021 Legal Text Retrieval**: "3,196 questions and 61,425 articles" **(search snippet; primary source not pinned)**. The MTEB repack (818 queries, 61.4K corpus, MIT) is in the earlier notes. — [GreenNode HF](https://huggingface.co/datasets/GreenNode/zalo-ai-legal-text-retrieval-vn)
- **BKAI VNLAWQC / VNSYNLAWQC**: a legal retrieval set plus an LLM-generated synthetic query set used for pre-training retrievers **(search snippet)**. — [arXiv 2412.00657](https://arxiv.org/html/2412.00657v1)
- **"From Benchmarking to Reasoning" (Le, arXiv 2604.16270)**: 60 complex legal articles; 480 model outputs error-annotated by five law students; "Cohen's Kappa … κ = 0.72"; 253 non-expert raters. — [arXiv 2604.16270](https://arxiv.org/pdf/2604.16270)

### Inferences
- **The bar for a Vietnamese legal benchmark in 2026 is VLegal-Bench's protocol**: independent double annotation,
  blind batch cross-checks, κ computed *before* discussion, an escalation count, a pilot calibration threshold, and
  annotator credentials. ViLexTime can copy most of it cheaply:
  - a 50-item pilot with a ≥85% agreement gate;
  - κ before reconciliation;
  - reporting of "disputes → resolved by pair → escalated to advisor";
  - annotator credentials stated.
- LegalSLM is the domestic precedent for an **LLM-jury stage before human review**. It reports the jury as a filter
  ("kept if ≥2/3 accept") and the humans as the final check. If ViLexTime's cross-check annotator A is an LLM jury,
  frame it the same way. Report κ(jury, human B) as a judge-validation statistic, not as human IAA.
- ViHERMES (312 per level × 5 levels) is a direct domestic precedent for 300 per group × 5 groups.
- VLQA *excluding* repealed articles, and LegalSLM's undated "hiện hành", show that Vietnamese datasets avoid
  validity over time rather than test it. That is ViLexTime's opening domestically.

### Gaps
- Per-year ALQAC question counts and annotator counts: not on the official sites. Participant papers would have them; none were read.
- The Zalo 2021 annotation process (who wrote and labelled the questions) was not found.
- ViBidLQA's primary paper and any agreement figure were not read.
- The licence status of Vietnamese legal texts (vbpl.vn terms) remains unresearched, as in the earlier notes.

---

## Q4. Across all benchmarks: items per category, LLM-generated-plus-verified vs human-written, and how expert involvement and agreement are reported

### Takeaway
- **Size per category.** Recent legal-temporal and Vietnamese benchmarks run from about **80 to 600 items per category**:
  German 84–115, FreshQA 125 test, CALRK 100–279 (one sub-cell has only 8), LexKairos 109–594, ViHERMES 312,
  LegalSLM 300–850, VLegal-Bench 161–1,359 per task, LegalBench at least 50 per task.
  300 per group is at the upper-middle of that range.
- **Who writes the questions.** Fully human-written is the minority in 2025–2026: VLegal-Bench, VLQA (real questions),
  FreshQA. The dominant pattern is **automatic gold from a structured source + template or LLM-written question +
  human or expert accept/reject**, with the acceptance rate and rejection reasons reported.
- **How expert involvement is reported.** Annotator credentials and counts are now standard. κ is reported by only a
  few: SituatedQA, VLegal-Bench, the German judge validation, the Vietnamese error-analysis paper 2604.16270
  (κ 0.72), and FreshQA's rater agreement.

### Cited Findings

#### Comparative table
Abbreviations: H = human-written; L = LLM-generated; T = template/rule; A = automatic from KB or diff.
"—" means not reported in what was read. Sources are the links in Q1–Q3 unless a different one is given.

| Dataset (source) | Venue/year | Size | Lang | Question source | How gold was built | Annotation & verification | IAA reported | Splits | Categories (counts) | Metrics | Known weaknesses |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TimeQA ([ar5iv](https://ar5iv.labs.arxiv.org/html/2108.06314)) | NeurIPS D&B 2021 | 41,172 QA (easy 20,326 / hard 20,846); 5,060 facts | en | T (2–5 templates/relation) + 2,160 human paraphrases | A: Wikidata qualifiers aligned to Wikipedia | AMT fix of 5,500 fact-object pairs; 41.6% segments revised; 85–90% spot-check acceptance | — | train/dev/test | easy/hard; 12% segments unanswerable | EM/F1 | no temporal metadata field; snapshot-bound **(earlier notes)** |
| SituatedQA ([ar5iv](https://ar5iv.labs.arxiv.org/html/2109.06157)) | EMNLP 2021 | temp 12,227 triples; geo 5,451 | en | H (NQ-Open) | H: crowd timelines with start/end transitions | 3-stage (identify, collect, validate) | Fleiss κ 0.56–0.62 | 6,009/3,423/2,795 (temp) | Start/Sampled/Static; stable/updated | EM | ≤2021 Wikipedia snapshot **(earlier notes)** |
| StreamingQA ([ar5iv](https://ar5iv.labs.arxiv.org/html/2205.11388)) | ICML 2022 | eval ~36.4K (28K L-gen + 8.8K H); train 100K | en | H + L | H answers; L questions filtered | 3-annotator agreement filter + answerability check; 3 refs/question | — (agreement used as filter) | train/valid/eval | recent/past; written/generated | EM/F1 | extractive focus **(earlier notes)** |
| RealTimeQA ([ar5iv](https://ar5iv.labs.arxiv.org/html/2207.13332)) | NeurIPS D&B 2023 | 1,470 live + 2,886 earlier (6/2023); ~30/week | en | H (news quizzes) | H (publisher answers) | scraped | — | weekly | MC, MC+NOTA, generation | acc, EM/F1 | ~12% not time-dependent |
| ArchivalQA ([ar5iv](https://ar5iv.labs.arxiv.org/html/2109.03438)) | SIGIR 2022 | 532,444 | en | L (T5 QG) | A + classifier filters | 10 grad students rated 5K | — | 425,956/53,244/53,244 | Easy/Hard, Time/NoTime | EM/F1 | generated questions |
| TemporalWiki ([ar5iv](https://ar5iv.labs.arxiv.org/html/2204.14211)) | EMNLP 2022 | 4 × ~8.6–9.3K probes | en | T | A: Wikidata snapshot diffs | heuristics only | — | per month | Changed/Unchanged | perplexity | diffs ≠ real world changes; no deletions |
| TempReason ([ar5iv](https://ar5iv.labs.arxiv.org/html/2306.08952)) | ACL 2023 | L1 408K, L2 26,935, L3 21,877 | en | T | A: Wikidata 2022-11-20 | none described | — | train/dev/test | L1/L2/L3 | EM/F1 | no metadata **(earlier notes)** |
| MenatQA ([ar5iv](https://ar5iv.labs.arxiv.org/html/2310.05157)) | EMNLP-F 2023 | 2,853 | en | H perturbations of TimeQA | H | trained students, 2-round validation | — | test only | scope 1,448 / order 857 / counterfactual 548; 14.2% unanswerable | EM/F1 | small **(earlier notes)** |
| FreshQA ([ar5iv](https://ar5iv.labs.arxiv.org/html/2310.03214)) | ACL-F 2024 | 600 | en | H (researchers + freelancers) | H + URL + year last changed | updated regularly | 99% / 96% (2 raters, 100 answers) | 500 test / 100 dev | 4 × 125 test (never/slow/fast/false-premise) | RELAXED / STRICT acc | needs maintenance |
| ChroKnowBench ([arXiv](https://arxiv.org/html/2410.09870)) | ICLR 2025 | ~65K incl. legal 6,284 | en | T | A: yearly object tracking (CFR for legal) | limited | — | — | dynamic/static × domain | Known/Partial/Cut-off/Unknown | exact-match gold |
| Test of Time ([HF](https://huggingface.co/datasets/baharef/ToT/blob/main/README.md)) | ICLR 2025 | 2,800 + 1,850 (+46,480 large) | en | T (synthetic) | A | — | — | test | 7 types | acc | synthetic |
| TRAM ([arXiv](https://arxiv.org/html/2310.00835v3)) | ACL-F 2024 | 526.7K MCQ **(snippet)** | en | mixed | mixed | — | — | — | 10 tasks | acc | — |
| VersionQA ([arXiv](https://arxiv.org/html/2510.08109v1)) | arXiv 2025 | 100 **(snippet)** | en | H | H | — | — | — | 6 types; 60% version-sensitive | — | tiny |
| German statutory ([arXiv](https://arxiv.org/html/2605.23497)) | ICAIL 2026 | 312 (of 697) | de | L (Gemini 3 Pro) | A: buzer.de versions | 2 senior law students + 1 lawyer accept/reject | none for validation; judge κ 0.751 | none | 115 / 113 / 84 | LLM judge (outcome, legal basis) | unofficial source; small |
| FiscalQA Pro ([arXiv](https://arxiv.org/html/2608.09393)) | arXiv 2026 | 221 (209 scored) | fr | A candidates + H text | A: Légifrance version histories | 1 tax professional reviewed all | — | single frozen set | R1–R4 (counts unclear) | strict acc + provenance | French tax only; small |
| TALD ([arXiv](https://arxiv.org/html/2608.14610)) | arXiv 2026 | 26,000 judgments; 200/run | zh | A (regex from judgments) | A: version cited by court | 2 experts random-sample cross-check | — | pre/post Code | balanced 100/100 | acc | Chinese civil only |
| LexKairos ([arXiv](https://arxiv.org/html/2608.09106)) | arXiv 2026 | 3,796 | zh | T + L-extraction | A + expert review | manual check; experts for Task 3 | — | — | 9 subtasks, 109–594 | acc/F1 | small Task 3 cells |
| CALRK-Bench ([arXiv](https://arxiv.org/html/2603.26332)) | arXiv 2026 | 479 | ko | H seeds + GPT-5 filter | H | researchers + 1 law professor | — | — | TCR 100 / ISR 279 / JSA 100 | acc | amendment cell n = 8 |
| LawShift ([NeurIPS](https://papers.nips.cc/paper_files/paper/2025/hash/adf82a0a1d52d93961476458b9566a2b-Abstract-Datasets_and_Benchmarks_Track.html)) | NeurIPS D&B 2025 | — | zh | synthetic edits **(snippet)** | metamorphic relations | — | — | — | 31 change types | MR violations | synthetic |
| LeKUBE ([arXiv](https://arxiv.org/html/2407.14192)) | arXiv 2024 | 180 + 60 statutes; 806 T/F + 180 MC | zh | H (law-school annotators) | H synthetic updates | 2nd-annotator confirmation | — | — | 5 dimensions | EM/acc | synthetic updates |
| LegalBench ([arXiv](https://arxiv.org/html/2308.11462)) | NeurIPS D&B 2023 | 162 tasks, avg 563 items (≥50) | en | H / adapted | H | vetted by contributors | — | small train + test | 16/5/16/16/119/10 | balanced acc | heterogeneous |
| LegalBench-RAG ([arXiv](https://arxiv.org/abs/2408.10343)) | arXiv 2024 | 6,858 | en | inherited | inherited spans | expert spans (inherited) | — | full + mini | 4 sources | P/R@k | — |
| Bar Exam QA / Housing Statute QA ([arXiv](https://arxiv.org/html/2505.03970v1)) | CS&Law 2025 | 1,195 + 1,815 / 6,853 | en | H (exams) / H (LSC DB) | H law students (~6 months) / H researchers | authors validated subsets | — | — | jurisdictions | Recall@10 | statutes frozen at 2021 |
| VLegal-Bench ([arXiv](https://arxiv.org/html/2512.14554v5)) | arXiv 2025–26 | 10,450 | vi | H (lawyers) | H | 2 juniors + blind cross-check + senior adjudication | 92.39%, κ 0.89 | test + dev | 5 levels / 22 tasks (161–1,359) | acc/F1/ROUGE | static |
| VLQA ([arXiv](https://arxiv.org/html/2507.19995v1)) | arXiv 2025 | 3,129 | vi | H (citizens) | H (5 law students, double) | expert reviewed; 74.18% unchanged | — (correction rates instead) | 7:1:2 | 27 domains | IR + ROUGE/BERTScore | repealed articles removed |
| VLSP 2025 LegalSLM ([ACL](https://aclanthology.org/2025.vlsp-1.21.pdf)) | VLSP 2025 | 1,950 | vi | L (GPT-4.1) from forum QA | L + rules | 3-LLM jury (≥2/3) → 2 annotators | — | — | MC 800 / NLI 850 / syllogism 300 | acc; LLM judge | undated "hiện hành" |
| ViHERMES ([arXiv](https://arxiv.org/pdf/2602.07361)) | arXiv 2026 | test 1,560 | vi | L | L + structural validation | annotators under expert, borderline only | — | train/test | 5 hop levels × 312 | F1 + LLM judge | no as_of |
| ViBidLQA (**snippet**) | 2024–25 | 5,300 train + 1,000 test | vi | L train / H test | — | 2 legal experts | — | train/test | — | — | — |
| ALQAC ([2021](https://ar5iv.labs.arxiv.org/html/2204.10717)) | KSE 2021–26 | — | vi | H | H | "verified by legal experts" | — | train/test | T/F, MC, free text | F2 / acc | no counts, no licence |
| Zalo 2021 LTR ([HF](https://huggingface.co/datasets/GreenNode/zalo-ai-legal-text-retrieval-vn)) | Zalo AI 2021 | 3,196 Q / 61,425 articles **(snippet)** | vi | — | — | — | — | — | — | retrieval | — |

### Inferences
- **Precision at 300 per category (computed, not cited).** The 95% CI half-width for an accuracy near 50% is about ±5.7 pp
  at n = 300, ±8.8 pp at n = 125 and ±9.8 pp at n = 100. With 300 per group, a T-group can show a difference of
  about 8–10 pp between two systems. Paired tests on the same items (McNemar, or the planned bootstrap by
  provision chain) are tighter than that.
  300 lineages per group does **not** equal 300 independent items if several as_of dates share one lineage. Report
  both counts, and bootstrap by lineage, as `problem_statement.md` RQ2 already plans.
- **Splits.** FreshQA reserves 100 of 600 items as dev. The German set and FiscalQA ship a single frozen test set.
  For a 1,500-lineage evaluation benchmark, a small dev set of about 10% plus a frozen test set matches common practice.
- **What the LLM-plus-human precedents report**, and ViLexTime should too:
  - generated vs accepted counts (German: 697 → 312);
  - a taxonomy of rejection reasons;
  - which model generated the items;
  - a per-item generated/written flag (StreamingQA).
  A human-written test set paired with LLM-generated training data (ViBidLQA) is a further option, but ViLexTime has no training split.
- **Labelling throughput (only weak anchors).** LeKUBE reports 4–5 *creations* per hour. Verifying an auto-built item
  should be faster, but 1,500 lineages × 2 annotators is 3,000 judgments. At 10–15 per hour that is about 200–300
  person-hours before adjudication. This is an estimate for planning, not a cited figure.

### Gaps
- No source found states a "minimum items per category" rule. The ranges above are observed practice, not a standard.
- No benchmark found reports κ for an LLM-generated-then-human-verified legal set. The German set explicitly does not.
  ViLexTime cannot cite a precedent for the size of κ to expect on accept/reject verification.

---

## Q5. Lessons for ViLexTime: category definitions, no-longer-valid answers, how to evaluate time-sensitivity, and where it is novel

### Takeaway
ViLexTime's design (auto-gold from version chains; questions as (x, as_of); groups T1–T6; 300 per group) lines up with the
2026 legal-temporal cluster. Its defensible novelty is **narrower** than "first temporal legal QA". It is:
1. the first **Vietnamese** point-in-time legal QA benchmark;
2. **provision-level (Khoản/Điểm) validity**, including partial repeal inside a document that stays in force (T6)
   and validity inherited from parent units;
3. a dedicated **retroactive-effect** category (T5), which no benchmark found has;
4. **near-identical real versions** (T4) as an explicit stressor;
5. official-source version chains (vbpl.vn) plus **κ-reported human verification**, which none of the seven
   legal-temporal peers report.

### Cited Findings
- **Category design precedents.**
  - The German set defines categories by *where the asked date falls relative to amendments and the model cutoff*:
    post-cutoff vs pre-amendment vs multi-provision. — [arXiv html 2605.23497](https://arxiv.org/html/2605.23497)
  - FreshQA defines categories by *how fast the answer changes*, plus false premise. — [ar5iv 2310.03214](https://ar5iv.labs.arxiv.org/html/2310.03214)
  - LexKairos defines them by *temporal capability* (date / version / status). — [arXiv html 2608.09106](https://arxiv.org/html/2608.09106)
  - CALRK defines them by *type of legal change* (constitutional invalidation / amendment / precedent change). — [arXiv html 2603.26332](https://arxiv.org/html/2603.26332)
  - TALD uses a balanced pre/post-reform design. — [arXiv html 2608.14610](https://arxiv.org/html/2608.14610)
- **Control groups.** SituatedQA's "Static" examples and TemporalWiki's "Unchanged" probes are explicit controls of the
  same kind as T1. — [ar5iv 2109.06157](https://ar5iv.labs.arxiv.org/html/2109.06157); [ar5iv 2204.14211](https://ar5iv.labs.arxiv.org/html/2204.14211)
- **"No longer valid" or unanswerable answers.**
  - TimeQA uses an "[unanswerable]" sentinel (12% of segments). — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)
  - MenatQA has 14.2% unanswerable items. — [ar5iv 2310.05157](https://ar5iv.labs.arxiv.org/html/2310.05157)
  - RealTimeQA has a NOTA setting. — [ar5iv 2207.13332](https://ar5iv.labs.arxiv.org/html/2207.13332)
  - FreshQA has a false-premise class (125 test items) where the answer must reject the premise. — [ar5iv 2310.03214](https://ar5iv.labs.arxiv.org/html/2310.03214)
  - LegalSLM forces "insufficient basis" during generation. — [ACL 2025.vlsp-1.21](https://aclanthology.org/2025.vlsp-1.21.pdf)
  - LexKairos has an Effective Status Verification task (480 items). — [arXiv html 2608.09106](https://arxiv.org/html/2608.09106)
  - CALRK has an "insufficient" condition (123 items). — [arXiv html 2603.26332](https://arxiv.org/html/2603.26332)
  - FiscalQA *excludes* ill-posed and indexed items rather than scoring them. — [arXiv html 2608.09393](https://arxiv.org/html/2608.09393)
- **Time-sensitivity evaluation designs.**
  - SituatedQA: same question at different dates; stable vs updated; about −15 points on updated answers. — [ar5iv 2109.06157](https://ar5iv.labs.arxiv.org/html/2109.06157)
  - StreamingQA: question date plus recent/past split. — [ar5iv 2205.11388](https://ar5iv.labs.arxiv.org/html/2205.11388)
  - FreshQA: RELAXED vs STRICT. — [ar5iv 2310.03214](https://ar5iv.labs.arxiv.org/html/2310.03214)
  - FiscalQA: strict accuracy separate from provenance. — [arXiv html 2608.09393](https://arxiv.org/html/2608.09393)
  - German set: outcome vs legal basis, judged separately. — [arXiv html 2605.23497](https://arxiv.org/html/2605.23497)
  - ChroKnow: Known / Partial / Cut-off / Unknown across years. — [arXiv html 2410.09870](https://arxiv.org/html/2410.09870)

### Inferences
- **Define each T-group by one manipulated variable**, as the German, CALRK and LexKairos categories do, and state
  the expected failure for each in one sentence:
  - T2: picks the wrong one of two versions.
  - T3: picks a stale middle version.
  - T4: confused by a lexically near-identical distractor (HoH's stated limitation shows this is a real stressor).
  - T5: anchors on the signing date instead of the effective date.
  - T6: answers with repealed text.
  - T1: control; nothing should fail.
- **Make T6 explicitly scorable.** Prior sets fold "no answer" into a sentinel string (TimeQA) or exclude it
  (FiscalQA). Score T6 two ways: (a) did the system say "no longer in force", and (b) did it avoid quoting the
  repealed text. That is a FreshQA STRICT-style check. Keep the reason code as in the earlier schema notes.
- **Keep the as_of in a field, not only in the question text**, and vary how it is phrased in the question. The German
  set's regex extraction of the as-of date shows that a date in the question alone forces systems to parse it. ViLexTime
  can report results both with the date given as metadata and with it embedded in the text.
- **Separate correctness from version provenance.** Report answer correctness plus a version-provenance metric
  (TV-Recall@1 / VCR), citing FiscalQA's provenance and the German legal-basis split. Validate the LLM judge on
  each dimension separately: the German set's legal-basis κ was only 0.549.
- **Human check of the auto-gold.** Report the share of TKG gold that annotators corrected, per group and per
  boundary/interior as_of (TimeQA's 41.6% is the reference point). Report κ before adjudication, the escalation count
  and the pilot gate (VLegal-Bench). This also addresses the circularity limitation in `problem_statement.md` §2.5(3),
  as FiscalQA and TALD do by having an expert review the automatic gold.
- **Novelty claims to avoid**: "first temporal legal QA benchmark" (German, FiscalQA, LexKairos, TALD, CALRK and
  LawShift precede it); "first legal amendment KG for Vietnam" (VLegal-Bench, ViHERMES); "largest" (LexKairos has
  3,796 items, TALD 26K judgments).
- **Novelty claims that hold, as far as this search found**:
  - first Vietnamese point-in-time legal QA;
  - provision-level partial-repeal (T6) and retroactivity (T5) categories;
  - real one-phrase-change version pairs (T4);
  - a balanced 300-per-group design with κ-reported human verification of KG-derived gold;
  - official-source version chains.

### Gaps
- Whether any benchmark tests **retroactive effect** was not searched exhaustively. Run one targeted search
  ("retroactive amendment benchmark LLM", "hồi tố") before claiming it.
- Whether LexKairos "Effective Status Verification" or CALRK's "statutory amendment" items reach **clause level** is unverified.
- Whether a 2026 Vietnamese temporal legal benchmark exists that this search missed: none found in arXiv or VLSP 2025.
  VLSP 2026 tasks were not checked.
