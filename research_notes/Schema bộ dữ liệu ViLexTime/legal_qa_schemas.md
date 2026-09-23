# Record-level schemas of legal QA / IR datasets, with emphasis on Vietnamese legal NLP and temporal validity of provisions

Scope note: everything below is field-level evidence gathered from primary sources
(competition data-format pages, dataset papers, HF cards, OASIS/IETF/EU specs).
Where a field could not be verified from a primary source it is listed under **Gaps**
rather than guessed. Throughout, "dataset does X" and "standard allows X" are kept apart.

---

## Q1. Vietnamese legal NLP datasets: exact schemas, and how they identify a provision

### Takeaway

Every published Vietnamese legal dataset identifies a provision with exactly two
strings — the Vietnamese document number (`law_id`, e.g. `"45/2019/QH14"`) and an
article number (`article_id`, e.g. `"1"`). There is no version field, no date, no
Khoản/Điểm sub-path, and no opaque provision id anywhere in ALQAC, VLSP-LTER or
the Zalo challenge data. Sub-article granularity (Điều/Khoản/Điểm) appears only in
the very recent VLegal-Bench paper, and even there the released benchmark is static.

### Cited findings

**ALQAC (Automated Legal Question Answering Competition) — Vietnamese track**

- ALQAC 2021 summary paper gives the corpus and sample formats verbatim. Legal
  Articles file: a list of documents, each `{"id": "45/2019/QH14", "articles": [{"id": "1", "text": "The content of legal article"}]}`.
  Annotation samples: `{"question_id": "q-1", "text": "The content of question or statement", "label": true, "relevant_articles": [{"law_id": "45/2019/QH14", "article_id": "1"}]}` — [A Summary of the ALQAC 2021 Competition, arXiv:2204.10717](https://arxiv.org/pdf/2204.10717)
- Task 1 (retrieval) query file: `[{"question_id": "q-1", "text": "The content of question or statement"}]`; run submission:
  `[{"question_id": "q-193", "relevant_articles": [{"law_id": "100/2015/QH13", "article_id": "177"}]}]` — [arXiv:2204.10717](https://arxiv.org/pdf/2204.10717)
- Task 2 / Task 3 (entailment, QA) submission: `[{"question_id": "q-193", "label": false}, ...]` — the system "should answer whether the statement is true or false via 'label' in JSON format" — [arXiv:2204.10717](https://arxiv.org/pdf/2204.10717)
- Provenance/annotation statement, verbatim: "Based on the legal text, we pose questions that can be answered using the relevant articles alone without the need for additional sources such as legal theory or supporting evidence. The questions as well as the relevant articles are verified by legal experts." — no annotator count, no agreement statistic — [arXiv:2204.10717](https://arxiv.org/pdf/2204.10717)
- ALQAC 2021 data was prepared in Vietnamese **and Thai**; all participants chose the Vietnamese set — [arXiv:2204.10717](https://arxiv.org/pdf/2204.10717)
- ALQAC 2025 keeps the same shape, with a `question_type` field added:
  Task 1 training record `{"question_id": "DS-101", "question_type": "Đúng/Sai", "text": "...", "relevant_articles": [{"law_id": "05/2022/QH15", "article_id": "15"}]}`;
  Task 1 submission `{"question_id": "TN-2", "relevant_articles": [{"law_id": "05/2022/QH15", "article_id": "95"}]}`;
  Task 2 record `{"question_id": "DS-101", "question_type": "Đúng/Sai", "answer": "Đúng"}`;
  Task 2 submission `{"question_id": "TL-3", "answer": "<the answer>"}` — [ALQAC 2025 site](https://sites.google.com/view/ALQAC-2025)
- ALQAC 2025 describes the data as "a manually annotated dataset based on well-known statute laws in the Vietnamese language" and points participants at public legal databases such as **vbpl.vn**; it bans closed models (ChatGPT/GPT-4/Claude/Gemini), caps open-weight models at 10B parameters, and forbids external legal QA/entailment datasets — [ALQAC 2025 site](https://sites.google.com/view/ALQAC-2025)
- Question-id prefixes are semantic, not opaque: `DS-` (Đúng/Sai = true/false), `TN-` (trắc nghiệm = multiple choice), `TL-` (tự luận = free text) — [ALQAC 2025 site](https://sites.google.com/view/ALQAC-2025)
- ALQAC official hub: [alqac.github.io](https://alqac.github.io/); ALQAC 2024 page: [sites.google.com/view/ALQAC-2024](https://sites.google.com/view/ALQAC-2024); ALQAC 2021 lab page: [JAIST Nguyen Lab](https://www.jaist.ac.jp/is/labs/nguyen-lab/home/alqac-2021/)

**VLSP 2023 Legal Textual Entailment Recognition (LTER)**

- Training record, verbatim from the task page:
  `{"example_id": "DS-101", "label": "Yes/No", "statement": "<Vietnamese legal statement>", "legal_passages": [{"type": "law", "law_id": "05/2022/QH15", "article_id": "15"}]}`;
  prediction: `{"example_id": "DS-101", "label": "Yes/No"}` — [VLSP 2023 LTER](https://vlsp.org.vn/vlsp2023/eval/lter)
- Note the extra `"type": "law"` discriminator on the passage — the only place in the
  Vietnamese corpus of schemas where the *kind* of legal instrument is typed. The page
  references vbpl.vn as an example public law library but does not state the corpus
  source or the version of the laws used — [VLSP 2023 LTER](https://vlsp.org.vn/vlsp2023/eval/lter)

**VLSP 2025 MLQA-TSR (Multimodal Legal QA on Traffic Sign Regulation)**

- Two source documents, cited by their Vietnamese identifiers, including a dated
  technical regulation: `QCVN 41:2024/BGTVT` ("Quy chuẩn kỹ thuật Quốc gia về báo hiệu đường bộ" / National Technical Regulation on Traffic Signs and Signals) plus the Road Traffic and Safety Law — [VLSP 2025 MLQA-TSR overview, ACL Anthology 2025.vlsp-1.48](https://aclanthology.org/2025.vlsp-1.48.pdf)
- Relevant-article citation in the sample figure is a natural-language composite
  string, not a structured id: "Điều 22 và B.7a trong Quy chuẩn kỹ thuật Quốc gia về báo hiệu đường bộ QCVN41:2024/BGTVT" — [2025.vlsp-1.48](https://aclanthology.org/2025.vlsp-1.48.pdf)
- The law database "is provided to the participants as a JSON file format along with a directory containing corresponding images"; images inside articles are inlined as `«IMAGE: image_file.jpg /IMAGE»` and tables as `«TABLE: table_html_code /TABLE»` — [2025.vlsp-1.48](https://aclanthology.org/2025.vlsp-1.48.pdf)
- Answer label vocabulary is Vietnamese: `"Đúng"` = Yes, `"Sai"` = No; questions are multiple-choice (four choices, one marked correct) or yes/no — [2025.vlsp-1.48](https://aclanthology.org/2025.vlsp-1.48.pdf)
- Four-stage pipeline: Stage 1 Data Collection (Selenium crawl of traffic-sign images),
  Stage 2 Annotation, **Stage 3 Cross-checking** ("If the annotator disagrees with an annotated sample, the disagreement sample will be sent back to the group of annotators for re-annotating"), **Stage 4 Validation** — process described in prose; no per-record annotator field — [2025.vlsp-1.48](https://aclanthology.org/2025.vlsp-1.48.pdf)
- Other VLSP legal tracks: [VLSP 2025 LegalSLM](https://vlsp.org.vn/vlsp2025/eval/legalSLM), overview paper [2025.vlsp-1.21](https://aclanthology.org/2025.vlsp-1.21/); [VLSP 2025 MLQA-TSR arXiv:2510.20381](https://arxiv.org/abs/2510.20381)

**Zalo AI Challenge 2021 — Legal Text Retrieval**

- Training file `train_data_model.json` carries `question_id`, `question`,
  `relevant_articles`, `non_relevant_articles`; each article object is
  `{"law_id", "article_id", "title", "text"}`. Negatives were produced as the
  top-10 Elasticsearch/BM25 results — [ZaloAI2021_LTR repo README](https://github.com/hieudx149/ZaloAI2021_LTR/blob/main/README.md); [Kaggle mirror](https://www.kaggle.com/datasets/hariwh0/zaloai2021-legal-text-retrieval/discussion)
- The `title` field is the Vietnamese article heading — the Zalo schema is the only
  Vietnamese one that stores an article title alongside its text.
- MTEB repackaging splits it into `corpus` (61.4k rows, 60,701 unique docs, mean
  ~1,359 chars), `queries` (818 rows / 788 unique, mean ~84 chars) and `qrels`
  (793 rows, mean 1.01 relevant docs per query, max 2); task type "t2t"; license MIT;
  source https://challenge.zalo.ai/ — [GreenNode/zalo-ai-legal-text-retrieval-vn](https://huggingface.co/datasets/GreenNode/zalo-ai-legal-text-retrieval-vn)

**UIT-ViQuAD / ViNewsQA-style Vietnamese QA**

- UIT-ViQuAD: 23,074 human-generated QA pairs over 5,109 passages from 174 Vietnamese
  Wikipedia articles, stored in `.json`, span-extraction, SQuAD-compatible — [A Vietnamese Dataset for Evaluating Machine Reading Comprehension, COLING 2020](https://aclanthology.org/2020.coling-main.233.pdf)
- UIT-ViQuAD 2.0 is built on SQuAD 2.0 and adds over 12K unanswerable questions;
  the added fields are `is_impossible` and `plausible` (plausible answers) — [taidng/UIT-ViQuAD2.0](https://huggingface.co/datasets/taidng/UIT-ViQuAD2.0); used as the VLSP 2021 MRC task data — [VLSP 2021 MRC](https://vlsp.org.vn/vlsp2021/eval/mrc)
- Dataset family hub: [UIT NLP Group datasets](https://nlp.uit.edu.vn/datasets/); [kietnv/VietnameseDatasets](https://github.com/kietnv/VietnameseDatasets)

**VLegal-Bench / "Benchmarking Vietnamese Legal Knowledge of LLMs"**

- The only Vietnamese work that explicitly models the Điều/Khoản/Điểm hierarchy:
  provisions are identified as **Articles (Điều), Clauses (Khoản), Points (Điểm)**,
  and the authors build a Knowledge Graph Database encoding the "hierarchical
  structure of civil-law texts, including relationships among Articles, Clauses, and
  Points", tracking "amendments, replacements" and "temporal relations among legal
  documents" — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)
- Corpus: "approximately 55,000 centrally issued and currently effective documents
  processed via HTML parsing and OCR", from "official government portals and law firm
  Q&A repositories"; contamination checks referenced thuvienphapluat.vn and
  chinhphu.vn — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)
- Annotation metadata reported **in the paper, not per record**: initial
  inter-annotator agreement 92.39% (9,656/10,450 samples), Cohen's κ = 0.89, disputed
  7.61% "resolved through consensus or senior adjudication"; human-evaluation κ = 0.92
  — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)
- License CC BY-NC-ND 4.0; repo promised at github.com/CMC-OPENAI/VLegal-Bench — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)
- Self-declared limitation: "the benchmark itself is static" and "newly promulgated or
  revised statutes may render some benchmark items outdated over time" — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5); [v1 HTML](https://arxiv.org/html/2512.14554v1)

### Inferences

- `law_id` in Vietnamese datasets is the *số hiệu văn bản* (document number) of the
  form `NN/YYYY/CQBH` (`45/2019/QH14` = Bộ luật Lao động 2019, `100/2015/QH13` = Bộ luật
  Hình sự 2015, `05/2022/QH15`). It encodes the promulgating body and the year of
  promulgation, therefore it pins the **Work**, not the **Expression** — it can never
  distinguish the original text from the consolidated text after an amending law.
- Because `article_id` is a bare number string and there is no Khoản field, none of
  ALQAC / VLSP-LTER / Zalo can express the consumer's target unit "Điều X Khoản Y".
  A new benchmark adding `clause_id` / `point_id` is a genuine schema extension in
  this literature, not a re-implementation.
- ALQAC's corpus file uses `"id"` for both document and article, while its QA records
  use `"law_id"`/`"article_id"` for the same two things — a naming inconsistency worth
  not copying.

### Gaps

- No official ALQAC 2022/2023/2024 data-format page was retrieved verbatim in this
  session; the 2021 summary and the 2025 page bracket the format and agree, but an
  intermediate-year drift (e.g. when `question_type` was introduced) is unverified.
- No public dataset card or repo was found that distributes a vbpl.vn or
  thuvienphapluat.vn corpus with its own documented schema. The Vietnamese portals
  are cited as *sources* by ALQAC/VLSP/VLegal-Bench, never as a released, schema-ed
  dataset.
- ALQAC/VLSP/Zalo do not publish an explicit license or a retrieval-date field for the
  legal texts; no license statement was found on the ALQAC or VLSP-LTER pages.
- VLSP 2025 MLQA-TSR: the exact JSON keys of the released law database and QA files
  were not obtainable from the overview paper (it describes the files in prose only).
- ViNewsQA field-level schema was not verified separately from UIT-ViQuAD.

---

## Q2. Non-Vietnamese legal QA/IR datasets: record fields and citation of the statutory unit

### Takeaway

International datasets split into two camps: statute-law sets (COLIEE, BSARD, ALQAC)
that cite an article by a (code, article-number) pair, and case-law/contract sets
(CaseHOLD, CUAD) that carry no statutory path at all. None of the ones verified here
uses ELI, ECLI or an Akoma Ntoso eId as its record key.

### Cited findings

**COLIEE (Competition on Legal Information Extraction/Entailment)**

- Four tasks: case-law retrieval (Task 1), case-law entailment (Task 2), statute-law
  retrieval (Task 3), statute-law entailment/QA (Task 4) — [COLIEE 2022 Summary](https://sites.ualberta.ca/~miyoung2/Papers/COLIEE2022_summary.pdf)
- Task 3 definition: "extract a subset of Japanese Civil Code Articles S1, S2,...,Sn
  from the entire Civil Code articles considered appropriate for answering the legal
  bar exam question Q such that Entails(S1,...,Sn, Q) or Entails(S1,...,Sn, notQ)" — [COLIEE 2022 Summary](https://sites.ualberta.ca/~miyoung2/Papers/COLIEE2022_summary.pdf)
- **A version statement exists, in prose:** "since (updated in 2020), we use civil law
  articles that have official English translation (768 articles in total) as the target
  civil code" — i.e. COLIEE pins one snapshot of the Japanese Civil Code and says so in
  the overview paper, but carries no version field in the data — [COLIEE 2022 Summary](https://sites.ualberta.ca/~miyoung2/Papers/COLIEE2022_summary.pdf)
- COLIEE 2022 Task 3 had 109 questions classified by number of relevant articles
  (94 with 1, 11 with 2, 2 with 3, 1 with 4, 1 with 5) — [COLIEE 2022 Summary](https://sites.ualberta.ca/~miyoung2/Papers/COLIEE2022_summary.pdf)
- Larger reported Task-3 figures elsewhere: 996 questions, 768-article Civil Code
  corpus, 1,272 positive question–article pairs — [Legal Information Retrieval and Entailment Using Transformer-based Approaches, PMC11026203](https://pmc.ncbi.nlm.nih.gov/articles/PMC11026203/)
- Latest edition overview: [An Overview of the COLIEE 2025 Competition, ICAIL 2025](https://dl.acm.org/doi/10.1145/3769126.3785016)

**BSARD (Belgian Statutory Article Retrieval Dataset, French)**

- Articles corpus columns: `id`, `article` (full content), `code`, `article_no`,
  `description` ("Concatenated headings of the article"), `law_type`
  (`regional` | `national`) — [A Statutory Article Retrieval Dataset in French, arXiv:2108.11792](https://arxiv.org/html/2108.11792) / [ACL 2022](https://aclanthology.org/2022.acl-long.468/)
- Questions columns: `id`, `question`, `category` (Family, Housing, Money, Justice…),
  `subcategory`, `extra_description`, `article_ids` (list of relevant article ids) — [arXiv:2108.11792](https://arxiv.org/html/2108.11792)
- Files: `train.csv`, `test.csv`, `synthetic.csv`; 886 train / 222 test questions;
  22,633 articles from 32 Belgian codes — [arXiv:2108.11792](https://arxiv.org/html/2108.11792); [Kaggle mirror](https://www.kaggle.com/datasets/thedevastator/belgian-statutory-article-retrieval-dataset-bsar); [GitHub maastrichtlawtech/bsard](https://github.com/maastrichtlawtech/bsard)
- BSARD "is the only SAR dataset that provides the lists of consecutive division
  headings each article belongs to", which is what makes the legislative-structure
  graph buildable — [Finding the Law: Enhancing Statutory Article Retrieval via Graph Neural Networks, arXiv:2301.12847](https://arxiv.org/pdf/2301.12847)
- Annotators: "Six Belgian jurists from Droits Quotidiens (DQ)", each an expert in a
  specific field (family, housing, work); **no inter-annotator agreement metric is
  reported** — [arXiv:2108.11792](https://arxiv.org/html/2108.11792)

**CaseHOLD**

- Fields: `example_id` (int32), `citing_prompt` (string), `holding_0` … `holding_4`
  (five candidate holdings), `label` (5 classes, 0–4). 53.1k rows: 42.5k train /
  5.31k validation / 5.31k test; 11 subsets (`fold_1`…`fold_10`, `all`) — [casehold/casehold on HF](https://huggingface.co/datasets/casehold/casehold)
- No statutory path of any kind — the unit is a case holding.

**CUAD (Contract Understanding Atticus Dataset)**

- 500+ contracts, 41 clause types, 13,000+ expert annotations; distributed in SQuAD-style
  QA form as `theatticusproject/cuad-qa` — [CUAD paper, arXiv:2103.06268](https://arxiv.org/abs/2103.06268); [ar5iv HTML](https://ar5iv.labs.arxiv.org/html/2103.06268); [HF card](https://huggingface.co/datasets/theatticusproject/cuad-qa/blob/f4a87cf8573103dae9f2335ad3cc704725499de6/README.md)

**Pile of Law (provenance-bearing legal corpus)**

- Per-record fields: `text`, `created_timestamp` ("may be inaccurate"),
  `downloaded_timestamp` (when scraped), `url` (source url) — [pile-of-law/pile-of-law](https://huggingface.co/datasets/pile-of-law/pile-of-law)
- ~256GB, ~10M documents, 31–35 US/EU sources — [Pile of Law, arXiv:2207.00220](https://arxiv.org/pdf/2207.00220)

### Inferences

- The nearest structural analogue to a Vietnamese temporal benchmark is BSARD: it is
  the only verified statute dataset that stores the hierarchical path (`description` =
  concatenated division headings) next to the article text, and the only one whose
  paper states the corpus snapshot date explicitly (see Q3).
- COLIEE and ALQAC converge on the same minimal citation model (corpus id + article
  number) independently, so "law_id + article_id" is the de facto domain convention a
  new Vietnamese dataset should keep — and then extend, rather than replace.

### Gaps

- The literal COLIEE XML markup (`<pair id="H18-1-2" label="Y"><t1>…</t1><t2>…</t2></pair>`)
  could **not** be confirmed from a primary source in this session; the COLIEE 2022
  summary PDF describes the tasks but does not print the XML schema. Treat any
  tag-level claim about COLIEE as unverified until the official COLIEE data-format
  page or a downloaded data file is checked.
- LexGLUE, LegalBench, MAUD, GerDaLIR and LeCaRD were **not** verified at field level
  in this session. No field names for them should be asserted from these notes.
- No dataset was found that cites a provision by ELI, ECLI, Akoma Ntoso eId or urn:lex
  as its record key.

---

## Q3. Does any legal dataset model the point-in-time version of a provision?

### Takeaway

Essentially none. Among all datasets verified here, **zero** carry a per-record
validity interval, an "as amended by" pointer, or a consolidated-vs-original flag.
The handful of temporally aware artefacts either (a) state a single corpus snapshot
date in prose (COLIEE, BSARD), or (b) keep version information in an *auxiliary*
knowledge graph while the released benchmark records stay static (VLegal-Bench), or
(c) are 2026 diagnostic benchmarks that probe the problem without publishing a
documented per-record temporal schema (the German statutory-QA work). This is a
strong, defensible novelty claim.

### Cited findings

- **BSARD** is explicit that it is a frozen snapshot and warns readers: legal texts were
  "collected in May 2021" from ejustice.just.fgov.be, and "both the questions and
  articles correspond to an outdated version of the Belgian law from May 2021". The
  warning lives in the paper; **there is no date column in `articles.csv`** — [arXiv:2108.11792](https://arxiv.org/html/2108.11792)
- **COLIEE** pins the Japanese Civil Code "(updated in 2020)" to the 768 officially
  translated articles, again in prose, with no per-article version field — [COLIEE 2022 Summary](https://sites.ualberta.ca/~miyoung2/Papers/COLIEE2022_summary.pdf)
- **VLegal-Bench** builds a Knowledge Graph Database tracking "amendments,
  replacements" and "temporal relations among legal documents", yet concedes "the
  benchmark itself is static" and that revisions "may render some benchmark items
  outdated over time" — the temporal structure is in the KG, not in the benchmark
  record — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)
- **"Asking For An Old Friend: Diagnosing and Mitigating Temporal Failure Modes in
  LLM-based Statutory Question Answering"** — 312 expert-validated, time-sensitive
  German statutory QA pairs, in three categories: **Post-Cutoff Amendment Questions**,
  **Pre-Amendment Questions**, **Multi-Provision Pre-Amendment Questions**. Mitigation
  uses "fact date extraction and version filtering" in RAG variants; evaluation uses
  "an LLM-as-a-judge validated against human expert ratings" — [arXiv:2605.23497](https://arxiv.org/abs/2605.23497)
- **Pile of Law** is the only corpus verified here with a machine-readable time field
  per record — but `created_timestamp` / `downloaded_timestamp` are *scrape* metadata,
  not legal validity — [pile-of-law/pile-of-law](https://huggingface.co/datasets/pile-of-law/pile-of-law)
- **LEXAM** (4,886 law-exam questions, 2016–2023) is reported to have observed "some
  answers may have become outdated" and to have proposed metadata-based updates
  (reported via search synthesis; primary source not fetched — see Gaps).

### Inferences

- The field-level novelty to claim for a Vietnamese temporal benchmark is narrow and
  precise: *a per-record validity interval plus an amendment-provenance pointer on the
  cited provision*. Not "temporal legal QA" in general — that now has at least one 2026
  German precedent — but the released **schema** that makes each answer checkable
  against a dated expression.
- Because COLIEE and BSARD both handle time by freezing and footnoting it, a dataset
  whose records carry `valid_from` / `valid_to` is doing something the domain has only
  ever documented in prose.

### Gaps

- The exact JSON keys of the German temporal benchmark (arXiv:2605.23497) are not in
  the abstract; the full-text HTML was not fetched. Do not assert its field names.
- LEXAM and CALRK-Bench (Korean, [arXiv:2603.26332](https://arxiv.org/html/2603.26332))
  were surfaced only through search synthesis; their schemas are unverified.
- Statutory databases that *do* serve point-in-time text (legislation.gov.uk, Lexis/
  Westlaw, vbpl.vn itself) were not surveyed here as *datasets* — the claim above is
  about ML benchmark datasets, and should be stated that way.

---

## Q4. Identifier standards for citing a provision at a point in time

### Takeaway

Three standards can name "Điều 5 Khoản 2 of document X as it stood on 2020-01-01"
canonically: **Akoma Ntoso Naming Convention** (best fit — expression date + fragment
path in one IRI), **urn:lex / RFC 9676** (equally expressive, URN form), and **ELI**
(ontology-level: `eli:version_date` on a `LegalExpression`, with in-force intervals).
Note these are what the *standards allow*; no dataset surveyed in Q1–Q2 uses them.

### Cited findings — Akoma Ntoso (OASIS LegalDocML)

- Work IRI: `/akn/{country}/{doctype}[/{subtype}][/{author}]/{date}/{number}`, e.g.
  `[http://www.authority.org]/akn/sl/act/2004-02-13/2` — [Akoma Ntoso Naming Convention v1.0, §4.5](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html)
- Expression IRI adds language and an `@`-separated version date:
  - `/akn/sl/act/2004-02-13/2/eng` — "English version, current version (as accessed today)"
  - `/akn/sl/act/2004-02-13/2/eng@` — "English version, original version"
  - `/akn/sl/act/2004-02-13/2/eng@2004-07-21` — "English version, as amended on July 2004"
  - `/akn/uy/bill/ejecutivo/carpeta/2005-04-04/137-2005/esp@2005-05-02T13:30:00-03:00` — timestamped to the minute
  - `/akn/ng/bill/2003-05-14/19/eng@first` — named version
  — [AKN-NC v1.0 §4.6](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html)
- **Virtual expressions** — the exact construct for "as it stood on date D" when the
  amendment date is not known, using `:` instead of `@`:
  - `/akn/sl/act/2004-02-13/2/eng:2007-01-01` — "English version, as amended on the closest date before January 1st, 2007"
  - `/akn/eu/act/2004-11-13/87/und:2015-01-10` — all language versions, closest date before 2015-01-10
  - `/akn/ch/act/2009-05-09/432/deu:` — dynamic reference to any German version
  - `/akn/it/act/2005-03-07/82/eng:2010-01-01->2015-12-31` — "any of the Italian versions valid within the interval January 1st 2010 to December 31st 2015"
  — [AKN-NC v1.0 §4.6.2](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html)
- Fragment (provision) path appended with `~`, using the eId naming convention:
  - `/akn/eu/act/2003-11-13/87/eng@2015-01-20/!main~art_3` — "article 3 of the Expression … at the version dated 2015-01-20"
  - `/akn/eu/act/2003-11-13/87/eng@2015-01-20/~art_3->art_5` — article range (`!main` may be omitted)
  - `/akn/uy/act/2008-08-11/18331/esp@2009-12-12;2010-01-01~art_3__para_5__point_c` — "Act of Uruguay n. 18331 in the version of 2009, Dec 12, with a retroactive modification happened in 2010"
  — [AKN-NC v1.0 §4.6, §4.8](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html)
  **This last example is the direct template for "Điều 5 Khoản 2 as of D": `art_5__para_2`.**
- Retroactivity is expressible with two dates separated by `;` (version date `;` event date).
- Manifestation adds format/publisher: `/akn/sl/act/2004-02-13/2/eng@2004-07-21/CIRSFID/2011-07-15.akn` — [AKN-NC v1.0 §4.7](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html)
- `eId` vs `wId`: "The @eId of a provision may change multiple times throughout the life
  of the document – it is non-persistent"; "@wId is the optional work identifier that
  uses the same syntactic convention as the @eId value … used to mark the identifier
  that the structure used to have in the original version, and is only needed when a
  renumbering occurred" — [Akoma Ntoso v1.0 Part 2: Specifications](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/os/part2-specs/os-part2-specs-3.html)
- Conformance level 2 requires "The values of the eId and wId attributes follows the
  Akoma Ntoso naming convention as formulated in chapters 4 and 5 of this document" — [AKN-NC v1.0 §3](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html)
- eId/wId syntax is defined in §5.4 (Prefix, element_ref, Number), with usage rules in
  §5.5 covering "The Master Expression", "Multi-Lingual Document", "Multi-Version
  Document" and amendment cases — [AKN-NC v1.0 ToC §5](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html)
- FRBR metadata containers `<FRBRWork>`, `<FRBRExpression>`, `<FRBRManifestation>` hold
  the corresponding identifying properties; `<FRBRformat>` in `<FRBRManifestation>` MUST
  match the format suffix of the manifestation IRI — [AKN-NC v1.0 §4.7](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html); [AKN Part 2](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/os/part2-specs/os-part2-specs-3.html)
- Schema: [akomantoso30.xsd](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/os/part2-specs/schemas/akomantoso30.xsd); EU profile: [AKN4EU 3.0 Volume II](https://op.europa.eu/documents/3938058/7067425/AKN4EU+3.0+Documentation+-+Volume+II+-+XML+markup+-+Part+1+-+Part+2.pdf)

### Cited findings — urn:lex (RFC 9676, IETF, informational, May 2025)

- Top-level: `"urn:lex:" NSS`, `NSS = jurisdiction ":" local-name` — [RFC 9676 §2.1](https://www.rfc-editor.org/rfc/rfc9676.txt)
- `local-name = work ["@" expression] ["$" manifestation]` — [RFC 9676 §5.3](https://www.rfc-editor.org/rfc/rfc9676.txt)
- `work = authority ":" measure ":" details *(":" annex)`;
  `details = (dates / period) ";" numbers` — [RFC 9676 §8 ABNF](https://www.rfc-editor.org/rfc/rfc9676.txt)
- `expression = version [":" language]`;
  `version = (amendment-date / specification) *(";" (event-date / event))`;
  `amendment-date = date`; `date = date-iso ["|" date-loc]`, `date-iso = year "-" month "-" day` — [RFC 9676 §8](https://www.rfc-editor.org/rfc/rfc9676.txt)
- Reserved characters: `@` = "Separator of the expression that contains information on
  version and language"; `$` = manifestation; `:` = main-element separator; `;` = level
  or specification separator; `+` = repetition; `|` = alternative formats of an element — [RFC 9676 §3.2](https://www.rfc-editor.org/rfc/rfc9676.txt)
- Version semantics: `amendment-date` "Contains the issuing date of the last considered
  amendment"; the original text uses the string "original" expressed in the language of
  the act (e.g. `originel` in French, `original` in German) — [RFC 9676 §5.6](https://www.rfc-editor.org/rfc/rfc9676.txt)
- Expression examples, verbatim:
  `urn:lex:ch:etat:loi:2006-05-14;22@originel:fr`,
  `urn:lex:ch:staat:gesetz:2006-05-14;22@original:de`,
  `urn:lex:ch:etat:loi:2006-05-14;22@2008-03-12:fr` (amended version in French),
  `urn:lex:be:conseil.etat:decision:2008-07-09;185.273@originel:fr` — [RFC 9676 §5.6](https://www.rfc-editor.org/rfc/rfc9676.txt)
- **Partition (provision) reference:** `URN-reference = URN-document ["~" partition-id]`.
  Verbatim: "referring to paragraph 3 of article 15 of the French Act of 15 May 2004,
  n. 106, the reference can be `urn:lex:fr:etat:loi:2004-05-15;106~art15;par3`" — [RFC 9676 §5.9 / references](https://www.rfc-editor.org/rfc/rfc9676.txt)
  **This is the direct urn:lex template for "Điều 15 Khoản 3".**
- Work examples: `urn:lex:it:stato:legge:2003-09-21;456`, `urn:lex:eu:commission:directive:2010-03-09;2010-19-EU`,
  `urn:lex:us:supreme.court:decision:1978-04-28;77-5953` — [RFC 9676 §2.1](https://www.rfc-editor.org/rfc/rfc9676.txt)
- Manifestation examples: `urn:lex:it:stato:legge:2000-04-03;56$parlamento.it:application-pdf;1.7` — [RFC 9676 §5.7](https://www.rfc-editor.org/rfc/rfc9676.txt)
- Status: registered in the IANA "Formal URN Namespaces" registry in 2022; finalized as
  informational RFC 9676 in May 2025 — [IETF datatracker draft-spinosa-urn-lex](https://datatracker.ietf.org/doc/draft-spinosa-urn-lex/); [Wikipedia: Lex (URN)](https://en.wikipedia.org/wiki/Lex_(URN))

### Cited findings — ELI (European Legislation Identifier)

Ontology namespace `http://data.europa.eu/eli/ontology#`. Verified property and class
names, extracted directly from the published `eli.owl`
([SEMICeu/e-legislation-pilot/ELI_Model/eli.owl](https://github.com/SEMICeu/e-legislation-pilot/blob/master/ELI_Model/eli.owl);
canonical copies: [op.europa.eu eli.owl](https://op.europa.eu/documents/3938058/11669184/eli.owl/), [data.europa.eu/eli/ontology](https://data.europa.eu/eli/ontology)):

- FRBR-style classes: `eli:LegalResource` (Work), `eli:LegalExpression` (Expression),
  `eli:Format` (Manifestation), linked by `eli:is_realized_by` (domain `LegalResource`,
  range `LegalExpression`), `eli:realizes`, `eli:is_embodied_by`, `eli:embodies`,
  `eli:is_exemplified_by`
- **Temporal properties:** `eli:version`, `eli:version_date`,
  `eli:first_date_entry_in_force`, `eli:date_no_longer_in_force`,
  `eli:date_publication` (domain `LegalResource`, range `xsd:date`), `eli:date_document`
- **In-force status:** class `eli:InForce` with a code list `eli:InForceTable` and
  individuals `eli:InForce-inForce`, `eli:InForce-notInForce`,
  `eli:InForce-partiallyInForce`; linked by property `eli:in_force`
- **Amendment/consolidation relations:** `eli:changes` / `eli:changed_by`,
  `eli:consolidates` / `eli:consolidated_by`, `eli:based_on` / `eli:basis_for`,
  `eli:implements` / `eli:implemented_by`, `eli:transposes` / `eli:transposed_by`,
  `eli:cites` / `eli:cited_by`, `eli:related_to`
- **Structure:** `eli:has_part` / `eli:is_part_of` (this is how ELI reaches a single
  article or paragraph — each part is itself a `LegalResource` with its own ELI URI)
- **Legal value / authenticity:** class `eli:LegalValue` with individuals
  `eli:LegalValue-authoritative`, `-definitive`, `-official`, `-unofficial`
- **Licensing/provenance:** `eli:licence` (domain `eli:Format`), `eli:rights`
  (domain `eli:Format`), `eli:rightsholder`, `eli:publisher`, `eli:published_in`,
  `eli:id_local`, `eli:uri_schema`, `eli:language`, `eli:format`, `eli:responsibility_of`
- ELI Pillar I = HTTP URI templates for identification; Pillar II = the metadata
  ontology; consolidated versions may be modelled either as a separate legal resource
  linked with `consolidates`, or as a different `LegalExpression` of the same resource
  — [ELI overview, EU Vocabularies](https://op.europa.eu/en/web/eu-vocabularies/eli); [ELI Technical Implementation Guide](https://op.europa.eu/documents/2050822/2138819/ELI+-+A+Technical+Implementation+Guide.pdf/); [EUR-Lex ELI register](https://eur-lex.europa.eu/eli-register/about.html)
- Schema.org has an aligned property `legislationDateOfApplicability` — [schema.org](https://schema.org/legislationDateOfApplicability)

### Inferences

- **Best fit for the consumer's dataset:** Akoma Ntoso naming convention, because a
  single string carries jurisdiction + document + language + point-in-time + provision
  path. A Vietnamese analogue of the Uruguay example would read
  `/akn/vn/act/2015-11-24/91/vie@2020-01-01/!main~art_5__para_2`
  (Work = Bộ luật Dân sự 91/2015/QH13; note this is a *constructed* illustration of the
  template, not a citation from the spec).
- For "as it stood on D" where D is a query date rather than a known amendment date,
  the **virtual expression** form with `:` (`…/vie:2020-01-01`) is the semantically
  correct one — it resolves to "the closest amendment date before D", which is exactly
  the semantics of a temporal knowledge-graph lookup.
- urn:lex `~art5;par2` maps 1:1 onto Điều/Khoản; ELI is the weakest of the three for
  provision-level point-in-time because it reaches sub-document units only via
  `has_part` chains of separately-minted URIs.

### Gaps

- **ECLI** (European Case Law Identifier) was not verified from a primary source in this
  session. It identifies *case law*, not statutory provisions, so it is out of scope for
  "Điều X Khoản Y", but do not assert its syntax from these notes.
- **LegalRuleML** was not examined; its temporal model (it does have one, for norm
  effectiveness intervals) is unverified here.
- The literal ELI URI template string (the `{jurisdiction}/{agent}/{year}/{natural_identifier}/{version}/{version_date}/…`
  form) could not be fetched — irishstatutebook.ie returned HTTP 403. The *ontology*
  property names above are verified; the *URI template* components are not.

---

## Q5. In-record annotation metadata: annotator ids, agreement, adjudication

### Takeaway

Not one of the datasets verified here ships per-item annotator metadata. Annotation
process is universally reported as prose in the paper (and often only as "verified by
legal experts"), with aggregate agreement statistics at best. There is no `verified_by`,
`review_status`, `annotator_id`, `n_annotators` or `kappa` field in any schema examined.

### Cited findings

- **ALQAC:** "The questions as well as the relevant articles are verified by legal
  experts." No count, no agreement figure, no per-record field — [arXiv:2204.10717](https://arxiv.org/pdf/2204.10717)
- **BSARD:** six named-organisation jurists (Droits Quotidiens), each a domain expert;
  no inter-annotator agreement reported; no annotator column in `train.csv`/`test.csv`
  (columns are `id, question, category, subcategory, extra_description, article_ids`) — [arXiv:2108.11792](https://arxiv.org/html/2108.11792)
- **VLegal-Bench:** the richest aggregate reporting found — initial IAA 92.39%
  (9,656/10,450), Cohen's κ = 0.89, 7.61% disputed "resolved through consensus or senior
  adjudication", human-eval κ = 0.92 — all **in the paper**, none in the record schema — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)
- **VLSP 2025 MLQA-TSR:** an explicit four-stage protocol with a cross-check stage
  ("If the annotator disagrees with an annotated sample, the disagreement sample will be
  sent back to the group of annotators for re-annotating") and a validation stage whose
  criteria are "the consistency between the question and the traffic signs, the
  correctness of the relevant articles and the answers, and the typos and syntax" —
  again process-only, no per-record status field — [2025.vlsp-1.48](https://aclanthology.org/2025.vlsp-1.48.pdf)
- **CUAD:** the most heavily documented annotation process in legal NLP — "a year-long
  effort by dozens of law student annotators, lawyers, and machine learning
  researchers"; annotators "attended 70-100 hours of contract review sessions lead by
  experienced lawyers" and followed "more than 100 pages of detailed annotation
  guidelines"; **"Each annotation was verified by three additional annotators"** — a
  3-way verification policy stated in the paper, not encoded per span — [CUAD, arXiv:2103.06268](https://arxiv.org/abs/2103.06268)
- **German temporal statutory QA benchmark:** items are "expert-validated" (312 pairs)
  and evaluation uses "an LLM-as-a-judge validated against human expert ratings" — [arXiv:2605.23497](https://arxiv.org/abs/2605.23497)

### Inferences

- Adding per-record `verified_by` / `review_status` / `n_annotators` fields would put a
  Vietnamese temporal benchmark ahead of domain practice, not merely in line with it.
  Since the convention is aggregate-only, the safe design is: keep the aggregate
  statistics in the paper (κ, % disputed, adjudication rule — mirror VLegal-Bench's
  reporting, which is the Vietnamese-domain high-water mark) **and** add the per-item
  fields as a superset, so existing tooling that ignores them still parses the file.
- CUAD's "verified by three additional annotators" is the closest thing to an
  adjudication convention worth naming as precedent.

### Gaps

- LegalBench's per-task metadata (it is a collaboratively built benchmark, so it may
  carry contributor attribution per task) was not verified — do not assert either way.

---

## Q6. Licensing and provenance fields

### Takeaway

Provenance is carried in dataset cards and papers, rarely in records. The one verified
exception is Pile of Law, whose records carry `url` + `downloaded_timestamp`. Vietnamese
legal datasets publish essentially no licensing or provenance fields at all.

### Cited findings

- **Pile of Law** — per-record `url`, `created_timestamp`, `downloaded_timestamp`,
  `text`. License: "CreativeCommons Attribution-NonCommercial-ShareAlike 4.0
  International. But individual sources may have other licenses." Provenance policy:
  "We do not normalize the data, but we provide dataset creation code and relevant urls
  in https://github.com/Breakend/PileOfLaw". Distribution restriction: "Please do not
  re-host any data in a way that can be indexed by search engines." — [pile-of-law/pile-of-law](https://huggingface.co/datasets/pile-of-law/pile-of-law); [arXiv:2207.00220](https://arxiv.org/pdf/2207.00220)
- **BSARD** — data CC BY-NC-SA 4.0, code MIT; source stated as publicly available
  Belgian codes from ejustice.just.fgov.be, collected May 2021; `law_type` column
  records the regional/national jurisdiction level — [arXiv:2108.11792](https://arxiv.org/html/2108.11792)
- **Zalo AI legal retrieval (MTEB repack)** — license MIT, reference
  https://challenge.zalo.ai/, creator GreenNode, 150 MB / 63,036 rows — [GreenNode/zalo-ai-legal-text-retrieval-vn](https://huggingface.co/datasets/GreenNode/zalo-ai-legal-text-retrieval-vn)
- **VLegal-Bench** — CC BY-NC-ND 4.0 — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)
- **ELI** provides the ontology slots for all of this at Manifestation level:
  `eli:licence` and `eli:rights` (both domain `eli:Format`), `eli:rightsholder`,
  `eli:publisher`, `eli:published_in`, `eli:language`, `eli:format`, `eli:id_local`,
  plus the authenticity code list `eli:LegalValue-{authoritative,definitive,official,unofficial}`
  — the last is the standards-level way to say "this is an unofficial consolidated text"
  — [eli.owl](https://github.com/SEMICeu/e-legislation-pilot/blob/master/ELI_Model/eli.owl)
- Large multilingual legal corpora with documented provenance practice:
  [MultiLegalPile (689GB), ACL 2024](https://aclanthology.org/2024.acl-long.805.pdf) / [arXiv:2306.02069](https://arxiv.org/pdf/2306.02069);
  dataset registries: [neelguha/legal-ml-datasets](https://github.com/neelguha/legal-ml-datasets), [openlegaldata/awesome-legal-data](https://github.com/openlegaldata/awesome-legal-data)

### Inferences

- A minimal, convention-respecting provenance block for a vbpl.vn-derived dataset would
  be: `source_url`, `retrieved_at` (Pile of Law's pair), `jurisdiction: "VN"`,
  `language: "vi"`, plus an ELI-style `legal_value` flag distinguishing the official
  published text from a consolidated/derived one. Only the first two have direct dataset
  precedent; the last is standards precedent.

### Gaps

- No license statement of any kind was found on the ALQAC or VLSP-LTER pages, and none
  is printed in the ALQAC 2021 summary. Vietnamese competition data appears to be
  distributed without an explicit license — report this as observed absence, not as
  permissive licensing.
- Copyright status of Vietnamese legal texts themselves (vbpl.vn / thuvienphapluat.vn
  terms of use) was not researched.

---

## Q7. What the literature says about stale law, and whether anyone evaluates it

### Takeaway

Stale law has moved from a footnote-level limitation to a named research problem within
roughly the last year, but the evaluations are diagnostic probes, not released
schema-bearing benchmarks. The framing "legal QA is a temporally-indexed retrieval
problem" is the sharpest available statement of the hazard.

### Cited findings

- "Large language models are increasingly used for legal research, yet their fixed
  training cutoffs and reliance on static parametric knowledge are at odds with the
  evolving nature of statutory law." Two named failure modes: **post-cutoff staleness**
  ("models apply superseded rules after legislative amendments") and **recency bias**
  ("models prefer newer provisions even when a historical version governs the fact
  pattern"). Benchmark: 312 expert-validated, time-sensitive German statutory QA pairs
  across Post-Cutoff Amendment / Pre-Amendment / Multi-Provision Pre-Amendment
  categories; mitigation via fact-date extraction and version filtering in RAG — [arXiv:2605.23497](https://arxiv.org/abs/2605.23497)
- **Temporal misgrounding** is defined in this literature as "the systematic retrieval
  and citation of the currently in-force version of a legal article when the applicable
  version is an earlier or future one", with the accompanying claim that legal question
  answering is a temporally-indexed retrieval problem (surfaced via search synthesis of
  the temporal-QA literature; exact source paper not individually fetched — see Gaps).
- Vietnamese-specific statement of the hazard: "law is inherently dynamic with
  frequently amended, replaced, or repealed legislation, and newly promulgated or
  revised statutes may render benchmark items outdated over time, limiting the long-term
  validity of fixed benchmark instances" — [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)
- BSARD makes the same admission for Belgian law, three years earlier: questions and
  articles "correspond to an outdated version of the Belgian law from May 2021" — [arXiv:2108.11792](https://arxiv.org/html/2108.11792)
- Korean parallel: [CALRK-Bench: Evaluating Context-Aware Legal Reasoning in Korean Law](https://arxiv.org/html/2603.26332)
- Domain survey framing tasks/datasets/challenges: [NLP for the Legal Domain: A Survey, arXiv:2410.21306](https://arxiv.org/pdf/2410.21306)

### Inferences

- The strongest available novelty positioning for a Vietnamese temporal benchmark is
  therefore *not* "nobody has noticed stale law" — by 2026 several papers have — but
  "the hazard is acknowledged and then frozen into the data; no released dataset encodes
  the validity interval that would let the hazard be measured on the record itself."
  That claim is supported by BSARD, COLIEE and VLegal-Bench all documenting the problem
  in prose while shipping schemas with no temporal field.
- A `question_date` / `as_of_date` field plus per-provision `valid_from`/`valid_to` is
  precisely what would let the German paper's three question categories (post-cutoff,
  pre-amendment, multi-provision pre-amendment) be generated automatically from a
  temporal KG rather than hand-built — a reasonable design target.

### Gaps

- The "temporal misgrounding" definition came through search synthesis rather than a
  fetched primary source; locate and cite the originating paper before using the term
  as a quotation.
- No evaluation was found that measures whether a system *cites a repealed provision*
  as a distinct error class with its own metric — the German work measures answer
  correctness under temporal conditions, not citation staleness. Worth checking
  JURIX/ICAIL 2025–2026 proceedings directly, which were not searched in this session.

---

## Cross-cutting summary for the schema designer (inference, not a cited finding)

Field-by-field, the domain convention a Vietnamese temporal benchmark should match,
and where it must extend:

| Concern | Domain convention (sourced above) | Extension needed |
|---|---|---|
| Question id | `question_id` / `example_id`, semantic prefix (`DS-`, `TN-`, `TL-`) | — |
| Question text | `text` (ALQAC) / `question` (Zalo, BSARD) / `statement` (VLSP-LTER) | — |
| Document id | `law_id` = số hiệu văn bản, e.g. `91/2015/QH13` | — |
| Provision id | `article_id` (bare number) | add `clause_id` (Khoản), `point_id` (Điểm) |
| Evidence text | `text` inside article object; `title` (Zalo only) | — |
| Answer | `label` (bool) / `answer` (`"Đúng"`/`"Sai"`) | — |
| Doc type | `type: "law"` (VLSP-LTER only) | keep — Vietnam has Luật/Nghị định/Thông tư |
| Point in time | **absent everywhere** | `as_of_date` on the question; `valid_from`/`valid_to` on the cited provision |
| Amendment provenance | **absent everywhere** | `amended_by` (law_id of the amending document), `version_id` |
| Canonical identifier | **absent everywhere** | AKN-style `…/vie@{date}/~art_5__para_2` or urn:lex `…@{date}~art5;par2` |
| Annotation | prose only; CUAD's "verified by three additional annotators" is the precedent | per-record `verified_by`, `review_status` as a superset |
| Provenance | Pile of Law's `url` + `downloaded_timestamp` | `source_url` (vbpl.vn permalink), `retrieved_at`, `jurisdiction`, `language` |
