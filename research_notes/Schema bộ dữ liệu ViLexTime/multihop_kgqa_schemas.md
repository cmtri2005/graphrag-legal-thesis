# Record-level schemas of multi-hop QA and KG/RAG-grounded QA benchmarks

Scope note: every JSON block below was pulled live (HuggingFace `datasets-server`
`/first-rows` API, HF dataset cards, or raw GitHub files) on 2026-09-21. Where a
record could not be retrieved verbatim, that is stated as a gap rather than
paraphrased into a fake quote.

---

## Q1. Exact top-level JSON keys of one record, per benchmark

### Takeaway

The dominant reading-comprehension multi-hop schema is HotpotQA's
`{id, question, answer, type, level, supporting_facts, context}`, copied almost
verbatim by 2WikiMultihopQA (which adds `evidences` triples and `entity_ids`) and
restructured by MuSiQue (`paragraphs` with `is_supporting` flags +
`question_decomposition`). RAG-era benchmarks (MultiHop-RAG, CRAG, RAGBench,
GraphRAG-Bench) drop `supporting_facts` and instead carry a list of
document/evidence objects with metadata, plus a categorical `question_type`.

### Cited Findings

**HotpotQA** — top-level keys `id, question, answer, type, level,
supporting_facts, context`. The HF card gives this record shape — [HuggingFace: hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa):

```json
{
  "answer": "This is the answer",
  "context": {
    "sentences": [["Sent 1"], ["Sent 21", "Sent 22"]],
    "title": ["Title1", "Title 2"]
  },
  "id": "000001",
  "level": "medium",
  "question": "What is the answer?",
  "supporting_facts": {
    "sent_id": [0, 1, 3],
    "title": ["Title of para 1", "Title of para 2", "Title of para 3"]
  },
  "type": "comparison"
}
```
`type` ∈ {`comparison`, `bridge`}; `level` ∈ {`easy`, `medium`, `hard`} — [HuggingFace: hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)

**2WikiMultihopQA** — keys `_id, type, question, context, supporting_facts,
evidences, answer` (+ `entity_ids` in the released full files). Verbatim first
record of `dev.json`, abridged in the `context` middle only — [HF mirror: voidful/2WikiMultihopQA dev.json](https://huggingface.co/datasets/voidful/2WikiMultihopQA/resolve/main/dev.json):

```json
{
  "_id": "8813f87c0bdd11eba7f7acde48001122",
  "type": "compositional",
  "question": "Who is the mother of the director of film Polish-Russian War (Film)?",
  "context": [
    ["Maheen Khan", ["Maheen Khan is a Pakistani fashion and costume designer, ...", "..."]],
    ["Polish-Russian War (film)", ["Polish-Russian War", "(Wojna polsko-ruska) is a 2009 Polish film directed by Xawery Żuławski based on the novel ..."]],
    ["Xawery Żuławski", ["Xawery Żuławski (born 22 December 1971 in Warsaw) is a Polish film director.", "In 1995 he graduated National Film School in Łódź.", "He is the son of actress Małgorzata Braunek and director Andrzej Żuławski.", "..."]]
  ],
  "supporting_facts": [["Polish-Russian War (film)", 1], ["Xawery Żuławski", 2]],
  "evidences": [
    ["Polish-Russian War", "director", "Xawery Żuławski"],
    ["Xawery Żuławski", "mother", "Małgorzata Braunek"]
  ],
  "answer": "Małgorzata Braunek"
}
```

Official field definitions: `supporting_facts` = "a list, each element is a list
that contains: [title, sent_id]"; `context` = "a list, each element is a list
that contains [title, sentences]"; `evidences` = "a list, each element is a
triple that contains [subject entity, relation, object entity]" (absent in test);
`entity_ids` = "a string that contains the two Wikidata ids ... of the gold
paragraphs"; `type` ∈ {comparison, inference, compositional, bridge_comparison},
where bridge_comparison carries four Wikidata IDs instead of two — [Alab-NII/2wikimultihop README](https://raw.githubusercontent.com/Alab-NII/2wikimultihop/main/README.md)

**MuSiQue** — exact feature spec from the HF viewer — [datasets-server first-rows, dgslibisey/MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation):

```
id                     : string            e.g. "2hop__460946_294723"
paragraphs             : list of {idx:int, title:str, paragraph_text:str, is_supporting:bool}
question               : string
question_decomposition : list of {id:int, question:str, answer:str, paragraph_support_idx:int}
answer                 : string
answer_aliases         : list of string
answerable             : bool
```
The hop count is encoded **inside the id string** (`2hop__…`), not in a separate
field — [datasets-server, dgslibisey/MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation). The MuSiQue README lists exactly these seven
fields — [StonyBrookNLP/musique](https://github.com/StonyBrookNLP/musique)

**QAngaroo / WikiHop** — keys `query, supports, candidates, answer, id`. Real row — [datasets-server, community-datasets/qangaroo config wikihop](https://datasets-server.huggingface.co/first-rows?dataset=community-datasets%2Fqangaroo&config=wikihop&split=train):

```json
{
  "query": "participant_of juan rossell",
  "supports": ["The 2004 Summer Olympic Games, officially known as ...", "The Pan-American or Pan American Games ..."],
  "candidates": ["..."],
  "answer": "...",
  "id": "..."
}
```
Note `query` is a *relation + subject* pair, not natural language — WikiHop is
KB-seeded but ships no triple id.

**ComplexWebQuestions** — keys `ID, answers, composition_answer,
compositionality_type, created, machine_question, question, sparql, webqsp_ID,
webqsp_question`. Real row — [datasets-server, drt/complex_web_questions](https://datasets-server.huggingface.co/first-rows?dataset=drt%2Fcomplex_web_questions&config=complex_web_questions&split=train):

```json
{
  "ID": "WebQTrn-3513_7c4117891abf63781b892537979054c6",
  "answers": {"aliases": [["Washington D.C.", "Washington", "The District", "..."]],
              "answer": ["Washington, D.C."], "answer_id": ["m.0rh6k"]},
  "composition_answer": "george washington university",
  "compositionality_type": "composition",
  "created": "2018-02-13T02:07:47",
  "machine_question": "what state is the the education institution has a sports team named George Washington Colonials men's basketball in",
  "question": "What state is home to the university that is represented in sports by George Washington Colonials men's basketball?",
  "sparql": "PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?x\nWHERE {\nFILTER (?x != ?c)\n?c ns:education.educational_institution.sports_teams ns:m.03d0l76 . \n?c ns:organization.organization.headquarters ?y .\n?y ns:location.mailing_address.state_province_region ?x .\n}\n",
  "webqsp_ID": "WebQTrn-3513",
  "webqsp_question": "what ..."
}
```

**StrategyQA** — the widely mirrored trimmed version has `qid, term,
description, question, answer, facts`. Real row — [datasets-server, ChilleD/StrategyQA](https://datasets-server.huggingface.co/first-rows?dataset=ChilleD%2FStrategyQA&config=default&split=train):

```json
{
  "qid": "4fd64bb6ce5b78ab20b6",
  "term": "Mixed martial arts",
  "description": "full contact combat sport",
  "question": "Is Mixed martial arts totally original from Roman Colosseum games?",
  "answer": false,
  "facts": "Mixed Martial arts in the UFC takes place in an enclosed structure called The Octagon. The Roman Colosseum games were fought in enclosed arenas ..."
}
```
The official AI2 release additionally carries `decomposition` and `evidence`
(see Q6/Q7).

**MultiHop-RAG** — keys `query, evidence_list, question_type, answer`. Real row
(evidence_list abridged to two of three items) — [datasets-server, yixuantt/MultiHopRAG](https://datasets-server.huggingface.co/first-rows?dataset=yixuantt%2FMultiHopRAG&config=MultiHopRAG&split=train):

```json
{
  "query": "Who is the individual associated with the cryptocurrency industry facing a criminal trial on fraud and conspiracy charges, as reported by both The Verge and TechCrunch, and is accused by prosecutors of committing fraud for personal gain?",
  "evidence_list": [
    {"author": "Elizabeth Lopatto", "category": "technology",
     "fact": "Before his fall, Bankman-Fried made himself out to be the Good Boy of crypto — the trustworthy face of a sometimes-shady industry.",
     "published_at": "2023-09-28T12:00:00+00:00", "source": "The Verge",
     "title": "The FTX trial is bigger than Sam Bankman-Fried",
     "url": "https://www.theverge.com/2023/9/28/23893269/ftx-sam-bankman-fried-trial-evidence-crypto"},
    {"author": "Jacquelyn Melinek", "category": "technology",
     "fact": "The highly anticipated criminal trial for Sam Bankman-Fried, former CEO of bankrupt crypto exchange FTX, started Tuesday ...",
     "published_at": "2023-10-01T14:00:29+00:00", "source": "TechCrunch",
     "title": "SBF's trial starts soon, but how did he — and FTX — get here?",
     "url": "https://techcrunch.com/2023/10/01/ftx-lawsuit-timeline/"}
  ],
  "question_type": "inference_query",
  "answer": "Sam Bankman-Fried"
}
```
Each `fact` is a verbatim sentence from the named article; the article is
identified by `title`+`url`+`published_at`, i.e. **metadata, not a chunk id** — [datasets-server, yixuantt/MultiHopRAG](https://datasets-server.huggingface.co/first-rows?dataset=yixuantt%2FMultiHopRAG&config=MultiHopRAG&split=train)

**CRAG (KDD Cup 2024, Meta)** — official schema table — [facebookresearch/CRAG docs/dataset.md](https://raw.githubusercontent.com/facebookresearch/CRAG/main/docs/dataset.md):

| Field | Type | Meaning |
|---|---|---|
| `interaction_id` | string | unique identifier for each example |
| `query_time` | string | date/time when the query and the web search occurred |
| `domain` | string | finance, music, movie, sports, open |
| `question_type` | string | simple, simple_w_condition, comparison, aggregation, set, false_premise, post-processing, **multi-hop** |
| `static_or_dynamic` | string | static, slow-changing, fast-changing, real-time |
| `query` | string | the question |
| `answer` | string | gold answer |
| `alt_ans` | list | other valid gold answers |
| `split` | integer | 0 = validation, 1 = public test |
| `popularity` | string | head / torso / tail; **non-empty ⇒ the answer came from the KG**, empty ⇒ from the web |
| `search_results` | list of JSON | up to k HTML pages: `page_name, page_url, page_snippet, page_result, page_last_modified` |

**CRAG-MM (2025)** — per-turn fields are `interaction_id, domain,
query_category, dynamism, query, image_quality`; `query_category` is a ClassLabel
whose values are `reasoning, comparison, aggregation, simple-recognition,
simple-knowledge, multi-hop` — [datasets-server, crag-mm-2025/crag-mm-single-turn-public](https://datasets-server.huggingface.co/first-rows?dataset=crag-mm-2025%2Fcrag-mm-single-turn-public&config=default&split=validation)

**RAGBench (Galileo)** — keys, from the live feature spec — [datasets-server, galileo-ai/ragbench config hotpotqa](https://datasets-server.huggingface.co/first-rows?dataset=galileo-ai%2Fragbench&config=hotpotqa&split=test):

```
id, question, documents (list[str]), response,
generation_model_name, annotating_model_name, dataset_name,
documents_sentences   : list[list[list[str]]]   # doc -> sentence -> [key, text]
response_sentences    : list[list[str]]
sentence_support_information : list of {response_sentence_key, supporting_sentence_keys, fully_supported, explanation}
unsupported_response_sentence_keys : list[str]
adherence_score : bool
overall_supported_explanation : str
relevance_explanation : str
all_relevant_sentence_keys : list[str]
all_utilized_sentence_keys : list[str]
```
This is the closest real thing to a "used context ids" convention: sentence-level
string keys (e.g. `0a`, `1c`) with separate **relevant** vs **utilized** sets.

**GraphRAG-Bench** — keys `id, source, question, answer, question_type,
evidence, evidence_relations`. Real rows — [datasets-server, GraphRAG-Bench/GraphRAG-Bench config medical](https://datasets-server.huggingface.co/first-rows?dataset=GraphRAG-Bench%2FGraphRAG-Bench&config=medical&split=train):

```json
{
  "id": "Medical-a8bad1cf",
  "source": "Medical",
  "question": "From which cell type does basal cell carcinoma arise?",
  "answer": "Basal cell carcinoma arises from basal cells in the lower part of the epidermis.",
  "question_type": "Fact Retrieval",
  "evidence": ["Basal cell carcinoma arises from basal cells.",
               "Basal cells are located in the lower part of the epidermis."],
  "evidence_relations": "BCC arises from basal cells in the lower part of the epidermis"
}
```
`evidence` is a list of atomic natural-language propositions (not ids, not spans);
`evidence_relations` is a JSON-typed column carrying the graph relation(s) behind
the question. Configs are `medical` and `novel` — [datasets-server splits, GraphRAG-Bench/GraphRAG-Bench](https://datasets-server.huggingface.co/splits?dataset=GraphRAG-Bench%2FGraphRAG-Bench)

### Inferences

- There are exactly two stable families. **Family A (reading-comprehension)**:
  context is shipped *inside* the record as titled paragraphs, and grounding is a
  pointer into that inline context (`[title, sent_id]` or `paragraph_support_idx`).
  **Family B (retrieval/RAG)**: context lives in a separate corpus, and the record
  carries either verbatim evidence strings + source metadata (MultiHop-RAG,
  GraphRAG-Bench) or sentence keys into shipped documents (RAGBench).
- A Vietnamese legal temporal benchmark generated *from* a TKG sits naturally in
  Family B with a Family-A-style pointer: i.e. GraphRAG-Bench's `evidence` +
  `evidence_relations` pair is the nearest published precedent for "answer traced
  back to the graph".

### Gaps

- **FreshQA**: no schema retrieved. HF hosts only third-party forks
  (`SeaLLMs/FreshQA-multilingual`, `bojanbabic/freshqa_*`); the canonical release
  is a Google Sheet in `google/FreshLLMs`, which I did not fetch. Do not assert
  FreshQA field names without checking that sheet.
- **STaRK** (semi-structured KB retrieval benchmark, `stark-qa`): HF search for
  `stark-qa` returned zero datasets; not verified. Treat as unverified.
- **CRAG text task 1/2 rows**: the HF mirror `Quivr/CRAG` fails to parse in the
  viewer, so only the documented schema table above is sourced, not a live row.

---

## Q2. Where does `hop_level` (or `hop`, `num_hops`, `hops`, `level`, `type`) literally appear?

### Takeaway

**`hop_level` is not a field name I could trace to any published dataset.** The
real conventions are: HotpotQA's `level` (difficulty, *not* hops), HotpotQA/2Wiki
`type` (reasoning shape), CRAG/MultiHop-RAG/CRAG-MM `question_type` (with
`multi-hop` as one value), MuSiQue's hop count baked into the `id` prefix, and
GrailQA's `level` (generalization split, *not* hops).

### Cited Findings

- `level` in **HotpotQA** takes `easy` / `medium` / `hard` — annotator difficulty,
  unrelated to hop count — [HuggingFace: hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
- `type` in **HotpotQA** takes `comparison` / `bridge` — [HuggingFace: hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
- `type` in **2WikiMultihopQA** takes `comparison` / `inference` /
  `compositional` / `bridge_comparison` — [Alab-NII/2wikimultihop README](https://raw.githubusercontent.com/Alab-NII/2wikimultihop/main/README.md)
- **MuSiQue** has no hop field; hop count is a prefix of `id`, e.g.
  `"id": "2hop__460946_294723"` — [datasets-server, dgslibisey/MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation)
- **CRAG** `question_type` enumerates `simple, simple_w_condition, comparison,
  aggregation, set, false_premise, post-processing, multi-hop` — [facebookresearch/CRAG docs/dataset.md](https://raw.githubusercontent.com/facebookresearch/CRAG/main/docs/dataset.md)
- **CRAG-MM** `query_category` ClassLabel: `reasoning, comparison, aggregation,
  simple-recognition, simple-knowledge, multi-hop` — [datasets-server, crag-mm-2025/crag-mm-single-turn-public](https://datasets-server.huggingface.co/first-rows?dataset=crag-mm-2025%2Fcrag-mm-single-turn-public&config=default&split=validation)
- **MultiHop-RAG** `question_type` — observed value `inference_query` — [datasets-server, yixuantt/MultiHopRAG](https://datasets-server.huggingface.co/first-rows?dataset=yixuantt%2FMultiHopRAG&config=MultiHopRAG&split=train)
- **GraphRAG-Bench** `question_type` — observed value `Fact Retrieval` — [datasets-server, GraphRAG-Bench/GraphRAG-Bench](https://datasets-server.huggingface.co/first-rows?dataset=GraphRAG-Bench%2FGraphRAG-Bench&config=medical&split=train)
- **GrailQA** has a top-level field literally named `level`, but its values are
  the three *generalization* levels: "It can be used to test three levels of
  generalization in KBQA: i.i.d., compositional, and zero-shot" — [dki-lab/GrailQA README](https://raw.githubusercontent.com/dki-lab/GrailQA/main/README.md); the field
  is confirmed present in the record schema — [datasets-server, Hieuman/grail_qa](https://datasets-server.huggingface.co/first-rows?dataset=Hieuman%2Fgrail_qa&config=default&split=validation)
- **GrailQA** does carry structural size counters instead: `num_node` (e.g. 3) and
  `num_edge` (e.g. 2) — [datasets-server, Hieuman/grail_qa](https://datasets-server.huggingface.co/first-rows?dataset=Hieuman%2Fgrail_qa&config=default&split=validation)
- **NovelHopQA** is described as stratified into "hop depths H ∈ {1,2,3,4}" with
  ~1,000 examples per hop level — [NovelHopQA arXiv:2506.02000](https://arxiv.org/abs/2506.02000). I could **not** confirm the
  JSON field name; the only hits using the phrase "hop level" were an aggregator
  site — [emergentmind: NovelHopQA](https://www.emergentmind.com/topics/novelhopqa) — which is not a primary source.

### Inferences

- `hop_level` reads like a portmanteau of HotpotQA's `level` and the generic
  "hop" vocabulary. It is a **reasonable, self-documenting name but not a
  standard**. If interoperability matters, the safer choices are `num_hops`
  (integer, unambiguous) plus a separate categorical `question_type`; HotpotQA's
  `level` is actively misleading because two major datasets (HotpotQA, GrailQA)
  already use `level` for two *different* non-hop meanings.
- MuSiQue's `2hop__…` id convention is worth copying for a temporal legal
  benchmark: it makes hop count visible in filenames, logs and error reports with
  zero schema cost, and it survives CSV/TSV round-tripping.

### Gaps

- No published dataset with a literal `hop_level` key was found. Searching
  `"hop_level" multi-hop QA benchmark field` returned no primary source — [WebSearch result set](https://www.emergentmind.com/topics/multi-hop-question-answering-qa-benchmarks). **No published source found for `hop_level`.**
- NovelHopQA's and MoreHopQA's actual column names are unverified (the HF viewer
  for `alabnii/morehopqa` returned no feature block for either split I tried).

---

## Q3. How gold/retrieved context is linked to the answer

### Takeaway

Four distinct real mechanisms exist: (a) `[title, sent_id]` pointers into inline
context (HotpotQA, 2Wiki); (b) per-paragraph boolean `is_supporting` + integer
`paragraph_support_idx` (MuSiQue); (c) verbatim evidence sentences plus source
metadata (MultiHop-RAG, GraphRAG-Bench, StrategyQA `facts`); (d) sentence-level
string keys with separate relevant/utilized sets (RAGBench). Only (d) is really
an "id list".

### Cited Findings

- **HotpotQA** `supporting_facts` is a parallel-array struct
  `{"title": [str], "sent_id": [int]}`, each pair pointing at one sentence of the
  inline `context` — [HuggingFace: hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
- **2WikiMultihopQA** keeps the same `[title, sent_id]` list form, e.g.
  `"supporting_facts": [["Polish-Russian War (film)", 1], ["Xawery Żuławski", 2]]`,
  and *adds* a parallel `evidences` list of `[subject, relation, object]` triples — [voidful/2WikiMultihopQA dev.json](https://huggingface.co/datasets/voidful/2WikiMultihopQA/resolve/main/dev.json)
- **MuSiQue** flags support twice: `paragraphs[i].is_supporting: bool` and, per
  decomposition step, `question_decomposition[j].paragraph_support_idx: int`
  pointing at `paragraphs[i].idx` — [datasets-server, dgslibisey/MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation)
- **MultiHop-RAG** stores the gold span as a literal `fact` string per evidence
  item, keyed by `title`/`url`/`published_at`/`source`/`author`/`category` rather
  than by a chunk id — [datasets-server, yixuantt/MultiHopRAG](https://datasets-server.huggingface.co/first-rows?dataset=yixuantt%2FMultiHopRAG&config=MultiHopRAG&split=train)
- **RAGBench** decomposes both sides into keyed sentences: `documents_sentences`
  (`doc → sentence → [key, text]`), `response_sentences`, then
  `sentence_support_information[*].supporting_sentence_keys`,
  `all_relevant_sentence_keys` and `all_utilized_sentence_keys` — [datasets-server, galileo-ai/ragbench](https://datasets-server.huggingface.co/first-rows?dataset=galileo-ai%2Fragbench&config=hotpotqa&split=test)
- **GraphRAG-Bench** stores `evidence` as a list of atomic propositions and
  `evidence_relations` as a JSON column holding the underlying graph relation — [datasets-server, GraphRAG-Bench/GraphRAG-Bench](https://datasets-server.huggingface.co/first-rows?dataset=GraphRAG-Bench%2FGraphRAG-Bench&config=medical&split=train)
- **QAngaroo/WikiHop** ships `supports` (a flat list of paragraph strings) with
  **no** annotation of which support is gold — [datasets-server, community-datasets/qangaroo](https://datasets-server.huggingface.co/first-rows?dataset=community-datasets%2Fqangaroo&config=wikihop&split=train)

### Inferences

- RAGBench's split between `all_relevant_sentence_keys` and
  `all_utilized_sentence_keys` is the only published schema that distinguishes
  "context that *could* ground the answer" from "context the answer actually
  *used*". For a TKG-generated legal benchmark this distinction is directly
  useful: relevant = every provision version matching the query's time window;
  utilized = the versions the gold answer actually cites.
- 2Wiki is the single best template for the consumer's use case: it carries an
  inline sentence-level pointer *and* the generating triple, in the same record.

### Gaps

- I did not verify the string format of RAGBench sentence keys from a live row
  (the feature spec shows `list[list[list[str]]]` but the row payload was
  truncated). Confirm the key format before copying it.

---

## Q4. Are `used_context_ids` and `context_block` real conventions?

### Takeaway

**No published source found for either name.** Both appear to be from an unnamed
in-house or LLM-generated pipeline. Ragas — the most likely framework origin —
uses `reference_contexts`, not `used_context_ids` or `context_block`.

### Cited Findings

- A targeted search for `"used_context_ids" dataset schema` returned no dataset,
  paper or framework using that key; results were unrelated patents and
  schema.org material — [WebSearch: "used_context_ids" dataset schema](https://schema.org/Dataset)
- A targeted search for `"context_block" QA dataset schema field` likewise
  returned no QA dataset using that key; the only `block` schema hit was Sanity
  CMS's rich-text "block" type, unrelated to QA — [Sanity schema types docs](https://www.sanity.io/docs/studio/schema-types)
- **Ragas** testset records are `TestsetSample` objects: "eval_sample : Union[SingleTurnSample, MultiTurnSample] … synthesizer_name : str — The name of the
  synthesizer used to generate this sample", and `Testset.to_list()` emits each
  eval sample's fields plus `sample_dict["synthesizer_name"]` — [ragas/src/ragas/testset/synthesizers/testset_schema.py](https://raw.githubusercontent.com/explodinggradients/ragas/main/src/ragas/testset/synthesizers/testset_schema.py)
- The Ragas RAG testset-generation docs show the generated record as
  `SingleTurnSample(user_input=query, reference_contexts=contexts, reference=reference)` — [Ragas docs: test data generation for RAG](https://docs.ragas.io/en/stable/concepts/test_data_generation/rag/)
- The closest real equivalents to `used_context_ids` are RAGBench's
  `all_utilized_sentence_keys` / `supporting_sentence_keys` — [datasets-server, galileo-ai/ragbench](https://datasets-server.huggingface.co/first-rows?dataset=galileo-ai%2Fragbench&config=hotpotqa&split=test) — and MuSiQue's
  `paragraph_support_idx` — [datasets-server, dgslibisey/MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation)
- The closest real equivalent to `context_block` is HotpotQA/2Wiki's `context`
  (list of `[title, sentences]`) — [Alab-NII/2wikimultihop README](https://raw.githubusercontent.com/Alab-NII/2wikimultihop/main/README.md) — or RAGBench's `documents` (list of
  strings) — [datasets-server, galileo-ai/ragbench](https://datasets-server.huggingface.co/first-rows?dataset=galileo-ai%2Fragbench&config=hotpotqa&split=test)

### Inferences

- `used_context_ids` is semantically sound and maps cleanly onto RAGBench's
  `all_utilized_sentence_keys`; `context_block` maps onto `context` / `documents`.
  Renaming to the published names costs nothing and buys tooling compatibility
  (HotpotQA-format evaluators, Ragas `SingleTurnSample`, HF `datasets` loaders).
- Ragas notably does **not** persist a hop count or a context-id list in its
  testset schema — provenance is limited to `synthesizer_name` (which synthesizer
  built the sample) plus `reference_contexts` (the chunk *texts*, inlined). Any
  claim that "LLM-QA pipelines standardly emit `used_context_ids`" is unsupported.

### Gaps

- I did not check DeepEval, TruLens or LlamaIndex synthetic-dataset schemas
  directly (call budget). Given Ragas is the most-cited of the four and does not
  use these names, the negative result is suggestive but not exhaustive for
  DeepEval/TruLens/LlamaIndex.
- I did not search Chinese- or Vietnamese-language venues for these field names.

---

## Q5. Is `source_tuple_id` real? Which KGQA datasets link a question to its generating triple?

### Takeaway

**No published source found for a field literally named `source_tuple_id`.** KGQA
datasets overwhelmingly store the *executable query* (SPARQL / S-expression /
graph query) rather than an opaque triple id; the triple is recoverable by
executing or parsing that query. 2WikiMultihopQA is the notable case that stores
the triples themselves, as `evidences`, but with surface labels and no ids.

### Cited Findings

- A search for `"source_tuple_id" QA dataset` produced no dataset or paper using
  that key — [WebSearch result set, ad-freiburg/large-qa-datasets](https://github.com/ad-freiburg/large-qa-datasets)
- **ComplexWebQuestions** links each question to its seed question and to an
  executable query: `webqsp_ID` (the WebQuestionsSP question it was built from),
  `webqsp_question`, `machine_question` (the templated form), and `sparql` — [datasets-server, drt/complex_web_questions](https://datasets-server.huggingface.co/first-rows?dataset=drt%2Fcomplex_web_questions&config=complex_web_questions&split=train). The Freebase MIDs of the seed
  triple appear *inside* the SPARQL string (`ns:m.03d0l76`), not as a separate id — [datasets-server, drt/complex_web_questions](https://datasets-server.huggingface.co/first-rows?dataset=drt%2Fcomplex_web_questions&config=complex_web_questions&split=train)
- **GrailQA** is the most explicit: each record carries `graph_query` with typed
  `nodes` (`nid, node_type, id, class, friendly_name, question_node, function`)
  and `edges` (`start, end, relation, friendly_name`), alongside `sparql_query`
  and `s_expression` — [datasets-server, Hieuman/grail_qa](https://datasets-server.huggingface.co/first-rows?dataset=Hieuman%2Fgrail_qa&config=default&split=validation). Real row:

```json
{
  "qid": "3202959008000",
  "question": "what is the role of opera designer gig who designed the telephone / the medium?",
  "answer": {"answer_type": ["Entity"], "answer_argument": ["m.0b787yg"], "entity_name": ["Set Designer"]},
  "function": "none",
  "num_node": 3,
  "num_edge": 2,
  "graph_query": {
    "nodes": {
      "nid": [0, 1, 2],
      "node_type": ["class", "class", "entity"],
      "id": ["opera.opera_designer_role", "opera.opera_designer_gig", "m.0pm2fgf"],
      "class": ["opera.opera_designer_role", "opera.opera_designer_gig", "opera.opera_production"],
      "friendly_name": ["Opera Designer Role", "Opera Designer Gig", "The Telephone / The Medium"],
      "question_node": [1, 0, 0]
    },
    "edges": {"start": [...], "end": [...], "relation": [...], "friendly_name": [...]}
  },
  "sparql_query": "...",
  "domains": [...],
  "level": "...",
  "s_expression": "..."
}
```
  The `graph_query.nodes.id` array **is** the per-node KB id list — the real
  equivalent of "which graph elements this question came from".
- **LC-QuAD 2.0** record: `Question ID, Answer Type, Aggregation, OnlyDBO,
  Hybrid, Question, SPARQL Query, Answer, Label`. Real row — [datasets-server, s-nlp/lc_quad2](https://datasets-server.huggingface.co/first-rows?dataset=s-nlp%2Flc_quad2&config=default&split=train):

```json
{
  "Question ID": 19719,
  "Answer Type": "resource",
  "Aggregation": false,
  "OnlyDBO": false,
  "Hybrid": false,
  "Question": "What periodical literature does Delta Air Lines use as a moutpiece?",
  "SPARQL Query": "select distinct ?obj where { wd:Q188920 wdt:P2813 ?obj . ?obj wdt:P31 wd:Q1002697 }",
  "Answer": "http://www.wikidata.org/entity/Q3486420",
  "Label": "Sky"
}
```
  Again the generating triple (`wd:Q188920 wdt:P2813 ?obj`) is embedded in the
  SPARQL, and the answer is a **URI**, with `Label` the surface form.
- **2WikiMultihopQA** is the multi-hop dataset that ships triples directly:
  `"evidences": [["Polish-Russian War", "director", "Xawery Żuławski"], ["Xawery Żuławski", "mother", "Małgorzata Braunek"]]` — surface strings, no Wikidata
  ids at the triple level; Wikidata ids appear only in the separate `entity_ids`
  field for the gold *paragraphs* — [voidful/2WikiMultihopQA dev.json](https://huggingface.co/datasets/voidful/2WikiMultihopQA/resolve/main/dev.json); [Alab-NII/2wikimultihop README](https://raw.githubusercontent.com/Alab-NII/2wikimultihop/main/README.md)

### Inferences

- The published convention is **query-as-provenance**, not **id-as-provenance**.
  A `source_tuple_id` is defensible only if the TKG itself assigns stable tuple
  ids; if so, the closest published analogue is GrailQA's `graph_query.nodes.id`
  plus `edges.relation`, and the field would be better named as a *list*
  (`source_triples` / `graph_query`) because most multi-hop questions come from
  ≥2 tuples — exactly what 2Wiki's plural `evidences` encodes.
- For a Vietnamese legal TKG, the strongest design is 2Wiki's `evidences` (human-
  readable triples, so a reviewer can hand-check) **plus** stable tuple ids (so an
  automatic regrader can re-execute against a rebuilt graph). Neither dataset does
  both; doing both is a genuine, defensible contribution rather than a deviation.

### Gaps

- **WebQSP, KQA Pro, SimpleQuestions, QALD** field names were not retrieved from
  primary sources in this session (HF viewer misses / dataset-not-found). I know
  of their general shapes but will not state field names without a source. Verify
  before citing: WebQSP's `Parses[*].Sparql`, KQA Pro's `program`, SimpleQuestions'
   4-column `subject / relation / object / question` TSV are all **unverified here**.

---

## Q6. Executable provenance (SPARQL / S-expression / logical form)

### Takeaway

GrailQA, LC-QuAD 2.0 and ComplexWebQuestions all ship an executable query beside
the natural-language question, in some cases in multiple syntaxes. That is what
makes a KGQA answer set re-derivable when the underlying KB changes — which is
precisely the failure mode a *temporal* legal benchmark faces.

### Cited Findings

- GrailQA advertises "64,331 questions annotated with both answers and
  corresponding logical forms in different syntax (i.e., SPARQL, S-expression,
  etc.)" — [dki-lab/GrailQA README](https://raw.githubusercontent.com/dki-lab/GrailQA/main/README.md); the record carries `graph_query`, `sparql_query` and
  `s_expression` simultaneously — [datasets-server, Hieuman/grail_qa](https://datasets-server.huggingface.co/first-rows?dataset=Hieuman%2Fgrail_qa&config=default&split=validation)
- The GrailQA paper states "Both graph queries and S-expressions can be easily
  converted into SPARQL queries to get answers" — [GrailQA, arXiv:2011.07743](https://ar5iv.labs.arxiv.org/html/2011.07743)
- LC-QuAD 2.0 stores `SPARQL Query` plus both the answer URI and its `Label`, so a
  regrader can re-execute and re-resolve the label — [datasets-server, s-nlp/lc_quad2](https://datasets-server.huggingface.co/first-rows?dataset=s-nlp%2Flc_quad2&config=default&split=train)
- ComplexWebQuestions stores the full `sparql` with `PREFIX ns: <http://rdf.freebase.com/ns/>` and a three-triple WHERE clause, plus `answers[*].answer_id`
  (the Freebase MID `m.0rh6k`) and `answers[*].aliases` for surface-form-robust
  scoring — [datasets-server, drt/complex_web_questions](https://datasets-server.huggingface.co/first-rows?dataset=drt%2Fcomplex_web_questions&config=complex_web_questions&split=train)
- CRAG addresses the same reproducibility problem *without* a logical form, by
  freezing `query_time` ("Date and time when the query and the web search
  occurred"), `page_last_modified` per retrieved page, and tagging each question
  `static / slow-changing / fast-changing / real-time` — [facebookresearch/CRAG docs/dataset.md](https://raw.githubusercontent.com/facebookresearch/CRAG/main/docs/dataset.md)

### Inferences

- For a temporal legal QA benchmark, CRAG's `query_time` + `static_or_dynamic`
  pair is the single most transferable idea on this list: a question like "which
  provision was in force on date D" has a *fixed* as-of semantics that must be
  recorded, and CRAG's `dynamism` taxonomy gives a published vocabulary for
  saying how volatile the gold answer is.
- Storing an executable query (even a small graph-pattern DSL over the TKG rather
  than full SPARQL) lets you regenerate gold answers after a graph rebuild and
  catch silent gold-answer rot. None of HotpotQA / 2Wiki / MuSiQue / MultiHop-RAG
  can do this; all the KGQA datasets can.

### Gaps

- No source found quantifying regrading benefit (e.g. "X% of gold answers changed
  after KB refresh"). This is an inference about mechanism, not a measured claim.

---

## Q7. Rationale / decomposition fields: `reasoning`, `explanation`, `decomposition`

### Takeaway

Real named conventions are MuSiQue's `question_decomposition` (structured,
human/composition-derived), StrategyQA's `decomposition` + `facts` (human-written
by crowdworkers) and RAGBench's `explanation` fields (explicitly
**model-written**, with the model recorded). A free-text field simply named
`reasoning` is not a convention I could trace.

### Cited Findings

- **MuSiQue** `question_decomposition` is a *list of structured steps*, each with
  `id`, `question`, `answer`, `paragraph_support_idx` — not free text — [datasets-server, dgslibisey/MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation)
- **StrategyQA** stores, per example: question id, source Wikipedia term and its
  description, question, boolean answer, annotator-provided `facts`,
  `decomposition` steps (which may reference earlier steps), and `evidence`
  annotations from **three** workers including Wikipedia paragraph identifiers.
  Steps are marked either as retrieval steps or as **`operation`** steps (logical
  functions over previous answers), and **`no_evidence`** is flagged when
  Wikipedia has no relevant paragraph — [StrategyQA, arXiv:2101.02235](https://ar5iv.labs.arxiv.org/html/2101.02235)
- StrategyQA's canonical illustration: "Did Aristotle use a laptop?" decomposes to
  "(1) When was Aristotle alive? (2) When was the laptop invented? (3) Was
  Aristotle alive when laptops were invented?" — [StrategyQA, arXiv:2101.02235](https://ar5iv.labs.arxiv.org/html/2101.02235)
- StrategyQA human performance was 87% vs ~66% for the best models reported — [StrategyQA, arXiv:2101.02235](https://ar5iv.labs.arxiv.org/html/2101.02235)
- **RAGBench** carries three model-written rationale fields —
  `sentence_support_information[*].explanation`, `overall_supported_explanation`,
  `relevance_explanation` — and, critically, two provenance columns naming the
  models: `generation_model_name` and `annotating_model_name` — [datasets-server, galileo-ai/ragbench](https://datasets-server.huggingface.co/first-rows?dataset=galileo-ai%2Fragbench&config=hotpotqa&split=test)
- **GraphRAG-Bench** stores no rationale; the nearest is `evidence` as a list of
  atomic propositions that together imply the answer — [datasets-server, GraphRAG-Bench/GraphRAG-Bench](https://datasets-server.huggingface.co/first-rows?dataset=GraphRAG-Bench%2FGraphRAG-Bench&config=medical&split=train)
- **ComplexWebQuestions** ships `machine_question` — the templated, ungrammatical
  machine-generated form ("what state is the the education institution has a
  sports team named … in") — *beside* the human-rewritten `question`, making the
  generation provenance auditable — [datasets-server, drt/complex_web_questions](https://datasets-server.huggingface.co/first-rows?dataset=drt%2Fcomplex_web_questions&config=complex_web_questions&split=train)

### Inferences

- The published pattern is: **structure the rationale, don't prose it.** MuSiQue's
  step list and StrategyQA's operation-tagged decomposition are both machine-
  checkable against the support annotations; a free-text `reasoning` blob is not.
- RAGBench is the precedent for shipping model-written rationale as part of a
  benchmark, and it does so only with the annotating model named in every row.
  The documented risk it implicitly guards against is that a model-written
  rationale is an *artifact of a specific model*, so a system built on the same
  model family inherits an unfair advantage and the rationale silently becomes
  part of the label rather than a description of it.
- CWQ's `question`/`machine_question` pair is a cheap, published way to keep an
  LLM-paraphrased Vietnamese question honest: keep the template output next to the
  polished surface form.

### Gaps

- I found **no source** documenting measured failure rates of model-written gold
  rationales (e.g. rationale-answer inconsistency rates). The risk argument above
  is an inference from RAGBench's design, not a cited finding. Do not present it
  as an empirical result.
- The exact nesting of StrategyQA's `evidence` (annotator → step → evidence list)
  is described narratively in the paper but I could not fetch a verbatim JSON
  record; allenai.org/data/strategyqa 302-redirects to a Semantic Scholar page.

---

## Q8. Distractors and train/dev/test splitting; do they show up as schema fields?

### Takeaway

Distractor status is almost always a schema field: HotpotQA/2Wiki ship distractor
paragraphs inline and mark gold via `supporting_facts`; MuSiQue marks it directly
as `is_supporting: false`. Split membership is usually a *file*, with CRAG the
exception that puts it in the record as `split`. GrailQA is the one dataset whose
`level` field is explicitly a leakage-control construct.

### Cited Findings

- **MuSiQue** carries a per-paragraph boolean `is_supporting`; in the retrieved
  validation row, the gold paragraph `idx: 5` ("Miquette Giraudy") has
  `"is_supporting": true` while paragraphs `idx: 0–4` are distractors with
  `"is_supporting": false` — [datasets-server, dgslibisey/MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation)
- MuSiQue also has a top-level `answerable: bool`, and ships two dataset variants
  (`musique_ans_v1.0_*` and `musique_full_v1.0_*`) — the "full" set being the one
  containing unanswerable contrastive items — [StonyBrookNLP/musique](https://github.com/StonyBrookNLP/musique)
- **2WikiMultihopQA**'s retrieved `context` contains 8+ paragraphs of which only 2
  appear in `supporting_facts` — the rest are topically-similar distractors
  ("Snow White and the Three Stooges", "A Snow White Christmas", …) — [voidful/2WikiMultihopQA dev.json](https://huggingface.co/datasets/voidful/2WikiMultihopQA/resolve/main/dev.json)
- **CRAG** puts split membership in the record: `split` (integer), "where 0 is for
  validation and 1 is for the public test" — [facebookresearch/CRAG docs/dataset.md](https://raw.githubusercontent.com/facebookresearch/CRAG/main/docs/dataset.md)
- CRAG also explicitly balances a leakage-adjacent axis in-schema: `popularity`
  ∈ {head, torso, tail}, "created a roughly equal number of questions for each
  bucket" — [facebookresearch/CRAG docs/dataset.md](https://raw.githubusercontent.com/facebookresearch/CRAG/main/docs/dataset.md)
- **GrailQA** engineers the split to prevent memorization: "For the validation and
  test sets, 50% of the questions are from held-out domains not covered in
  training (zero-shot), 25% of the questions correspond to canonical logical forms
  not covered in training (compositional), and the rest 25% are randomly sampled
  from training (i.i.d.)" — [GrailQA, arXiv:2011.07743](https://ar5iv.labs.arxiv.org/html/2011.07743). The per-record `level` and
  `domains` fields record which bucket the item falls in — [datasets-server, Hieuman/grail_qa](https://datasets-server.huggingface.co/first-rows?dataset=Hieuman%2Fgrail_qa&config=default&split=validation)
- **RAGBench** records `dataset_name` per row, so the multi-source benchmark can be
  sliced and de-duplicated by provenance — [datasets-server, galileo-ai/ragbench](https://datasets-server.huggingface.co/first-rows?dataset=galileo-ai%2Fragbench&config=hotpotqa&split=test)
- **QAngaroo/WikiHop** ships `supports` with no gold marking at all, so distractor
  vs gold is not recoverable from the schema — [datasets-server, community-datasets/qangaroo](https://datasets-server.huggingface.co/first-rows?dataset=community-datasets%2Fqangaroo&config=wikihop&split=train)

### Inferences

- For a TKG-generated Vietnamese legal benchmark, the highest-value borrowing here
  is GrailQA's generalization split applied to *legal domains and amendment
  patterns*: hold out whole văn bản/lĩnh vực for a zero-shot slice, hold out
  unseen temporal-query templates for a compositional slice, and record the bucket
  in a `level`-style field — noting that this makes `level` mean generalization,
  not hop count, so hops need their own field or id prefix.
- The near-universal pattern is that *distractor status is a field on the context
  item*, never a separate top-level list. `is_supporting` (MuSiQue) is the
  cleanest published spelling and generalizes to graph tuples as well as text.

### Gaps

- I did not find documentation of explicit contamination/leakage checks (e.g.
  n-gram overlap between splits) for any of these datasets in the material
  retrieved. Not claimed either way.

---

## Cross-cutting verdict on the consumer's proposed field list

| Proposed field | Traceable to a published dataset? | Closest real convention |
|---|---|---|
| `id` | **Yes**, universal | HotpotQA `id`, 2Wiki `_id`, MuSiQue `id` (`2hop__…`), CRAG `interaction_id` — [hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa); [2wikimultihop](https://raw.githubusercontent.com/Alab-NII/2wikimultihop/main/README.md); [MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation); [CRAG](https://raw.githubusercontent.com/facebookresearch/CRAG/main/docs/dataset.md) |
| `question` | **Yes**, universal (RAG-era datasets use `query`) | HotpotQA `question`; MultiHop-RAG/CRAG `query`; Ragas `user_input` |
| `answer` | **Yes**, universal | + CRAG `alt_ans`, CWQ `answers[*].aliases` for alias-tolerant scoring |
| `hop_level` | **No published source found** | HotpotQA `level` (difficulty, *not* hops); 2Wiki/HotpotQA `type`; CRAG `question_type` incl. `multi-hop`; MuSiQue hop count in the `id` prefix; GrailQA `level` (generalization) |
| `evidence` | **Yes** — GraphRAG-Bench uses exactly `evidence` (list of propositions) + `evidence_relations`; 2Wiki uses plural `evidences` (triples); StrategyQA uses `evidence` (annotator-nested paragraph ids) — [GraphRAG-Bench](https://datasets-server.huggingface.co/first-rows?dataset=GraphRAG-Bench%2FGraphRAG-Bench&config=medical&split=train); [2wikimultihop](https://raw.githubusercontent.com/Alab-NII/2wikimultihop/main/README.md); [StrategyQA](https://ar5iv.labs.arxiv.org/html/2101.02235) | Beware: the same name means three different things in three datasets. Say which. |
| `reasoning` | **Not as a field name.** | MuSiQue `question_decomposition` (structured); StrategyQA `decomposition` + `facts` (human); RAGBench `*_explanation` (model-written, with `annotating_model_name`) |
| `used_context_ids` | **No published source found** | RAGBench `all_utilized_sentence_keys` / `supporting_sentence_keys` (and `all_relevant_sentence_keys` for the relevant-vs-used distinction); MuSiQue `paragraph_support_idx`; HotpotQA `supporting_facts` `[title, sent_id]` |
| `source_tuple_id` | **No published source found** | 2Wiki `evidences` (triples as surface strings); GrailQA `graph_query.nodes.id` + `edges.relation`; LC-QuAD `SPARQL Query`; CWQ `sparql` + `webqsp_ID` |
| `context_block` | **No published source found** | HotpotQA/2Wiki `context` (`[title, sentences]`); RAGBench `documents`; Ragas `reference_contexts` |

Four of the nine names (`hop_level`, `reasoning`, `used_context_ids`,
`source_tuple_id`, `context_block` — five counting `reasoning`) have no traceable
published origin. They read as a coherent in-house design rather than a citation;
none should be attributed to a paper in a thesis without a source.
