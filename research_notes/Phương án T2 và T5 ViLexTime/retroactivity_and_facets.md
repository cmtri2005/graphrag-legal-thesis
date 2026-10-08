# Retroactivity as an Evaluated Phenomenon, and the Precedent for Facets-vs-Groups

Scope note: searched 2026-10-07. Prioritised 2020–2026. Legal-informatics standards
are older and that is flagged inline. Every claim carries an inline source; where a
search-engine snippet could not be confirmed against the paper body, that is said
explicitly rather than smoothed over.

Convention used throughout: **[DOC]** = stated in the paper/spec itself;
**[INF]** = my inference from the cited material.

---

## Q1. Do any temporal QA / temporal RAG / legal NLP benchmarks explicitly model publication date vs effective date, retroactivity, commencement, transitional provisions, or "signed but not yet in force"?

### Takeaway

General-purpose temporal QA (TimeQA, SituatedQA, StreamingQA, RealTimeQA, TempLAMA,
ArchivalQA, ChroniclingAmericaQA, FreshQA, ComplexTempQA) models **document time vs
event time** but has no concept of an effective date distinct from publication, and
the field's 2025–2026 survey does not mention retroactivity or commencement at all.
A 2026 wave of legal-temporal benchmarks (LexKairos, the French-tax temporal-misgrounding
benchmark, TimelyQABench, the statutory-QA failure-mode paper, the Chinese
applicable-law paper) **does** model effective-date semantics and version-in-force
resolution — but **none of them makes retroactivity (effective date earlier than
signing) its own evaluated group**. Retroactivity appears only as a motivating
sentence, an appendix note, or a per-document metadata clause.

### Cited Findings — general temporal QA: effective dates absent

- The 2025–2026 survey "It's High Time: A Survey of Temporal Question Answering"
  catalogs 30+ datasets (NewsQA 2017; TORQUE 2020; TimeQA 2021, 41.2k questions
  spanning 1367–2018; ArchivalQA 2022, 532k questions 1987–2007;
  ChroniclingAmericaQA 2024, 485k questions 1800–1920; RealTimeQA 2023, 5.1k
  questions 2020–2024; ComplexTempQA 2025, 100.2M questions 1987–2023; TEMPO 2026,
  1.7k questions). It organises temporality as corpus temporality (diachronic vs
  synchronic), question temporality (explicit vs implicit intent; temporal
  orientation), and model capabilities — plus knowledge source, temporal orientation,
  question type, reasoning complexity — [Source](https://arxiv.org/html/2505.20243v4)
- **[DOC] Negative finding, explicit:** the same survey discusses "document creation
  time" and "event time" but treats them as aligned temporal anchors and does **not**
  address retroactive effects; retroactive application of rules, commencement dates,
  and backdated validity **do not appear in the document at all**. Legal-domain
  coverage is confined to a brief appendix subsection with no substantive analysis —
  [Source](https://arxiv.org/html/2505.20243v4)
- SituatedQA (2021) is 2,795 queries spanning 1700–2021, built by manually annotating
  temporally and geographically dependent questions; StreamingQA (2022) is 410k
  questions asked on a given date, answered from 14 years of time-stamped WMT news —
  i.e. the temporal axis is the *article's* timestamp —
  [Source](https://proceedings.mlr.press/v162/liska22a/liska22a.pdf);
  [Source](https://arxiv.org/pdf/2505.20243)
- PAT-Questions (ACL Findings 2024) is a self-updating present-anchored temporal QA
  benchmark — the temporal problem framed is answer *staleness*, not validity intervals
  — [Source](https://aclanthology.org/2024.findings-acl.777.pdf)

### Cited Findings — classic legal NLP benchmarks: no validity model

- LegalBench is 162 tasks over six types of U.S. legal reasoning, "predominantly
  without temporal indexing." Its only effective-date-adjacent task is
  `cuad_effective_date` — a *contract clause-detection* task ("Does the clause specify
  the date upon which the agreement becomes effective?"), not a point-in-time
  reasoning task — [Source](https://arxiv.org/pdf/2308.11462);
  [Source](https://proceedings.neurips.cc/paper_files/paper/2023/file/89e44582fd28ddfea1ea4dcb0ebbf4b0-Paper-Datasets_and_Benchmarks.pdf)
- LexGLUE covers seven English legal datasets (US Supreme Court, ECtHR, US/EU law
  corpora); LeXFiles is a multinational English legal pre-training corpus from six
  legal systems. Neither is organised around validity intervals —
  [Source](https://arxiv.org/pdf/2503.04305)
- **[INF]** CaseHOLD, SCALE and BSARD were not found to model effective dates in any
  source retrieved; see Gaps — I did not individually verify their
  dataset-construction sections.

### Cited Findings — the 2026 legal-temporal wave: effective dates yes, retroactivity no

- **LexKairos (2026)** — "Legal Time at the normative level concerns temporal
  attributes of statutes, including promulgation dates, effective periods,
  retroactivity, and procedural deadlines." Three dimensions / nine sub-tasks:
  Statutory Lifecycle Tracking (1,417 instances), Case Chronology Analysis (2,094),
  Procedural Time Limit Reasoning (289). Lifecycle sub-tasks are 1-1 Effective Date
  Inquiry, 1-2 Effective Version Identification, 1-3 Effective Status Verification
  ("whether that version was in force at the specified time") —
  [Source](https://arxiv.org/html/2608.09106); sub-task names also confirmed at
  [Source](https://arxiv.org/pdf/2608.09106)
- **[DOC] LexKairos names retroactivity in its framing but does not benchmark it:**
  retroactivity is "acknowledged but not systematically benchmarked" and is not a
  standalone capability dimension; the task design operationalises the promulgation/
  effective distinction only through effective-date queries, with no separate
  promulgation-tracking task — [Source](https://arxiv.org/html/2608.09106)
- **Temporal Misgrounding in Legal RAG (French tax law, 2026)** — uses the official
  Légifrance PISTE `date_debut` / `date_fin` validity fields; corpus of 32,436
  article-versions over 1938–2031; 221 curated questions (209 scored) over 33 CGI
  articles in four regimes R1–R4; 69,208 version-aware jurisprudence links;
  deterministic nugget scoring, never LLM-as-judge —
  [Source](https://arxiv.org/html/2608.09393)
- **[DOC]** That benchmark marks future-effective versions with Légifrance's
  `VIGUEUR_DIFF` status and extends the corpus to 2031 to hold them — but the scored
  R3 track uses single-date-anchor questions only, and the authors state that
  "future-law leakage" and "wrong-amendment resolution" **remain unexercised in the
  scored benchmark, reserved for future work** —
  [Source](https://arxiv.org/html/2608.09393)
- **Asking For An Old Friend (statutory QA, 2026)** — 312 expert-validated QA pairs
  from 697 generated (55% acceptance), in three categories: Post-Cutoff Amendment
  Questions (115 pairs), Pre-Amendment Questions (113), Multi-Provision Pre-Amendment
  Questions (84). Generation by Gemini 3 Pro Preview, validated by two senior law
  students and one qualified lawyer. **[DOC]** The paper does **not** discuss
  retroactive application or provisions effective before publication; retroactivity is
  not a category — [Source](https://arxiv.org/html/2605.23497)
- **When Do LLMs Apply the Wrong Law? (2026)** — 26,000 Chinese civil judgments split
  50/50 pre-Code / post-Code (2021 Civil Code); 200 sampled cases per trial. States
  the non-retroactivity principle as foundational: "newly enacted law generally applies
  only to facts and legal relationships arising after its entry into force, not to
  those already completed under prior law." **[DOC]** But retroactive laws are **not**
  a benchmark category — "retroactive application of newly introduced provisions"
  appears only in the appendix as a recognised judicial exception, and
  "signed but not yet in force" receives minimal attention and is not isolated as a
  test condition — [Source](https://arxiv.org/html/2608.14610)
- **TimelyQABench / TimelyRAG (2026)** — 12,000 Korean time-critical QA instances
  (3,000 each for legal, university, company, terms-of-service) over six temporal
  reasoning categories; per-item temporal fields Query Insert Time (QIT), Query Event
  Times (QET), Document Insert Time (DIT), Document Event Times (DET); ~3.1 supporting
  documents per query. **[DOC] Crucially for option (c):** documents carry "issuance
  dates, amendment dates, effective periods, or **retroactive applicability clauses**"
  as *document content/metadata*, while the *categories* are reasoning types — one of
  which is "Legacy Exception Rules" ("rules allowing certain entities to follow older
  rules despite newer versions", e.g. "students enrolled before 2021 follow the old
  graduation rules") — [Source](https://arxiv.org/html/2609.11572)
- **LeKUBE (CIKM/arXiv 2024)** — legal knowledge *update* benchmark: 180 updated
  statutes (~114 Chinese characters pre-update, ~124 post-update), synthetic
  amendments to the Chinese Criminal and Civil Codes written by law-school annotators,
  evaluated across five dimensions. The temporal model is "before update / after
  update", not a validity calendar — [Source](https://arxiv.org/html/2407.14192v2)
- **LawShift (NeurIPS 2025)** — first benchmark aimed at statutory amendments, built on
  the historical evolution of the Chinese Criminal Code; metamorphic testing with a
  Law Article Template plus Amendment Dimensions; 31 fine-grained revision types drawn
  only from revisions empirically observed across all 12 historical editions of the
  Criminal Code Amendments —
  [Source](https://neurips.cc/virtual/2025/poster/121832);
  [Source](https://openreview.net/forum?id=5SpFenlxDF)
- **CALRK-Bench (Korean, 2026)** and **TW-LegalBench (Taiwanese, 2026)** surfaced
  repeatedly in legal-temporal searches but I did not verify their effective-date
  handling — [Source](https://arxiv.org/html/2603.26332);
  [Source](https://arxiv.org/html/2606.18699)
- **Version- and Scope-Aware QA over Normative Documents (2026)** — a deployed system
  paper that separates **version-awareness** ("whether a clause belongs to the
  currently effective version of a document rather than a superseded, expired, or
  repealed version") from **scope-awareness** ("whether the document applies to the
  jurisdiction, applicant category, and time period asked about") —
  [Source](https://arxiv.org/html/2609.18769)

### Inferences

- **[INF] The author's T5 group appears to be novel as an *evaluated group*.** Across
  the 2026 legal-temporal benchmarks that do model effective dates, retroactivity is
  consistently mentioned in the framing and then dropped from the task design
  (LexKairos explicitly; the Chinese applicable-law paper explicitly; the statutory-QA
  paper silently). I found no benchmark with a retroactivity group, a retroactivity
  task, or a retroactivity-specific metric.
- **[INF] The repeated pattern of "named in motivation, absent from tasks" is itself
  evidence for option (c).** Four independent 2026 teams with versioned corpora in hand
  all declined to build a retroactivity group. Two plausible readings: the phenomenon
  is too rare in their corpora to support one (the author's own 21-chain ceiling is the
  same constraint), or those teams judged it a property of items rather than a capability.
  TimelyQABench's treatment — retroactive applicability as a *document clause* while
  categories stay reasoning-shaped — is the closest thing to a deliberate choice on record.
- **[INF] Novelty is defensible but should be claimed narrowly:** "first to evaluate
  retroactive commencement as a distinct phenomenon in a point-in-time legal QA
  benchmark", not "first to notice retroactivity" — LexKairos and de Martim (2026) both
  name it in print before the author's work.

### Gaps

- Could not individually verify effective-date handling in CaseHOLD, SCALE, BSARD,
  TempQuestions, TempLAMA, TAQA, FreshQA or CRAG dataset-construction sections. The
  survey-level negative finding covers the general temporal QA family, but these
  specific papers were not opened.
- "German statutory QA", "FiscalQA", "HoH" and "LexKairos'/CALRK-Bench's" full task
  tables were not retrieved. A dedicated search for HoH returned nothing relevant.
- LawShift's own paper body was not readable (OpenReview served a browser-verification
  page instead of the PDF); its Amendment Dimensions details below come from NeurIPS
  and mlanthology metadata plus search snippets, not from the paper text.

---

## Q2. Is the "signed but not yet in force" trap described in the temporal RAG / knowledge-conflict literature? Does it have names?

### Takeaway

Yes — and the literature has given it several names. The dominant failure direction
studied is the *mirror* case (retrieving the newest when an older version governs),
named **current-law substitution**, **recency bias**, and **newest-law bias**. The
author's exact option-(b) trap — a not-yet-in-force document outranking the governing
older one — is named **future-law leakage** and is explicitly flagged as **not yet
exercised by any scored benchmark**. That makes option (b) a documented open gap, not
a solved problem.

### Cited Findings — named phenomena

- **Temporal misgrounding** — "the systematic retrieval and citation of the currently
  in-force version of a legal article when the applicable version is an earlier or
  future one." Four named sub-modes: **current-law substitution** (dominant),
  **future-law leakage**, **wrong-amendment resolution**, **multi-version confusion**.
  Root causes given: parametric recency bias, absent date-conditioning in retrieval,
  and **article-number aliasing** (identical identifiers across versions) —
  [Source](https://arxiv.org/html/2608.09393)
- **[DOC] Definition of future-law leakage:** "a not-yet-in-force version is returned
  for a present-tense question" — [Source](https://arxiv.org/html/2608.09393)
- **[DOC] It is an acknowledged open gap:** the French-tax authors state future-law
  leakage and wrong-amendment resolution "remain unexercised in the scored benchmark,
  reserved for future work" — [Source](https://arxiv.org/html/2608.09393)
- **Post-cutoff staleness** vs **recency bias** — the statutory-QA paper's two failure
  modes: staleness is "models apply superseded rules after legislative amendments";
  recency bias is models "prefer newer provisions even when a historical version
  governs the fact pattern," despite having the outdated text available —
  [Source](https://arxiv.org/html/2605.23497)
- **Newest-law bias** with measured directional asymmetry: models score 0.70–0.84 on
  new-version cases but **below 0.25** on old-version cases, i.e. they
  "preferentially apply the newest version regardless of when the legally relevant
  facts occurred" — [Source](https://arxiv.org/html/2608.14610)
- **Diachronic naivety** — semantically similar provisions from different temporal
  states get conflated, so "superseded and currently valid norms appear
  interchangeable" (de Martim 2026) —
  [Source](https://arxiv.org/html/2606.09724)
- Severity baseline for how badly undated retrieval fails: static RAG retrieved the
  date-applicable version **0% of the time**, and the benchmark deliberately screens
  for cases where the current text *lacks* the correct historical value (208 of 209
  scored questions) — [Source](https://arxiv.org/html/2608.09393)
- Generic knowledge-conflict framing: RAG introduces "knowledge conflict," where
  injected context contradicts training-time facts (outdated information or
  adversarial fakes); inter-document conflicts are typed as factual, temporal and
  opinion, and **temporal conflicts are conventionally resolved by ranking documents by
  recency** — [Source](https://arxiv.org/pdf/2506.07270);
  [Source](https://arxiv.org/html/2605.17301v1)
- Related 2026 work on evolving standards in law: "Sycophants in the Courtroom: Are
  LLMs Fragile to Juridical Authority and Evolving Legal Standards?" —
  [Source](https://arxiv.org/pdf/2608.21409)

### Inferences

- **[INF] Option (b) has a ready-made name and a citable gap.** The author can call the
  group **future-law leakage** (de Martim-adjacent: **vacatio legis** items), cite the
  French-tax paper for the name *and* for the admission that no scored benchmark
  exercises it, and claim first scored coverage. That is a cleaner novelty claim than
  T5's, because the gap is stated by someone else in print.
- **[INF] The standard RAG remedy actively causes the option-(b) failure.** If the
  conventional fix for temporal conflict is "rank by recency"
  ([Source](https://arxiv.org/html/2605.17301v1)), then a corpus of 3,856 signed-but-
  not-yet-effective transitions is adversarial against the field's default heuristic by
  construction — every retrieval signal, including the recency prior, points at the
  wrong document. This is a stronger diagnostic argument than T5 can make.
- **[INF]** The measured 0.70–0.84 vs <0.25 asymmetry
  ([Source](https://arxiv.org/html/2608.14610)) predicts that option-(b) items will be
  *discriminative* — models should fail them at high rates — which is what a diagnostic
  group needs.

### Gaps

- No paper found that *scores* a "signed but not yet in force" group, so there is no
  prior item-construction recipe to copy for option (b); the author would be defining it.
- I did not find a term for the specific sub-case where the not-yet-effective
  instrument is also the *highest-ranked by lexical/semantic similarity*. "Future-law
  leakage" covers the outcome, not the retrieval mechanism.

---

## Q3. Has point-in-time / "as-at" versioning been formalised in legal informatics outside NLP? Do the standards represent commencement, retrospective commencement, and effective-vs-publication dates explicitly?

### Takeaway

Yes, unambiguously, and this is the strongest evidence base in these notes. Akoma Ntoso
(OASIS LegalDocML, first drafted 2006, OASIS standard 29 Aug 2018) carries **two
independent date pairs per fragment** — validity/in-force and efficacy — precisely so
that efficacy can diverge from entry into force. The ELI ontology and the
Palmirani–Brighi legal time model make the same split, and 2025–2026 work states
outright that the two diverge **under vacatio legis and under retroactive (ex tunc)
effect**. The distinction the author's T5 group encodes is a first-class, named
construct in the standards even though NLP has not evaluated it.

### Cited Findings — Akoma Ntoso / LegalDocML

- Akoma Ntoso is an XML vocabulary for legal documents aligned with the FRBR WEMI
  model; "the temporal model of laws is particularly important in Akoma Ntoso, which
  provides a simple and rigorous approach that fully tracks and describes the temporal
  evolution and timed events affecting a legal text." It is designed to enable access
  to **point-in-time consolidation of amended acts**. First drafted 2006 for the Cape
  Town conference organised by UNDESA; first official OASIS standard approved
  **29 Aug 2018** — [Source](https://en.wikipedia.org/wiki/Akoma_Ntoso);
  [Source](https://www.oasis-open.org/standard/akn-v1-0/);
  [Source](https://publicadministration.un.org/Parliaments/Portals/0/conferences/capetown2006/04%20Fabio%20Vitali%20-%20Introduction%20to%20Akoma%20Ntoso.pdf)
- **[DOC] The five-attribute mechanism:** in `multipleVersions` documents, each element
  and text fragment may be associated with an enactment specification through five
  attributes: **`@start`, `@end`** (validity / enactment), **`@startEfficacy`,
  `@endEfficacy`** (efficacy), and **`@status`**. `@start`/`@end` and
  `@startEfficacy`/`@endEfficacy` each hold a reference to the **ID of the event** that
  began or ended the enactment (or the efficacy) of the fragment —
  [Source](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0-part1-vocabulary.html);
  [Source](https://cris.unibo.it/retrieve/handle/11585/710681/517270/balisageVol24-2019.pdf)
- Supporting elements: `lifecycle` (required for `singleVersion` and `multipleVersions`
  documents), `eventRef` (references to amendment documents), `temporalData` (lists
  dates of lifecycle events), `temporalGroup` and `timeInterval`, plus `efficacyMod` /
  `forceMod` modification elements. Lifecycle event types mentioned include
  **generation, amendment, repeal, `entryIntoEfficacy`, `entryIntoForce`** —
  [Source](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0-part1-vocabulary.html);
  [Source](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/csprd01/part2-specs/akn-core-v1.0-csprd01-part2-specs.html)
- Monica Palmirani is an editor of Akoma Ntoso v1.0; the Palmirani–Brighi legal time
  model distinguishes text as it existed on a specific date, and creation of new
  **Temporal Versions (TV)** of amended norms is the key transformative effect modelled
  — [Source](https://dl.acm.org/doi/pdf/10.1145/3820755.3833405);
  [Source](https://link.springer.com/chapter/10.1007/978-94-007-1887-6_6)
- **[DOC] Caveat on how firmly retroactivity is stated in the spec itself:** the AKN
  spec separates legal existence (`@start`/`@end`) from when provisions apply
  (`@startEfficacy`/`@endEfficacy`), which accommodates retroactive efficacy or delayed
  application; the spec does not *prohibit* efficacy before entry into force. My read of
  the retrieved spec text is that retroactivity is **enabled by independent date
  references rather than named as a prohibited-or-blessed case** in the passages I saw
  — [Source](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0-part1-vocabulary.html)

### Cited Findings — the explicit retroactivity / vacatio legis statements

- **[DOC] The clearest formal statement found**, from the LRMoo diachronic-norms paper
  (2025/2026): "following the ELI ontology and the legal time model of Palmirani and
  Brighi, we distinguish the date a norm enters the legal order from its
  applicability — the temporal scope of the facts it may govern — **because the two
  diverge under vacatio legis (deferred onset), retroactive (ex tunc) effect, and
  tax-anteriority or lex mitior rules**" — [Source](https://arxiv.org/html/2506.07853)
- Worked example in the same paper: "A tax statute, for instance, may be published and
  in force in October yet only applicable to taxable events from the following January;
  conversely, a more lenient criminal law (lex mitior) applies retroactively to facts
  predating its enactment" — [Source](https://arxiv.org/html/2506.07853)
- Bitemporality is stated as a strict requirement: "The temporal dimension of legal
  knowledge is bitemporal in the strict technical sense: it requires distinguishing
  **valid time** — when a norm produces legal effect — from **transaction time** — when
  the norm was recorded in the official system." The model treats each temporal state of
  a norm and of each of its components as a distinct versioned entity, and every
  amendment as a formal creation event that ends one version and starts the next —
  [Source](https://arxiv.org/html/2506.07853)
- de Martim (Federal Senate of Brazil, 2026): "Each norm has a lifecycle bounded by
  formal events: enactment, publication, **vacatio legis (a deferral period between
  publication and legal effect)**, the validity interval itself, and termination"; and
  "legal informatics standards … represent **date of entry into force** and **date of
  applicability** as distinct properties, since a norm may enter the legal order on one
  date while producing its effects on another, as in vacatio legis, deferred
  effectiveness, or retroactive application" — [Source](https://arxiv.org/html/2606.09724)
- *Vacatio legis* is the standing technical term for "the period between the
  announcement of a legislation and its entering into force" —
  [Source](https://en.wikipedia.org/wiki/Vacatio_legis)
- Drafting-office / publisher practice: a point-in-time version "sets out the law at a
  particular point in time," letting users access the law in force today and as it
  appeared at a past date; official portals render this as "point in time view as at
  01/04/2000." Commercial and official point-in-time services advertise reconstructing
  legislation "as it existed at any date in the past, present **or future**" —
  [Source](https://www.legislation.gov.au/help-and-resources/understanding-legislation/glossary);
  [Source](https://www.legislation.gov.uk/ukpga/1980/43/schedule/7/crossheading/powers-of-criminal-courts-act-1973-c-62/2000-04-01);
  [Source](https://www.thomsonreuters.com.au/en-au/products/timebase/point-in-time.html)
- National implementations expose the two dates as API fields: the French Légifrance
  PISTE API supplies `date_debut` / `date_fin` per article version and a
  **`VIGUEUR_DIFF`** status for future-effective versions —
  [Source](https://arxiv.org/html/2608.09393)

### Inferences

- **[INF] The author can make a strong two-part claim:** the publication/effective split
  is a *standardised* construct (AKN `@start` vs `@startEfficacy`; ELI entry-into-force
  vs applicability; `VIGUEUR_DIFF` in a production government API) that NLP evaluation
  has not operationalised. That asymmetry — mature in legal informatics, absent from NLP
  benchmarks — is the cleanest framing for the contribution, and it holds for *both*
  option (a) and option (b).
- **[INF] The standards also license option (c).** AKN records the retroactive case as
  *two attributes on the fragment*, not as a separate document class. If the field's own
  data model represents retroactivity as per-item fields, recording it as a per-item
  field in a benchmark is a faithful mirror of the authority, not a demotion.
- **[INF] Vietnamese Article 152 maps onto the AKN/ELI vocabulary directly** — effective
  date earlier than signing is `@startEfficacy` < publication event — so the author can
  cite a standard rather than invent terminology. (Vietnamese-law specifics not
  researched, per the assignment.)

### Gaps

- The AKN Part 1 vocabulary page is ~246k characters and WebFetch read only the first
  100k; I did not reach the per-element reference entries for `efficacyMod`, `forceMod`
  or the enumerated `lifecycle` event-type list. The `@startEfficacy` semantics are
  confirmed from two sources, but an exhaustive event-type enumeration is unverified.
- LegalRuleML's handling of temporal validity was not researched (searches surfaced
  Akoma Ntoso and LRMoo instead). JURIX/ICAIL/AI&Law proceedings were not searched
  directly; the legal-informatics evidence here comes from the OASIS specs, the
  Palmirani Springer chapter, the Balisage paper, the 20-years-of-AKN ACM paper and the
  LRMoo arXiv paper.
- One attribution I could **not** confirm: a search snippet produced a longer
  enumeration — "vacatio legis … retroactive provisions … delayed or conditional
  effectiveness … **corrigenda or republications**, where the official record changes
  without necessarily changing the valid-time state" — together with the claim that
  "current retrieval-oriented benchmarks assume the underlying corpus is normatively
  stable and do not assess whether retrieved provisions remain in force or have been
  superseded, amended, or repealed." When I fetched de Martim (2606.09724) directly, the
  first 100k characters contained closely related wording on vacatio legis and on
  corrigenda vs transaction time, but **not** that benchmark-stability sentence. **Do not
  quote the benchmark-stability sentence without locating it first** — it may sit in the
  unread portion of that paper, or in 2609.18769 / 2608.09106, which were in the same
  result set.

---

## Q4. Precedent for OPTION (c): when is a phenomenon better a per-item attribute to slice on than a separate group with a quota?

### Takeaway

The methodological precedent is strong and runs in option (c)'s favour when a group
cannot reach a usable size. NLP evaluation has a standing distinction between *tasks/
scenarios* (what is measured) and *slices/subpopulations/facets* (how results are cut),
institutionalised by Robustness Gym, CheckList's capability × test-type matrix, and
HELM's scenario × metric grid. The statistical literature — Card et al.'s GLUE power
analysis, BenchScope, and a 2026 LREC power toolkit — says small subsets lack the
resolution to support claims and that excessive fragmentation adds noise, not signal.
At 21 chains, T5 is below any plausible resolution threshold.

### Cited Findings — the facets-vs-tasks architecture

- **Robustness Gym (NAACL 2021 demo)** unifies four evaluation paradigms —
  **subpopulations, transformations, evaluation sets, and adversarial attacks**. Slices
  "can be constructed as evaluation sets from pre-existing datasets **or as
  subpopulations by filtering a larger dataset**"; subpopulations let you "evaluate model
  performance on specific subgroups **rather than treating evaluation as separate
  tasks**" — [Source](https://arxiv.org/abs/2101.04840);
  [Source](https://aclanthology.org/2021.naacl-demos.6/);
  [Source](https://robustnessgym.readthedocs.io/en/latest/getting-started/nutshell.html)
- **CheckList (ACL 2020)** is explicitly a *matrix*: linguistic **capabilities as rows**
  × **test types as columns** (MFT = minimum functionality test, INV = invariance test,
  DIR = directional expectation test). Capabilities include Vocabulary+POS, Taxonomy,
  Robustness, NER, Fairness, **Temporal**, Negation, Coreference, SRL, Logic. The
  phenomenon ("Temporal") is a row in a matrix, not a standalone benchmark —
  [Source](https://aclanthology.org/2020.acl-main.442/);
  [Source](https://arxiv.org/pdf/2005.04118)
- **HELM (2022)** has two levels: "(i) an **abstract taxonomy of scenarios and metrics**
  to define the design space … and (ii) a concrete set of implemented scenarios and
  metrics selected to prioritize **coverage, value, and feasibility** (e.g. limited
  engineering resources)." Scenarios are triples of (task, domain, language); 7 metrics
  are measured for **each** of 16 core scenarios, plus 7 targeted evaluations over 26
  targeted scenarios — [Source](https://arxiv.org/html/2211.09110.pdf);
  [Source](https://nlp.stanford.edu/helm/instruction-pilot/)
- **Designing Benchmarks for Knowledge Work (2026)** proposes a work-centred
  representation for benchmark design and reporting with four parts: represented
  activity, tested setting, required work product, evaluated result — i.e. *fields* per
  item. It also notes "benchmark-level coverage would require a **stratified task sample
  within each suite** and independent field assignment by a second coder," and that
  "when a benchmark is highly heterogeneous, aggregate claims become less informative,
  and **reporting diagnostics alongside mean scores** makes these patterns visible" —
  [Source](https://arxiv.org/html/2605.23262v2)
- Task-stratified analysis is a recognised methodology class: dissecting an evaluation
  "into strata defined by **task, task attribute, or contextual subpopulation**" to
  surface heterogeneity that aggregates hide —
  [Source](https://www.emergentmind.com/topics/task-stratified-analysis)
- **LawShift** is the candidate in-domain precedent: it keeps a **Law Article Template**
  (the components of an article that may change) separate from **Amendment Dimensions**
  (all the ways those components can change), yielding **31 fine-grained revision types**
  applied metamorphically to items, rather than 31 separate task groups —
  [Source](https://neurips.cc/virtual/2025/poster/121832);
  [Source](https://mlanthology.org/neurips/2025/han2025neurips-lawshift/)
- **TimelyQABench** does the same split in the temporal-legal setting: effective periods
  and **retroactive applicability clauses** live on documents, while the six evaluated
  categories are reasoning patterns (e.g. Legacy Exception Rules); per-item temporal
  fields are QIT/QET/DIT/DET — [Source](https://arxiv.org/html/2609.11572)

### Cited Findings — the statistical cost of fragmenting into small groups

- **Card et al. (2020), "With Little Power Comes Great Responsibility":** a power
  analysis of GLUE found that **many test sets lacked the resolution needed to
  distinguish the small state-of-the-art improvements researchers reported** —
  [Source](https://aclanthology.org/2026.lrec-1.353.pdf)
- **BenchScope (2026)** argues benchmarks should be judged by how many **independent
  signals** they provide rather than raw task count, and finds that **excessive
  fragmentation adds noise rather than signal** — small subsets suffer high small-sample
  variance, weak correlations between tiny subsets, and statistical noise overwhelming
  true differences; "fewer, larger groups provide more reliable measurements" than many
  fine-grained splits. Its recommendation is to **report sliced attributes as dimensions
  rather than creating separate subsets**, which preserves full-dataset information and
  avoids small-sample unreliability. It gives no absolute minimum, but indicates roughly
  **20–50 samples** as the floor below which noise is extreme, varying by benchmark —
  [Source](https://arxiv.org/pdf/2603.29357)
- A 2026 LREC power toolkit reports that smaller datasets (e.g. IFEval) "exhibit lower
  power on average, making it harder to detect meaningful differences" —
  [Source](https://aclanthology.org/2026.lrec-1.353.pdf)
- On composition bias: "conclusions drawn from a small subset can be statistically
  unstable … **subset choice can introduce selection bias**: when the benchmark
  composition is flexible, the apparent leader may be an artifact of the selected tasks
  rather than a genuine improvement" —
  [Source](https://arxiv.org/html/2606.27997)
- Ranking methods "nevertheless force a complete ordering, suggesting a meaningful
  distinction when there is none" under limited or noisy comparisons —
  [Source](https://www.nature.com/articles/s42005-025-02461-y)

### Inferences

- **[INF] 21 chains sits below the cited noise floor; 30–45 sits at its edge.** BenchScope's
  rough 20–50 floor ([Source](https://arxiv.org/pdf/2603.29357)) means option (a) at
  30–45 chains yields a group whose per-group accuracy has a confidence interval wide
  enough that no model comparison on it will be conclusive. That is an argument for
  labelling it a *diagnostic* set with no headline score — which is what the author
  already proposes — not for a quota'd group.
- **[INF] Options (a) and (c) are not exclusive, and the precedent favours doing both.**
  HELM's design logic (taxonomy level vs implemented level, selected for *feasibility*)
  and the knowledge-work paper's "report diagnostics alongside mean scores" both support:
  record retroactivity as a per-item field on **all** items (so it is sliceable
  benchmark-wide and the taxonomy stays complete), and additionally ship the ~21–45
  retroactive chains as a named, explicitly-underpowered diagnostic subset reported with
  counts and no quota. This gets the novelty claim and the honest statistics.
- **[INF] The field-not-group choice has a second payoff:** with retroactivity as a field
  on every item, the author can report retroactivity prevalence across the whole corpus
  — a descriptive finding about Vietnamese law that a 21-item group could never support.
- **[INF] A caution on the LawShift precedent:** I could not read its paper body, so the
  claim "LawShift separated dimensions from items *and said why*" is **not verified**.
  Treat it as a structural analogy from the abstract/metadata, and cite Robustness Gym
  and CheckList for the architecture claim instead — those are verified and stronger.

### Gaps

- **No paper found that states the facets-vs-groups rule normatively** ("a phenomenon
  should be an attribute rather than a group when X"). The case has to be assembled from
  (i) the slice/subpopulation architecture, (ii) HELM's feasibility criterion, and
  (iii) the power literature. No single citable rule exists.
- LawShift's stated rationale for dimension-vs-group separation is unverified (OpenReview
  blocked the PDF).
- BIG-bench's per-task keyword/tag mechanism, DynaBench's round structure, and GEM's
  task-and-metric design were not retrieved; I did not confirm how they treat facets.
- BenchScope's "20–50" floor was reported by the extraction as approximate and
  benchmark-dependent, and the paper gives no absolute threshold. Do not cite it as a
  hard rule.

---

## Q5. Precedent for OPTION (b): benchmarks whose difficulty is that the correct answer is an OLDER document than the newest retrievable one — how are such items built and named?

### Takeaway

This is now a well-populated design pattern with at least four independent 2026
constructions and settled vocabulary: **Pre-Amendment Questions**, **current-law
substitution**, **Legacy Exception Rules**, and pre-Code/post-Code splits. The standard
recipe is: build a versioned corpus with validity intervals, locate drift points where
versions disagree, anchor the question to a date inside an older interval, and screen so
the current text cannot produce the right answer. The author's option (b) is the
*inverse-direction* variant (newest document is future-effective rather than
superseding), which the same literature names **future-law leakage** and leaves unbuilt.

### Cited Findings — construction recipes

- **Drift-point curation (French tax law).** Pipeline: automatic drift-point surfacing →
  manual question/answer drafting → expert review. Deliberate screening so the current
  text *lacks* the correct historical value in **208 of 209** scored questions, "forcing
  systems to retrieve deliberately older versions." Scoring by deterministic nuggets
  (regex article IDs; numeric values with tolerance), never LLM-as-judge. Baseline:
  static RAG gets the date-applicable version **0% of the time** —
  [Source](https://arxiv.org/html/2608.09393)
- **Pre-Amendment Questions (statutory QA).** Named category, defined as questions
  "where the correct answer depends on an **older version of the law rather than the
  current one**" — framed as the inverse of post-cutoff staleness, testing whether models
  can suppress newer knowledge. Sizes: Post-Cutoff Amendment 115 pairs, Pre-Amendment
  113, Multi-Provision Pre-Amendment 84; total 312 of 697 generated kept (55%) after
  validation by two senior law students and one qualified lawyer —
  [Source](https://arxiv.org/html/2605.23497)
- **Regime split (Chinese civil law).** 26,000 judgments split 50/50 post-Code (2021
  Civil Code) vs pre-Code (prior standalone statutes); 200 sampled cases per trial, 100
  per split; metric is TALD accuracy (temporal applicable-law determination), computed
  per item on statute-version matching. The construction *is* the split — no synthetic
  perturbation — [Source](https://arxiv.org/html/2608.14610)
- **Hard-negative version generation (TimelyQABench).** For each policy theme, multiple
  temporally ordered versions share a topic but have "selected clauses revised in
  eligibility, scope, **effective period**, exception conditions, or required actions,"
  producing hard negatives that are "semantically similar but **temporally invalid**."
  Validation on four criteria: relevance, derivability, time sensitivity, domain
  specificity. The older-answer-correct category is named **Legacy Exception Rules** —
  [Source](https://arxiv.org/html/2609.11572)
- **Synthetic-amendment construction (LeKUBE / LawShift).** LeKUBE: law-school
  annotators write synthetic updates to the Chinese Criminal and Civil Codes plus
  question sets "of which the answers would change after the updates" (180 statutes) —
  [Source](https://arxiv.org/html/2407.14192v2). LawShift: metamorphic testing with 31
  revision types taken only from revisions empirically observed across the 12 historical
  Criminal Code Amendment editions; finding is that even SOTA LLMs "consistently fail to
  incorporate synthetic statutory amendments … **defaulting instead to predictions
  anchored in the current law**" —
  [Source](https://neurips.cc/virtual/2025/poster/121832);
  [Source](https://openreview.net/forum?id=5SpFenlxDF)
- **Naming for the retrieval-side mechanism:** **article-number aliasing** — identical
  identifiers across versions — is cited as a root cause, alongside parametric recency
  bias and absent date-conditioning — [Source](https://arxiv.org/html/2608.09393)

### Inferences

- **[INF] Option (b) is better supported than T5 on every construction axis.** It has a
  name in the literature (future-law leakage), a documented open gap, a transferable
  recipe (drift-point surfacing + date anchoring + screening so the newest document
  cannot yield the answer), an established naming convention to follow
  (Pre-Amendment / Legacy Exception), and 3,856 candidate transitions against T5's 21.
- **[INF] A 30-day minimum gap is a defensible screening threshold by analogy.** The
  French-tax benchmark screens on *answer divergence* (208/209), not gap length; the
  author's 30-day gap is a proxy for the same property — that the newest retrievable
  document is not yet the governing one. **[INF]** Stronger: screen on divergence as
  well as gap, i.e. keep only transitions where the not-yet-effective text would give a
  materially different answer, mirroring the 208/209 screen.
- **[INF] Suggested naming, consistent with the field:** "Not-Yet-In-Force" or
  "Vacatio Legis" items, with the failure mode reported as future-law leakage rate. Both
  terms are already in print ([Source](https://arxiv.org/html/2608.09393);
  [Source](https://arxiv.org/html/2506.07853)).
- **[INF] Deterministic nugget scoring is the defensible choice** for either option — the
  French-tax authors reject LLM-as-judge explicitly for a domain where "legal correctness
  is binary and conditional on date" ([Source](https://arxiv.org/html/2608.09393)).

### Gaps

- No existing benchmark *scores* a not-yet-in-force group, so there is no published
  item count, difficulty figure or baseline for option (b) to be calibrated against.
  The 0% static-RAG figure is for the older-version direction, not the future direction.
- Whether the French-tax `VIGUEUR_DIFF` versions were used in any unscored/exploratory
  track is not stated in what I read; the paper says only that the mode is "reserved for
  future work."
- TimelyQABench's full list of six temporal reasoning categories was not retrieved —
  only "Legacy Exception Rules" was named in the extracted text.

---

## Bottom line for the benchmark author

1. **T5 as novelty (option a):** defensible as "first to evaluate retroactive
   commencement as a distinct phenomenon in point-in-time legal QA," but not as "first to
   notice it." LexKairos (2026) and de Martim (2026) both name retroactivity in print and
   decline to benchmark it; the temporal-QA survey does not mention it at all. At 21–45
   chains it is below the cited reliability floor, so it should ship as an explicitly
   underpowered diagnostic set with no headline score — which is exactly what the
   fragmentation literature recommends over a quota'd group.
2. **Option (b) is the strongest contribution of the three:** the phenomenon already has
   a name (**future-law leakage**), a published admission that **no scored benchmark
   exercises it**, a transferable construction recipe, and a corpus two orders of
   magnitude larger. It is also adversarial against the field's default temporal-conflict
   heuristic (rank by recency), which makes it a sharper diagnostic than T5.
3. **Option (c) has the cleanest precedent:** slices/subpopulations (Robustness Gym),
   capability × test-type matrices (CheckList), scenario × metric grids chosen for
   feasibility (HELM), per-item temporal fields with retroactivity as a document clause
   (TimelyQABench), and — decisively — the legal standards themselves, which encode
   retroactivity as two attributes on a fragment (`@startEfficacy` vs `@start` in Akoma
   Ntoso) rather than as a document class.
4. **Options (a)+(c) combine, and (b) stands alone as a new group.** Recording
   retroactivity as a field on every item costs nothing, keeps the taxonomy complete,
   enables a corpus-wide prevalence finding, and leaves room to also report the small
   retroactive subset as a diagnostic. Replacing the *quota slot* with option (b) is the
   move the evidence supports.
