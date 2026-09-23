# Record-level schemas of temporal QA benchmarks

Scope note: "verified" below means I read the actual field names out of a shipped
data file, a HuggingFace dataset-server `features` block, or a repo README that
specifies the format. "Paper-only" means the schema is described in prose and I
could not confirm on-disk keys. Nothing here is invented; unconfirmed items are
in **Gaps**.

## Q1. Exact top-level fields of one record, per benchmark

### Takeaway

Three schema families exist. (1) The **slot-filling family** (TempLAMA,
TEMPREASON) puts a scalar `date` next to `query`/`question` and a list-valued
answer — one record per (query, date). (2) The **reading-comprehension family**
(TimeQA, StreamingQA, SituatedQA) carries `question` + `context`/`paragraphs` +
`targets`/`answers`, with time either in the question string or in explicit
timestamp integers. (3) The **taxonomy family** (ComplexTempQA, TempQA-WD, Test
of Time) adds a coded `type`/`CATEGORY` field and entity ids. The only datasets
that ship a machine-readable *query date* as its own column are TempLAMA
(`date`), TEMPREASON (`date`), StreamingQA (`question_ts`), and ComplexTempQA
(`timeframe`).

### Cited Findings

**TimeQA (Chen et al., NeurIPS 2021 Datasets & Benchmarks track; 2021).**
Verified features from the HF mirror `diwank/time-sensitive-qa`
([dataset-server first-rows](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train)):

```json
[{"name":"idx","type":{"dtype":"string"}},
 {"name":"question","type":{"dtype":"string"}},
 {"name":"context","type":{"dtype":"string"}},
 {"name":"targets","type":{"feature":{"dtype":"string"},"_type":"Sequence"}},
 {"name":"paragraphs","type":[{"text":{"dtype":"string"},"title":{"dtype":"string"}}]}]
```

Real record (context truncated by the fetch tool, keys intact):

```json
{"idx": "/wiki/Knox_Cunningham#P39#0",
 "question": "Which position did Knox Cunningham hold before Apr 1956?",
 "context": "Knox Cunningham Sir Samuel Knox Cunningham, 1st Baronet, QC (3 April 1909-29 July 1976), was a Northern Irish barrister, businessman and politician. ...",
 "targets": ["Ulster Unionist MP for South Antrim"],
 "paragraphs": [ {"title": "...", "text": "..."}, ... ]}
```

— [HF dataset-server, diwank/time-sensitive-qa](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train);
dataset page [wenhuchen/Time-Sensitive-QA](https://github.com/wenhuchen/Time-Sensitive-QA);
paper [arXiv 2108.06314](https://arxiv.org/pdf/2108.06314)

Note the composite `idx`: `"/wiki/<Page>#<WikidataPropertyID>#<n>"` — it packs
source page, relation, and an instance counter into one string rather than
separate provenance columns.

**TEMPREASON (Tan et al., ACL 2023; 2023).** Verified features of
`tonytan48/TempReason`
([dataset-server](https://datasets-server.huggingface.co/first-rows?dataset=tonytan48%2FTempReason&config=default&split=train)):

```json
[{"name":"question","type":{"dtype":"string"}},
 {"name":"date","type":{"dtype":"string"}},
 {"name":"text_answers","type":{"text":{"feature":{"dtype":"string"},"_type":"Sequence"}}},
 {"name":"id","type":{"dtype":"string"}},
 {"name":"context","type":{"dtype":"string"}}]
```

Real first row (L1 split):

```json
{"question": "What is the time 1 year and 7 month after Mar, 1873",
 "date": "March 26, 1873",
 "text_answers": {"text": ["Oct, 1874"]},
 "id": "0",
 "context": ""}
```

Files are named per level, e.g. `train_l2.json`. — [HF tonytan48/TempReason](https://huggingface.co/datasets/tonytan48/TempReason)

**TempLAMA (Dhingra et al., TACL 2022; data released 2021).** Verified features
of the `Yova/templama` mirror of the `google-research/templama` output
([dataset-server](https://datasets-server.huggingface.co/first-rows?dataset=Yova%2Ftemplama&config=default&split=train)):

```json
[{"name":"query","type":{"dtype":"string"}},
 {"name":"answer","type":[{"name":{"feature":{"dtype":"string"},"_type":"Sequence"},
                            "original_name":{"feature":{"dtype":"string"},"_type":"Sequence"},
                            "wikidata_id":{"dtype":"string"}}]},
 {"name":"date","type":{"dtype":"string"}},
 {"name":"id","type":{"dtype":"string"}},
 {"name":"most_frequent_answer","type":{"name":{"dtype":"string"},"wikidata_id":{"dtype":"string"}}},
 {"name":"most_recent_answer","type":{"name":{"dtype":"string"},"wikidata_id":{"dtype":"string"}}},
 {"name":"relation","type":{"dtype":"string"}}]
```

Real record:

```json
{"query": "Valentino Rossi plays for _X_.",
 "answer": [{"wikidata_id": "Q1085474",
             "name": ["Monster Energy Yamaha MotoGP*","Camel Yamaha Team","Movistar Yamaha MotoGP",
                      "Gauloises Fortuna Yamaha","Yamaha Motor Racing","Yamaha Factory Racing", "..."],
             "original_name": ["Yamaha Motor Racing"]}],
 "date": "2010",
 "id": "Q169814_P54_2010",
 "most_frequent_answer": {"wikidata_id": "Q1085474", "name": "Yamaha Motor Racing"},
 "most_recent_answer": {"wikidata_id": "Q1085474", "name": "Yamaha Motor Racing"},
 "relation": "P54"}
```

The `id` is `"<subject QID>_<property PID>_<year>"` — subject, relation and query
date are all recoverable from the key. — [HF Yova/templama](https://huggingface.co/datasets/Yova/templama);
paper [arXiv 2106.15110](https://arxiv.org/pdf/2106.15110)

**StreamingQA (Liška et al., ICML 2022; 2022).** JSONL fields documented in the
repo README, verified:
`qa_id` (str, `"eval-X"`/`"valid-X"`/`"train-X"` with X an int index from zero),
`question` (str), `answers` (List[str] — one answer for train/valid, three for
eval), `answers_additional` (List[str]), `question_ts` (int), `evidence_ts`
(int), `evidence_id` (str), `recent_or_past` (str), `written_or_generated`
(str), plus six Perspective-API toxicity floats: `toxicity_identity_attack`,
`toxicity_insult`, `toxicity_profanity`, `toxicity_severe_toxicity`,
`toxicity_sexually_explicit`, `toxicity_threat`. The README gives no full
example record. — [google-deepmind/streamingqa README](https://raw.githubusercontent.com/google-deepmind/streamingqa/main/README.md)

**ComplexTempQA (Gruber et al., 2024 arXiv; EMNLP 2025).** Verified columns from
the HF card `DataScienceUIBK/ComplexTempQA`: `id` (int64), `question` (string),
`answer` (sequence<string>), `type` (string), `rating` (int64), `timeframe`
(sequence<timestamp>), `question_entity` (sequence<string>), `answer_entity`
(sequence<string>), `question_country_entity` (sequence<string>),
`answer_country_entity` (sequence<string>), `is_unnamed` (int64). Real row:

```json
{"id": 1,
 "question": "Did the Winter Olympic Games in 1994 which had 1737 participants had a higher number of participants than the sports season in 2006 in Germany which had 32 participants?",
 "answer": ["yes"],
 "type": "2a",
 "rating": 1,
 "timeframe": ["1994-02-01T00:00:00", "2006-07-09T00:00:00"],
 "question_entity": ["9663", "37285"],
 "answer_entity": ["224013"],
 "question_country_entity": ["20", "183"],
 "answer_country_entity": null,
 "is_unnamed": 1}
```

— [HF DataScienceUIBK/ComplexTempQA](https://huggingface.co/datasets/DataScienceUIBK/ComplexTempQA);
paper [arXiv 2406.04866](https://arxiv.org/abs/2406.04866)

**TempQuestions (Jia et al., WWW'18 Companion; 2018) and TempQA-WD (IBM, 2021).**
The best machine-readable statement of TempQuestions' own fields comes from the
TempQA-WD README, which lists which fields it inherited: `"ID"`, `"TEXT"`,
`"FREEBASE_ANSWERS"`, `"TEMPORAL_SIGNAL"`, `"TYPE"`, `"DATA_SOURCE"`. TempQA-WD's
own test records add `"SPARQL"`, `"ANSWERS"`, `"CATEGORY"` (stated values:
`"Simple"`, `"Medium"`, `"Complex"`); dev records further add `"AMR"`,
`"LAMBDA"`, `"ENTITIES"` (each `{"SURFACEFORM","WIKIDATAID"}`), `"RELATIONS"`
(each `{"REFERENCE_EXPRESSION","SUBJECT","PROP","OBJECT","IS_REIFIED","IS_DATE"}`),
and `"LAMBDA_KBSPECIFIC"`. No example record is given in the README. —
[TempQA-WD README](https://github.com/AureliustechandTalentSolutions/TempQA-WD-Dataset/blob/main/README.md);
[IBM/tempqa-wd](https://github.com/IBM/tempqa-wd)

**Test of Time (Fatemi et al., ICLR 2025; data 2024).** Verified from the HF
card `baharef/ToT`. ToT-semantic and ToT-semantic-large: `question`,
`graph_gen_algorithm`, `question_type` (one of 7), `sorting_type`, `prompt`
(full prompt text used to evaluate LLMs), `label` (ground-truth answer).
ToT-arithmetic: `question`, `question_type`, `label`. Configs/sizes:
`tot_arithmetic` 2,800 test; `tot_semantic` 1,850 test; `tot_semantic_large`
46,480 test. The README ships no sample record. — [HF baharef/ToT README](https://huggingface.co/datasets/baharef/ToT/blob/main/README.md);
[ICLR paper](https://openreview.net/pdf?id=44CoQe6VCq)

**MenatQA (Wei et al., EMNLP 2023 Findings; 2023).** Repo ships
`datasets/MenatQA.json` (2.6 MB) and `datasets/1.json`; the README documents only
the three perturbation factors (scope, order, counterfactual) and no field list.
I could not read `MenatQA.json` (too large for a single fetch) and `1.json` is a
stub. Schema therefore **paper-only** here. —
[weiyifan1023/MenatQA](https://github.com/weiyifan1023/MenatQA);
[arXiv 2310.05157](https://arxiv.org/pdf/2310.05157)

**TimeBench (Chu et al., ACL 2024; 2023/2024).** It is an *aggregator*: three
categories — symbolic temporal reasoning (TimeX-NLI, Date Arithmetic),
commonsense temporal reasoning (MCTACO, TimeDial, DurationQA, SituatedGen), and
event temporal reasoning (TimeQA, TempReason, MenatQA, TRACIE). Each constituent
keeps its own schema; the README publishes no unified record format. —
[zchuz/TimeBench](https://github.com/zchuz/TimeBench); [arXiv 2311.17667](https://arxiv.org/abs/2311.17667)

**TempTabQA (Gupta et al., EMNLP 2023; 2023).** Zenodo record states the
packaging verbatim: *"Maindata: qapairs: split into train, dev, head, and tail
sets, in both csv and json formats; Tables: Wikipedia category and tables
metadata in csv, json and html formats"*, over "11,454 question-answer pairs
extracted from Wikipedia Infobox tables", with Head (popular domains) and Tail
(uncommon domains) test sets. Exact JSON keys are not published on Zenodo or the
project site. — [Zenodo 10022927](https://zenodo.org/records/10022927);
[temptabqa.github.io](https://temptabqa.github.io/);
[ACL Anthology 2023.emnlp-main.149](https://aclanthology.org/2023.emnlp-main.149/)

**SituatedQA (Zhang & Choi, EMNLP 2021; 2021), temporal split.** Dataset exists
as `siyue/SituatedQA` on HF (MIT, 10K–100K rows), but the dataset-server refused
the first-rows request (HTTP 501), so I have **no verified field list**. —
[HF siyue/SituatedQA](https://huggingface.co/datasets/siyue/SituatedQA)

**TIQ (Jia et al., WWW 2024; 2024).** Repo README documents the construction
pipeline and install steps only — no data-format section, no example record. —
[zhenjia2017/TIQ](https://github.com/zhenjia2017/TIQ);
[arXiv 2402.15400](https://arxiv.org/abs/2402.15400)

**TRAM (Wang & Zhao, ACL 2024 Findings; 2024).** HF card
`EternityYW/TRAM-Benchmark` returned HTTP 401 to the fetch tool; no verified
fields.

### Inferences

- The only two field names that appear in essentially every schema are
  `question` (or `query`) and an answer field that is **always a list**, even
  when a single string would do. Plan for list-valued gold answers.
- Identifier design splits two ways: opaque counters (`"0"` in TEMPREASON) versus
  composite keys that encode provenance and the query date
  (`"Q169814_P54_2010"`, `"/wiki/Knox_Cunningham#P39#0"`). The composite keys
  make (entity, relation, date) joins possible without extra columns.

### Gaps

- MenatQA, SituatedQA-temporal, TIQ, TempTabQA and TRAM: exact on-disk keys not
  confirmed. Each ships data but neither the README, the dataset card, nor the
  landing page states the schema in a fetchable form.
- TimeQA's *official* release (Google Drive, via the GitHub repo) may carry more
  fields than the `diwank` HF mirror; the repo README does not state the format
  and I could not fetch the Drive files.

## Q2. How the time anchor of a question is represented

### Takeaway

Four mechanisms are in use: a scalar query-date column (TempLAMA `date`,
TEMPREASON `date`), an integer timestamp on both question and evidence
(StreamingQA `question_ts` / `evidence_ts`), a start/end pair on the question
(ComplexTempQA `timeframe`), and time expressed only inside the question string
(TimeQA, Test of Time, TempQuestions). The newer, knowledge-update-oriented
datasets converge on an explicit machine-readable anchor; the reading-
comprehension ones do not.

### Cited Findings

- TempLAMA stores the anchor as a bare year string, `"date": "2010"`, and
  re-emits the same `query` once per year it is valid, with `id` suffixed by the
  year. — [HF Yova/templama](https://huggingface.co/datasets/Yova/templama)
- TEMPREASON stores `"date": "March 26, 1873"` as a free-text date string
  alongside the question, not a normalized ISO value. — [HF tonytan48/TempReason](https://huggingface.co/datasets/tonytan48/TempReason)
- StreamingQA is the only surveyed dataset with *two* timestamps per record:
  `question_ts` (int) for when the question is asked and `evidence_ts` (int) for
  when the supporting article was published, plus `recent_or_past` marking
  whether the answer is recent or historical relative to `question_ts`. —
  [google-deepmind/streamingqa README](https://raw.githubusercontent.com/google-deepmind/streamingqa/main/README.md)
- ComplexTempQA's `timeframe` is a *sequence of timestamps*; in the sampled row
  it holds two ISO datetimes, `["1994-02-01T00:00:00","2006-07-09T00:00:00"]`,
  i.e. the start/end of the period the question spans, not an as-of date. —
  [HF DataScienceUIBK/ComplexTempQA](https://huggingface.co/datasets/DataScienceUIBK/ComplexTempQA)
- TimeQA carries **no** time column at all; the anchor lives only in the question
  string (`"Which position did Knox Cunningham hold before Apr 1956?"`), and the
  survey flags exactly this: TimeQA *"lacks temporal metadata annotations and
  relies on Wikipedia snapshots"*. — [HF mirror](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train);
  [Piryani et al., "It's High Time: A Survey of Temporal Question Answering"](https://arxiv.org/html/2505.20243v1)
- The same survey says TEMPREASON *"covers 634–2023 but lacks temporal metadata,
  hindering focus-time estimation"* and TIQ *"emphasizes implicit temporal
  constraints but lacks comprehensive temporal metadata"* — so even a `date`
  column is judged insufficient when it is not a normalized, queryable focus
  time. — [arXiv 2505.20243](https://arxiv.org/html/2505.20243v1)
- The survey summarizes the field as using three encodings: explicit timestamps
  (e.g. publication dates), validity intervals marked with a "✓" temporal-
  metadata flag in its Table 1, and implicit grounding requiring inference. —
  [arXiv 2505.20243](https://arxiv.org/html/2505.20243v1)

### Inferences

- No surveyed dataset uses the literal key name `as_of`. The nearest
  equivalents are `date` (TempLAMA, TEMPREASON) and `question_ts` (StreamingQA).
- StreamingQA's separation of `question_ts` from `evidence_ts` is the only
  schema that can express "the document I must read is older than the date I am
  asking about" — structurally the same situation as a law in force on a date
  but enacted earlier.

### Gaps

- Whether any dataset stores a *validity interval on the answer* as an explicit
  pair of columns: I found none in the verified schemas. The survey's Table 1
  marks temporal metadata with a checkmark but I could not extract the per-row
  values (the PDF text layer failed to parse; the HTML version gave only a
  summary of the table, not the rows).

## Q3. Set-over-time answers: one record per (question, date), or intervals?

### Takeaway

Every verified dataset takes the **one record per (question, date)** route, or
else folds all time-varying answers into one list without intervals. No verified
schema stores `(interval, answer)` tuples on disk.

### Cited Findings

- TempLAMA materializes the cross-product: the same `query` (`"Valentino Rossi
  plays for _X_."`) appears once per year with a distinct `id`
  (`Q169814_P54_2010`) and its own `date`. The year-specific `answer` list is
  then supplemented by two *aggregate* fields, `most_frequent_answer` and
  `most_recent_answer` — the closest thing in any schema to acknowledging that
  the answer set varies over time, but they collapse the variation into single
  values rather than intervals. — [HF Yova/templama](https://huggingface.co/datasets/Yova/templama)
- TempLAMA's `answer` is a list of objects, each with a canonical
  `original_name` plus an alias list `name` and a `wikidata_id` — i.e. the list
  encodes *aliases of one answer* and *multiple simultaneous answers*, not
  answers at different times. — [HF Yova/templama](https://huggingface.co/datasets/Yova/templama)
- TEMPREASON keeps answers under a nested `text_answers.text` list and pushes
  the validity interval into the natural-language `context` instead: the paper's
  own example context is *"Eric Cantona played for Manchester United from Nov,
  1992 to May, 1997."* — [HF tonytan48/TempReason](https://huggingface.co/datasets/tonytan48/TempReason);
  [ACL 2023 paper](https://arxiv.org/pdf/2305.15014) (cited there as source of
  the L1/L2/L3 framing)
- TimeQA's `targets` is a flat list of answer strings for the one time
  constraint baked into the question; a different time constraint over the same
  Wikipedia page is a separate record with a different `idx` suffix
  (`#P39#0`, `#P39#1`, ...). — [HF mirror](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train)
- ComplexTempQA does carry a two-element `timeframe` per record, but it scopes
  the *question*, and the `answer` remains a flat sequence — no answer-to-
  interval binding. — [HF DataScienceUIBK/ComplexTempQA](https://huggingface.co/datasets/DataScienceUIBK/ComplexTempQA)

### Inferences

- The one-record-per-(question, date) convention is what makes TempLAMA usable
  for measuring knowledge staleness year by year; the cost is heavy duplication
  of the question string.
- The fact that TempLAMA needed `most_frequent_answer`/`most_recent_answer` as
  extra columns is evidence that a flat per-date schema loses information the
  evaluators wanted back.

### Gaps

- I found **no explicit statement of trade-offs** ("we chose one record per date
  because…") in any README or dataset card I could fetch. The papers may argue
  it in prose; the PDF text extraction failed for the two I tried (TimeQA
  2108.06314 and the survey 2505.20243 both returned unparseable binary).

## Q4. "No valid answer at this date" / unanswerable-at-time

### Takeaway

Only TimeQA has a documented convention, and it is a **sentinel string inside
the answer list**, not a boolean or a reason code. No verified schema carries a
machine-readable reason for unanswerability.

### Cited Findings

- TimeQA represents unanswerable instances as the literal string
  `"[unanswerable]"`; these arise when annotators mark a fact's time scope as
  "unknown", which the generator then turns into an unanswerable question. —
  [ar5iv rendering of arXiv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)
- TimeQA's paper reports a breakdown of model performance over answerable vs.
  unanswerable questions (FiD is noted as more answerability-aware), which
  implies the flag is derivable from `targets` alone — there is no separate
  boolean column in the shipped schema. — [arXiv 2108.06314](https://arxiv.org/pdf/2108.06314);
  schema per [HF mirror](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train)
- The survey's assessment of the field as a whole: *"The surveyed literature
  provides minimal discussion of unanswerable-question handling. Most datasets
  focus on answerable cases within bounded temporal ranges, representing a
  critical gap for real-world robustness assessment."* — [arXiv 2505.20243](https://arxiv.org/html/2505.20243v1)
- ComplexTempQA has a binary-looking `is_unnamed` (int64) column, but the card
  does not define it and it is not described as an answerability flag. —
  [HF DataScienceUIBK/ComplexTempQA](https://huggingface.co/datasets/DataScienceUIBK/ComplexTempQA)

### Inferences

- A sentinel string in the answer list is the only convention with any
  adoption; it is cheap but conflates "no answer exists at this date" with "the
  answer is the literal text `[unanswerable]`", and carries no reason code
  (not-yet-in-force vs. repealed vs. not-in-corpus).

### Gaps

- Whether MenatQA's counterfactual/scope perturbations introduce an explicit
  "no answer" marker: unverified (its data file was too large to fetch and the
  README does not say).
- The definition of ComplexTempQA's `is_unnamed`.

## Q5. Question type / reasoning-category metadata

### Takeaway

Categories are encoded three ways: **as a column** (ComplexTempQA `type`,
`rating`; Test of Time `question_type`; TempQuestions `TYPE` and
`TEMPORAL_SIGNAL`; TempQA-WD `CATEGORY`), **as a file name** (TEMPREASON's
`train_l2.json`, TimeQA's easy/hard files), or **not at all** in the record.

### Cited Findings

- TEMPREASON's L1/L2/L3 levels are **file-level**, not a column: the card's own
  error message references `train_l2.json`, and the verified feature list has no
  level field. L1 = time–time ("What is the year after 2010?"), L2 = event–time
  ("What team did Eric Cantona play for in 1995?"), L3 = event–event ("What team
  did Eric Cantona play for before Manchester United?"); L2/L3 additionally
  supply factual `context`. — [HF tonytan48/TempReason](https://huggingface.co/datasets/tonytan48/TempReason)
- TimeQA's easy/hard split is likewise file-level, and is defined by where the
  time specifier sits: easy questions use a specifier matching a temporal
  boundary explicitly stated in the text, so they need *"surface form rather than
  temporal reasoning"*; hard questions put the specifier *within* a time span,
  needing *"more temporal reasoning"*. Two splits of ~20K QA pairs over 5.5K
  time-evolving facts and 70 relations. — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314);
  [arXiv 2108.06314](https://arxiv.org/pdf/2108.06314)
- ComplexTempQA encodes type as a short opaque code in `type` (observed value
  `"2a"`) plus a difficulty `rating` (int64, documented as 0 = easy, 1 = hard);
  its taxonomy is Attribute / Comparison / Counting questions, further split by
  relation to events, entities or time periods. — [HF DataScienceUIBK/ComplexTempQA](https://huggingface.co/datasets/DataScienceUIBK/ComplexTempQA);
  [GitHub DataScienceUIBK/ComplexTempQA](https://github.com/datascienceuibk/complextempqa)
- Test of Time carries `question_type` ("one of 7 question types") in every
  record, and for the semantic subsets also `graph_gen_algorithm` (which
  synthetic graph generator produced the instance) and `sorting_type` (how facts
  were ordered in the prompt) — i.e. generation parameters kept as per-record
  metadata. — [HF baharef/ToT README](https://huggingface.co/datasets/baharef/ToT/blob/main/README.md)
- TempQuestions ships `TYPE` and `TEMPORAL_SIGNAL` per record; TempQA-WD adds
  `CATEGORY` with the stated values Simple / Medium / Complex. —
  [TempQA-WD README](https://github.com/AureliustechandTalentSolutions/TempQA-WD-Dataset/blob/main/README.md)
- StreamingQA's `recent_or_past` (str) is a temporal-category field: whether the
  question targets recent or past knowledge relative to `question_ts`. —
  [streamingqa README](https://raw.githubusercontent.com/google-deepmind/streamingqa/main/README.md)
- MenatQA's three factors — scope, order, counterfactual — are the stated
  taxonomy, but I could not confirm they appear as a record field. —
  [weiyifan1023/MenatQA](https://github.com/weiyifan1023/MenatQA)

### Inferences

- File-level encoding (TEMPREASON, TimeQA) makes the category invisible once
  records are concatenated or shuffled — a recurring practical annoyance for
  anyone doing per-category error analysis on a merged corpus.
- Test of Time is the only dataset that persists *how the item was generated*
  (`graph_gen_algorithm`, `sorting_type`) as first-class fields.

### Gaps

- The mapping from ComplexTempQA's `type` codes ("2a", …) to its taxonomy names
  is not given on the dataset card; it is presumably in the paper/GitHub, which
  I did not fetch in full.

## Q6. Provenance fields

### Takeaway

Provenance is usually a single id string, sometimes composite. Only StreamingQA
has a clean foreign key to a source document (`evidence_id`) plus its timestamp;
no verified dataset carries character-level span offsets or a snapshot date as
its own field.

### Cited Findings

- TimeQA: provenance is embedded in `idx` (`"/wiki/Knox_Cunningham#P39#0"` =
  Wikipedia page path + Wikidata property + instance index), and the record
  carries both a flat `context` string and a structured `paragraphs` list of
  `{title, text}` objects — passage-level, not offset-level. —
  [HF mirror](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train)
- TempLAMA: `relation` (Wikidata PID, e.g. `"P54"`), per-answer `wikidata_id`
  (e.g. `"Q1085474"`), and an `id` that encodes subject QID + PID + year. No URL,
  no snapshot date field. — [HF Yova/templama](https://huggingface.co/datasets/Yova/templama)
- StreamingQA: `evidence_id` (str) points at the source article and `evidence_ts`
  (int) gives its publication time — the only explicit document-id +
  snapshot-time pair among the verified schemas. It also uniquely ships six
  content-safety scores per record. — [streamingqa README](https://raw.githubusercontent.com/google-deepmind/streamingqa/main/README.md)
- ComplexTempQA: provenance is entity-level —`question_entity`, `answer_entity`,
  `question_country_entity`, `answer_country_entity`, all sequences of numeric id
  strings (e.g. `["9663","37285"]`). No document id or URL. —
  [HF DataScienceUIBK/ComplexTempQA](https://huggingface.co/datasets/DataScienceUIBK/ComplexTempQA)
- TempQA-WD: `SPARQL` (the executable query that produces the answer),
  `DATA_SOURCE`, `ENTITIES` with `{"SURFACEFORM","WIKIDATAID"}`, and `RELATIONS`
  with `{"REFERENCE_EXPRESSION","SUBJECT","PROP","OBJECT","IS_REIFIED","IS_DATE"}`
  — the richest provenance of any schema here, including an `IS_DATE` flag on
  each relation argument. — [TempQA-WD README](https://github.com/AureliustechandTalentSolutions/TempQA-WD-Dataset/blob/main/README.md)
- TEMPREASON: `context` is a plain string with no source id; `id` is a bare
  counter. Effectively no provenance. — [HF tonytan48/TempReason](https://huggingface.co/datasets/tonytan48/TempReason)

### Inferences

- Span offsets appear nowhere in the verified schemas; extractive datasets
  either give the passage list (TimeQA) or trust string matching.
- Wikipedia/Wikidata-derived datasets substitute *entity ids* for *document
  ids*, which works because the KB is the source of truth. A corpus where the
  authoritative text is the document (as with statute text) has no analogue in
  these schemas.

### Gaps

- Snapshot/dump dates: none of the verified schemas carries one per record.
  TimeQA and SituatedQA are described by the survey as relying on Wikipedia
  snapshots (SituatedQA *"≤2021"*), but the snapshot date is dataset-level
  documentation, not a field. — [arXiv 2505.20243](https://arxiv.org/html/2505.20243v1)

## Q7. `question` vs `question_template` / generated-vs-human-written flags

### Takeaway

Only **StreamingQA** ships a per-record human-vs-machine provenance flag
(`written_or_generated`). Template information is otherwise discarded: TimeQA and
TempLAMA are template-generated but ship only the realized string.

### Cited Findings

- StreamingQA: `written_or_generated` (str) is a documented top-level field,
  sitting next to `recent_or_past`. — [streamingqa README](https://raw.githubusercontent.com/google-deepmind/streamingqa/main/README.md)
- TimeQA generates questions from hand-written templates — *"For each given
  relation, we manually write 2-5 different templates"*, with reasoning types
  `in`, `before`, `after`, `between`, and randomly sampled times filling the
  placeholders — but the shipped record has no template id or template text,
  only `question`. — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314);
  schema per [HF mirror](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train)
- TempLAMA's `query` is itself a cloze template with a `_X_` slot
  (`"Valentino Rossi plays for _X_."`) — the template *is* the question field, so
  the distinction collapses. — [HF Yova/templama](https://huggingface.co/datasets/Yova/templama)
- Test of Time keeps the whole realized `prompt` alongside `question`, plus the
  generator parameters `graph_gen_algorithm` and `sorting_type` — the closest
  any dataset comes to storing "how this question was produced". —
  [HF baharef/ToT README](https://huggingface.co/datasets/baharef/ToT/blob/main/README.md)
- The survey records creation method as a *dataset-level* attribute — crowdsourced
  (CS) vs. automatically generated (AG) — in its comparison table, confirming the
  field is normally not per-record. — [arXiv 2505.20243](https://arxiv.org/html/2505.20243v1)

### Inferences

- Because the CS/AG distinction is usually dataset-level, mixed datasets cannot
  be filtered by it after the fact; StreamingQA's per-record flag is the
  exception that allows that analysis.

### Gaps

- No source I fetched states *why* StreamingQA kept the flag (the README lists it
  without rationale).

## Q8. Documented failure modes and critiques of these schemas

### Takeaway

The dominant, repeatedly stated criticism is **missing temporal metadata**: the
time anchor lives in the question text rather than in a field, so focus-time
estimation and per-date evaluation are impossible. Secondary critiques are
annotation noise inherited from automatic construction, snapshot staleness, and
small scale.

### Cited Findings

From Piryani et al., *"It's High Time: A Survey of Temporal Question Answering"*
([arXiv 2505.20243](https://arxiv.org/html/2505.20243v1)), per-dataset:

- TimeQA *"lacks temporal metadata annotations and relies on Wikipedia snapshots,
  limiting applicability to evolving information."*
- TempLAMA *"focuses narrowly on extractive answers from 2010–2020 news,
  constraining reasoning complexity."*
- TempQuestions *"contains only 1.2K instances and requires multi-hop reasoning
  that current models struggle with."*
- TEMPREASON *"covers 634–2023 but lacks temporal metadata, hindering focus-time
  estimation."*
- StreamingQA *"(147K questions) uniquely addresses knowledge updates over time
  but emphasizes extractive answering."*
- SituatedQA *"restricts scope to Wikipedia snapshots (≤2021), limiting
  real-world temporal drift assessment."*
- ComplexTempQA *"(100K+ questions) supports multi-hop reasoning but inherits
  Wikipedia's inherent temporal biases."*
- MenatQA *"extracts only 2.8K crowdsourced questions, reducing statistical
  robustness."*
- TimeBench *"includes future-oriented tasks but remains relatively small-scale."*
- TRAM *"evaluates LLM reasoning (event ordering, arithmetic, duration) but
  identifies significant gaps versus human performance."*
- TIQ *"emphasizes implicit temporal constraints but lacks comprehensive temporal
  metadata."*
- On no-answer cases: *"The surveyed literature provides minimal discussion of
  unanswerable-question handling. Most datasets focus on answerable cases within
  bounded temporal ranges, representing a critical gap for real-world robustness
  assessment."*
- On ambiguity: *"a persistent issue being temporal ambiguity where missing or
  implicit time references hinder both annotation and evaluation."*

Other critiques found:

- TimeQA is reported to *"inherit noisy or inaccurate annotations from source
  datasets, including captions and timestamps,"* with some errors not
  automatically filterable. — surfaced via search over
  [arXiv 2505.20243](https://arxiv.org/pdf/2505.20243) and related literature
  (see Gaps: I could not pin this sentence to a specific page).
- TimeQA's own paper reports a large human–model gap on the hard split (~46% vs.
  ~87%) and names the difficulties as temporal understanding of implicit
  expressions, relating query time to document facts, and *termination reasoning*
  — inferring when a fact stopped holding. — [ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)
- A memorization-leakage critique motivated UnSeenTimeQA, which argues
  time-sensitive benchmarks built from Wikipedia are contaminated by LLM
  pretraining memorization and therefore build questions *"beyond LLMs'
  memorization."* — [arXiv 2407.03525](https://arxiv.org/pdf/2407.03525)

### Inferences

- "Termination reasoning" (when did a fact stop holding) is the failure mode
  closest to legal validity intervals, and the schemas that omit an interval are
  exactly the ones where it is hardest.
- The survey's criticism pattern suggests two schema-level defects recur:
  (a) time anchor not machine-readable, (b) no unanswerable/no-answer
  representation. Both are schema choices, not corpus choices.

### Gaps

- I could not extract the survey's Table 1 row-by-row (per-dataset year, size,
  source, and the temporal-metadata ✓/✗ column). The PDF text layer failed to
  parse and the HTML fetch returned only a prose summary of the table. A future
  pass should read `arXiv:2505.20243` Table 1 directly.
- The "noisy captions and timestamps" sentence surfaced through search snippets;
  I could not confirm which paper and page it belongs to, so treat it as
  unverified.
- No later paper I found critiques a specific *field name* choice; critiques are
  at the level of "metadata missing", not "this key is wrong".

## Cross-cutting summary table (verified fields only)

| Dataset | Year | Time anchor field(s) | Answer field | Type/category field | Provenance field(s) |
|---|---|---|---|---|---|
| TempQuestions | 2018 | none (in text) | `FREEBASE_ANSWERS` | `TYPE`, `TEMPORAL_SIGNAL` | `ID`, `DATA_SOURCE` |
| TimeQA | 2021 | none (in question string) | `targets` (list; `"[unanswerable]"` sentinel) | file-level easy/hard | `idx`, `paragraphs[].title` |
| TempLAMA | 2021 | `date` (year string) | `answer` (list of `{wikidata_id, name[], original_name[]}`) | `relation` (PID) | `id` (`QID_PID_year`), `wikidata_id` |
| SituatedQA | 2021 | unverified | unverified | unverified | unverified |
| StreamingQA | 2022 | `question_ts`, `evidence_ts` (int) | `answers`, `answers_additional` | `recent_or_past`, `written_or_generated` | `evidence_id`, `qa_id` |
| TEMPREASON | 2023 | `date` (free-text) | `text_answers.text` (list) | file-level L1/L2/L3 | none (`id` is a counter) |
| MenatQA | 2023 | unverified | unverified | scope/order/counterfactual (unverified as field) | unverified |
| TempTabQA | 2023 | unverified | unverified | head/tail split, file-level | unverified |
| TimeBench | 2024 | inherits constituents | inherits | 3 categories, dataset-level | inherits |
| TRAM | 2024 | unverified | unverified | unverified | unverified |
| ComplexTempQA | 2024 | `timeframe` (seq of ISO timestamps) | `answer` (seq) | `type` (code), `rating` (0/1) | `question_entity`, `answer_entity`, `*_country_entity` |
| TIQ | 2024 | unverified | unverified | unverified | unverified |
| Test of Time | 2024/25 | none (synthetic, in text) | `label` | `question_type` | `graph_gen_algorithm`, `sorting_type`, `prompt` |

Superseded / caveats: TempQuestions (2018, 1.2K items) is superseded in scale by
TempQA-WD (same questions, Wikidata-grounded, richer fields) and by
ComplexTempQA. TimeQA's schema is the most widely reused but is the one the
survey singles out for lacking temporal metadata. TempLAMA's cloze format
(`_X_`) is tied to LM probing and is not a natural-question format.
