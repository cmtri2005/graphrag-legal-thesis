# Venue standards for a new dataset / benchmark paper (state as of 2 Oct 2026), mapped to ViLexTime

Scope note. This file deliberately does not repeat `research_notes/Schema bộ dữ liệu ViLexTime/dataset_release_conventions.md`
(Croissant versioning rules, split encoding, per-item flags, bitemporal fields, no-answer encoding, the BIG-bench canary,
ARR items B1–B6/D1/D2/D5 verbatim, the NeurIPS 2025 CFP hosting text). It adds: the NeurIPS 2026 track changes and the
exact mandatory Croissant/RAI field lists, the NeurIPS paper checklist and LLM policy, the full ARR checklist incl. D3/D4/E1,
ARR reviewer-form and "lazy reviewing" rules, LREC facts, BetterBench and construct-validity findings, contamination
guidance, and the Vietnamese legal status of the source texts.

Tier legend used throughout: **[M]** = mandatory, failure is a stated desk-rejection ground; **[S]** = strongly expected by
reviewers (asked in a checklist or review form, or a well-documented common weakness); **[N]** = nice to have.

Web tooling hit a session limit part-way through; items that could not be fetched are listed under Gaps, not asserted.

## 1. NeurIPS Datasets & Benchmarks track (now "Evaluations & Datasets"), 2025 → 2026

### Takeaway
In 2026 the track was renamed **Evaluations & Datasets (E&D)**, stays a separate track (not merged into main), switched to
**double-blind by default** (single-blind only on request when a dataset cannot be anonymised), and made **Croissant core +
8 RAI fields** mandatory; an invalid Croissant file, inaccessible data, or a missing paper checklist are each explicit
desk-rejection grounds. The NeurIPS 2026 cycle is closed (submission 6 May 2026, notifications 24 Sep 2026), so for
ViLexTime the realistic NeurIPS target is the 2027 cycle.

### Cited Findings
- 2026 rename and scope: "Previously called 'Datasets & Benchmarks Track,' renamed to 'Evaluations & Datasets Track'"; the
  track "welcomes contributions that advance the science of AI evaluation"; "Data-centric and benchmarking submissions
  historically welcomed by the track remain fully in scope", incl. new datasets and benchmarks; authors must "articulate how
  their work meaningfully changes, strengthens, or enables the evaluation of AI/ML systems". Separate submission portal, not
  merged with main track — [NeurIPS 2026 E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- 2026 dates: portal opened 15 Apr 2026, abstracts 4 May 2026, full papers 6 May 2026, notifications 24 Sep 2026 (AoE) —
  [NeurIPS 2026 E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets); same dates on
  [NeurIPS 2026 main CFP](https://neurips.cc/Conferences/2026/CallForPapers)
- **[M] Anonymity 2026**: double-blind is the default; authors may request single-blind if "the submission centers on datasets
  that cannot be fully anonymized for scientific or ethical reasons"; authors should still make a "best-effort attempt to
  anonymize the submission" — [NeurIPS 2026 E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- **Changed from 2025**: in 2025 "Authors can choose to submit either single-blind or double-blind" (single-blind via
  `\usepackage[preprint]{neurips_2025}`) — [NeurIPS 2025 D&B CFP](https://neurips.cc/Conferences/2025/CallForDatasetsBenchmarks);
  [NeurIPS 2025 D&B FAQ](https://nips.cc/Conferences/2025/DatasetsBenchmarks-FAQ)
- **[M] Mandatory Croissant core fields (2026)**: Dataset: `@context`, `@type` ("sc:Dataset"), `name`, `url`, `license`,
  `conformsTo`, `distribution`, `recordSet`; FileObject: `@id`, `contentUrl`, `encodingFormat`; RecordSet: `@id` and at least
  one `field`; each Field: `@id`, `dataType`, and `source` or `value` —
  [NeurIPS 2026 E&D hosting guidelines](https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting)
- **[M] Mandatory RAI fields (2026)**: "data limitations, data biases, personal/sensitive information, data use cases, social
  impact, synthetic data indicator, source datasets, and provenance activities (preprocessing, collection, annotation)" —
  [NeurIPS 2026 E&D hosting guidelines](https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting); background and the
  online RAI checker: [NeurIPS blog, May 2026](https://blog.neurips.cc/2026/05/04/responsible-ai-metadata-requirements-for-the-evaluations-and-datasets-track-neurips-2026/)
- **[M] Desk rejection**: "if your Croissant file is invalid or if your data is not accessible" —
  [NeurIPS 2026 E&D hosting guidelines](https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting); datasets/code must be
  "available and accessible to all reviewers, ACs, and SACs at submission time", "Non-compliance justifies the desk rejection
  of the paper" — [NeurIPS 2026 E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- **[M] Hosting**: Harvard Dataverse, Kaggle, Hugging Face, OpenML auto-generate Croissant; self-hosting allowed if reviewers can
  reach it by URL. Dataverse and Kaggle support private "Link Sharing"; "Hugging Face doesn't offer this feature" —
  [NeurIPS 2026 E&D hosting guidelines](https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting)
- **[M] Code**: required when "the primary contribution is a reusable executable artifact", optional for analytical/conceptual
  contributions; must be documented and executable; datasets >4 GB must ship samples —
  [NeurIPS 2026 E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- **[M] Camera-ready**: "All accepted papers must have their code and datasets documented and publicly available by the
  camera-ready deadline" — [NeurIPS 2026 E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- **[S] Licence**: "a clear license that enables the intended use"; "open data licenses" recommended; stricter licences only for
  "ethically sensitive data", kept "as open as possible" — [NeurIPS 2026 E&D hosting guidelines](https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting).
  Licence was the most frequently missing metadata among initial 2025 submissions (11.9%) —
  [NeurIPS blog, Mar 2025](https://blog.neurips.cc/2025/03/10/neurips-datasets-benchmarks-raising-the-bar-for-dataset-submissions/)
- **[M] NeurIPS Paper Checklist**: "The papers not including the checklist will be desk rejected." Dataset-relevant items:
  (2) limitations, separate section encouraged; (4) "If the contribution is a dataset or model, what steps did you take to make
  your results reproducible or verifiable?"; (5) code/data/instructions to reproduce main results; (10) negative societal
  impacts; (12) existing assets: "did you cite the creators and respect the license and terms of use?"; (13) new assets: "did
  you document them and provide these details alongside the assets?"; (14) crowdsourcing/human subjects: full instructions,
  screenshots, compensation; (15) participant risks and IRB "or an equivalent approval/review based on the requirements of your
  institution, if applicable"; (16) "Does the paper describe the usage of LLMs if it is an important, original, or non-standard
  component of the core methods in this research?" — [NeurIPS Paper Checklist guide](https://neurips.cc/public/guides/PaperChecklist)
- **LLM policy (2025 text; 2026 main track defers to its Handbook)**: editing/grammar use needs no disclosure; LLM use "should be
  described in the experimental setup section (or equivalent) if it is an important, original, or non-standard component";
  authors "are responsible for the entire content of the paper"; LLMs cannot be authors —
  [NeurIPS 2025 LLM policy](https://neurips.cc/Conferences/2025/LLM); 2026 main CFP points to the Main Track Handbook for
  "reciprocal reviewing, dual submissions and LLMs" — [NeurIPS 2026 CFP](https://neurips.cc/Conferences/2026/CallForPapers)
- **Private hold-out sets** are allowed if described, but "The main contribution of your paper should be the publicly released
  portion of your dataset"; existing public datasets must not be claimed as part of the submission; gated access must be
  "guaranteed to be maintained for many years" — [NeurIPS 2025 D&B FAQ](https://nips.cc/Conferences/2025/DatasetsBenchmarks-FAQ)
- Documentation frameworks the track points to (recommended, not individually mandated): "datasheets for datasets, dataset
  nutrition labels, data statements for NLP, data cards, and accountability frameworks" —
  [NeurIPS blog, Mar 2025](https://blog.neurips.cc/2025/03/10/neurips-datasets-benchmarks-raising-the-bar-for-dataset-submissions/)
- Scale and selectivity: 1,995 submissions in 2025 (1,820 in 2024); 2024 acceptance 25.3% vs main 25.8%; chairs: it is "less
  common for a dataset submission to be fundamentally 'technically incorrect'", so decisions hinge on "impact and scientific
  relevance" — [NeurIPS D&B chairs, Sep 2025](https://blog.neurips.cc/2025/09/30/reflecting-on-the-2025-review-process-from-the-datasets-and-benchmarks-chairs/)
- Chairs' suggestions for future years included clearer RAI provenance/bias documentation and possibly "requiring a
  'demonstrated impact' section" (suggestion, not a confirmed rule) —
  [NeurIPS blog, Dec 2025](https://blog.neurips.cc/2025/12/05/neurips-datasets-benchmarks-track-from-art-to-science-in-ai-evaluations/)

### Inferences
- Because decisions turn on impact rather than correctness, the ViLexTime paper must argue *why temporal validity in law is an
  evaluation gap* (the 2026 CFP wording: how the work "changes, strengthens, or enables" evaluation), not just describe the data.
- Double-blind default + HF lacking private link sharing ⇒ for a NeurIPS submission, host the review copy on Dataverse or Kaggle
  with a private link, or on an anonymous HF account; switch to the named HF repo at camera-ready. Requesting single-blind is
  weakly justified for ViLexTime (nothing about the data identifies the authors).
- "Synthetic data indicator" and "provenance activities (annotation)" are where LLM-drafted questions and the LLM-jury
  annotator A must be declared; omitting them is an RAI-checker failure, not just a reviewer complaint.

### Gaps
- Exact NeurIPS 2026 review form/scoring rubric for E&D (CFP defers to the main track) and the 2026 Main Track Handbook LLM
  text were not retrieved; the 2025 LLM policy is quoted instead — verify before submission.
- Whether the old D&B "author statement that they bear all responsibility in case of violation of rights" is still required in
  2026 was not confirmed by any page fetched; neither the 2025 nor 2026 CFP text retrieved mentions it.
- NeurIPS 2027 dates are unknown; the "May 2027" assumption is extrapolation from 2025/2026, not a source.
- No source found listing the most common *rejection* reasons quantitatively for D&B/E&D.

## 2. ACL Rolling Review (ACL/EMNLP/NAACL main + Findings), LREC/COLING

### Takeaway
ARR has no separate dataset track; resource papers go through the standard form (soundness, excitement, overall, reproducibility,
confidence). The Responsible NLP checklist is mandatory: a justified "No" is fine, but systematically failing to answer is a
desk-rejection ground. ARR guidelines explicitly forbid rejecting a paper for being non-English or niche. LREC is the main
resource venue but is biennial (last: May 2026).

### Cited Findings
- **[M] Checklist mandatory**: "Submissions that systematically fail to provide either specific relevant sections or
  justification...will be desk-rejected"; "Not answering positively to a question is not grounds for rejection" with
  justification; last updated for the October 2024 cycle — [ARR Responsible NLP Checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- Items not covered in the earlier notes: **A1** limitations; **A2** risks; **C1–C4** model sizes/compute, hyperparameters,
  descriptive statistics ("transparent whether you are reporting the max, mean, etc."), package settings; **D3** "Did you
  discuss whether and how consent was obtained from people whose data you're using/curating?"; **D4** "Was the data collection
  protocol approved (or determined exempt) by an ethics review board?"; **E1** "If you used any AI assistants, did you include
  information about your use?" — [ARR Responsible NLP Checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- **ACL generative-AI policy**: content-creating use "should be fully disclosed in the Acknowledgements section" (example:
  "Section 3 was written with inputs from ChatGPT"); grammar/spell checking needs no disclosure; permitted uses include
  language refinement, literature search, low-novelty text that authors verify; authors are fully accountable. The policy does
  not specifically address LLM-generated datasets — [ACL Policy on Publication Ethics](https://www.aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics)
- **Review form (as of Feb 2025)**: Soundness (must be "justified by the text of the review"), Excitement ("orthogonal to the
  assessment of soundness"), Overall assessment (composite incl. novelty/impact), plus confidence, reproducibility, and
  whether the reviewer knows the authors — [ARR reviewer guidelines](https://aclrollingreview.org/reviewerguidelines)
- **Resource papers are in scope**: "NLP is an interdisciplinary field, relying on many kinds of contributions: models,
  resource, survey, data/linguistic/social analysis, position, and theory"; lazy-review heuristics reviewers must not use
  include dismissing niche topics and penalising non-English work ("The same is true of NLP research that tests only on
  English"), and listing acknowledged limitations as weaknesses (H16) — [ARR reviewer guidelines](https://aclrollingreview.org/reviewerguidelines)
- **LREC 2026**: 11–16 May 2026, Palma de Mallorca; papers 4–8 pages excluding references; authors are "offered the opportunity"
  to share resources, linked to the LRE Map (voluntary) — [LREC 2026 CFP via LINGUIST List 36.1917](https://linguistlist.org/issues/36/1917);
  submission deadline was 17 Oct 2025 — [LREC 2026 CFP thread](https://list.lrec-conf.org/mailman3/hyperkitty/list/corpora@list.elra.info/thread/TEHBCJUAJM3XLLQF632MKCSVLP37FQ6E);
  described as the "fifteenth biennial" LREC — [resurchify listing](https://www.resurchify.com/ed/lrec-2025-fifteenth-biennial-language-resources-and/19912)
- **ARR calendar 2026–27**: August 2026 cycle (deadline 3 Aug 2026) → EACL 2027, commit 11 Oct 2026; **October 2026 cycle
  (deadline 12 Oct 2026)** → NAACL 2027 and COLING 2027, reviews due 16 Nov, meta-reviews 17 Dec, commit 23 Dec 2026;
  **January 2027 cycle → ACL 2027** (exact date not yet posted); ARR "generally runs five cycles per year" —
  [ARR dates](https://aclrollingreview.org/dates). NAACL 2027: San Francisco, 1–5 Jun 2027, ARR deadline 12 Oct 2026 —
  [NAACL 2027](https://2027.naacl.org/). (A search summary gave COLING 2027 commit as 24 Dec 2026; ARR's page says 23 Dec —
  likely a time-zone difference.)
- **NLLP 2026** (8th, @EMNLP 2026, Budapest, 28/29 Oct 2026): submission deadline 11 Aug 2026, ARR-commit deadline 27 Aug 2026,
  OpenReview — [NLLP 2026 CFP](https://www.aclweb.org/portal/content/nllp-2026) — closed for this cycle.
- **ICAIL 2027**: Vienna, 5–9 Jul 2027, papers due 28 Jan 2027 — [BERI event listing (aggregator)](https://www.beri.net/events/icail-2027);
  ICAIL host call — [IAAIL](https://iaail.org/call-for-expressions-of-interest-to-host-icail-2027/)

### Inferences
- Under ARR, a Vietnamese-only legal benchmark cannot be legitimately rejected for language or niche-ness (H9/H10), but the
  Soundness score will hinge on label quality evidence (IAA, adjudication) and a defensible metric; the Excitement score on the
  temporal-validity framing. Findings is the realistic floor if Excitement is low but Soundness is solid.
- Because ARR's AI-use disclosure goes in Acknowledgements (writing) and checklist E1, while NeurIPS wants methodological LLM use
  in the experimental-setup section, ViLexTime should do both: a methods paragraph on LLM roles in data creation, plus the
  acknowledgement line.
- LREC is the most resource-friendly venue but the next edition (by the biennial pattern) would be 2028, too late for the
  thesis; it is not a realistic 2026–2027 target.
- Timing: the 16 Nov 2026 data freeze is after the 12 Oct ARR deadline, so NAACL/COLING 2027 are only reachable with a paper
  submitted on a pre-freeze subset (risky: reviewers would see a different dataset than the final one). The clean targets are the
  **January 2027 ARR cycle (ACL 2027)**, **ICAIL 2027 (28 Jan 2027)**, and NeurIPS 2027 E&D. NLLP 2026 is closed; NLLP 2027
  (likely @EMNLP 2027, deadline ~Aug 2027 by the 2026 pattern) is a fallback.

### Gaps
- ACL 2027 January-cycle exact deadline not yet posted on ARR dates page.
- COLING 2027 resource-paper criteria and ICAIL 2027 data/ethics requirements were not retrieved; ICAIL date is from an aggregator.
- LREC ethics/limitations section requirements and anonymity mode were not in the fetched CFP text.
- JURIX 2026 not researched.

## 3. Documentation frameworks: what is required vs recommended

### Takeaway
Only **Croissant (+RAI)** is machine-enforced (NeurIPS 2026). ARR enforces *content* (B5/B6, D1–D5) not a format. Datasheets,
Data Statements, Data Cards and nutrition labels are listed as recommended frameworks; reviewers expect *one* of them in an
appendix.

### Cited Findings
- NeurIPS: Croissant core + RAI mandatory, desk-reject on invalid file —
  [NeurIPS 2026 E&D hosting guidelines](https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting)
- NeurIPS lists datasheets, nutrition labels, data statements, data cards, accountability frameworks as standards authors are
  encouraged to use — [NeurIPS blog, Mar 2025](https://blog.neurips.cc/2025/03/10/neurips-datasets-benchmarks-raising-the-bar-for-dataset-submissions/)
- ARR B5 asks for documentation of "coverage of domains, languages, and linguistic phenomena, demographic groups represented";
  B6 statistics and splits — [ARR Responsible NLP Checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- NeurIPS checklist item 13: new assets must be documented "alongside the assets" (i.e., in the hosted repo, not only in the
  paper) — [NeurIPS Paper Checklist guide](https://neurips.cc/public/guides/PaperChecklist)
- Datasheets for Datasets question bank (motivation, composition, collection, labelling, uses, distribution, maintenance) as
  quoted in the earlier notes — [Datasheets for Datasets](https://ar5iv.labs.arxiv.org/html/1803.09010)
- Data Statements (Bender & Friedman; guide now at version III, 2024): long form covers curation rationale, language variety
  (BCP-47 tag plus prose description), speaker demographic, annotator demographic, speech situation, text characteristics, and a
  provenance appendix; a short form points to the long form —
  [Data Statements Guide III](https://techpolicylab.uw.edu/wp-content/uploads/2024/11/Data_Statements-Guide-III.pdf);
  [Data Statements Guide V2](https://techpolicylab.uw.edu/wp-content/uploads/2021/11/Data_Statements_Guide_V2.pdf);
  [UW Tech Policy Lab](https://techpolicylab.uw.edu/data-statements/) (elements via search summary of these documents)
- BetterBench found "Standardized metadata is included" is a criterion "not fulfilled by almost any benchmark" —
  [BetterBench, arXiv 2411.12990](https://arxiv.org/html/2411.12990v1)

### Inferences
- Lazy path that satisfies every venue: one HF dataset card (README) that *is* a datasheet (answer the Gebru questions in its
  sections) + a short Data-Statement-style block for language variety (Vietnamese, legal register, `vi`) + Croissant with RAI
  fields filled from that same text. Writing a separate Data Card on top adds no compliance value.

### Gaps
- Google Data Cards (Pushkarna et al.) structure was not fetched; no claims made about its fields.
- Data Statements elements come from a search summary of the guide PDFs, not a full read of Guide III.

## 4. Benchmark-quality frameworks and the most-failed criteria

### Takeaway
Reviewers increasingly use BetterBench and construct-validity language. The most frequently failed items are: replication
scripts, statistical significance/uncertainty, standardised metadata, contamination prevention, and an explicit argument that
the benchmark measures the stated phenomenon (construct validity), plus over-reliance on exact match.

### Cited Findings
- BetterBench (NeurIPS 2024 D&B, spotlight): 46 best practices over four lifecycle stages (design, implementation,
  documentation, maintenance), 24 benchmarks scored 0/5/10/15 per criterion — [BetterBench abstract](https://arxiv.org/abs/2411.12990);
  [BetterBench full text](https://arxiv.org/html/2411.12990v1)
- BetterBench criteria include: design — clear tested capability, domain experts involved, metric interpretation, human/random
  baselines and floor/ceiling, differentiation from related benchmarks, input sensitivity, validation of automatic evaluation;
  implementation — evaluation code and test data available, replication scripts, contamination prevention via unique identifiers
  or encryption, training-on-test detection; documentation — construction process, statistical significance, limitations and
  normative assumptions, quick-start, licence, standardised metadata; maintenance — code usability monitoring, feedback
  channel, maintainer contact, retirement statement — [BetterBench full text](https://arxiv.org/html/2411.12990v1)
- Most-failed: "17 out of 24 benchmarks do not provide easy-to-run scripts to replicate the results"; statistical significance
  averaged 5.62/15 and "14 out of 24 benchmarks did not perform multiple evaluations"; implementation stage weakest (6.2/15 vs
  design 10.8, documentation 10.1, maintenance 9.6); "benchmarks with poorer design tend to also be less usable" —
  [BetterBench full text](https://arxiv.org/html/2411.12990v1)
- Construct validity review (Bean et al., NeurIPS 2025 D&B), 445 articles, 29 expert reviewers; eight recommendations: define
  the phenomenon; measure the phenomenon and only the phenomenon; construct a representative dataset; acknowledge limits of
  reusing datasets; prepare for contamination; use statistical methods to compare models; conduct an error analysis; justify
  construct validity — [Bean et al., arXiv 2511.04703](https://arxiv.org/html/2511.04703);
  [NeurIPS 2025 proceedings](https://proceedings.neurips.cc/paper_files/paper/2025/hash/1967e0fc3aa6cbbace562f5cb8e3954e-Abstract-Datasets_and_Benchmarks_Track.html)
- Bean et al. quantities: only 16.0% used statistical tests or uncertainty for model comparison; 81.3% relied at least partly on
  exact match; 39.0% used convenience sampling; 31.2% generated task data with LLMs; 78.2% defined the phenomenon but only 52.2%
  of those with widely agreed definitions; 53.4% addressed construct validity — [Bean et al.](https://arxiv.org/html/2511.04703)
- Raji et al. (NeurIPS 2021 D&B): influential benchmarks are framed as general measures of progress but lack the construct
  validity to support such claims — [Raji et al., arXiv 2111.15366](https://arxiv.org/abs/2111.15366)

### Inferences
- For ViLexTime the construct is narrow and definable ("given a legal question and a date, return the provision text in force
  on that date"), which is a strength under Raji/Bean; the paper should *state* that it does not measure legal advice quality or
  multi-provision reasoning.
- The documented gold–KG circularity (gold derived from the same version graph the proposed GraphRAG uses) is a direct hit on
  Bean rec. 2 and BetterBench "validation of automatic evaluation"; reviewers will ask for a human-verified subset whose gold was
  checked against the source text independently of the KG.
- With 300 items per group, a 95% interval on accuracy near 0.5 is about ±5.7 pp (1.96·√(0.25/300)); per-group comparisons
  between systems closer than that need paired tests (bootstrap/McNemar). Reporting this pre-empts the 16% finding.
- Exact match on full provision text is the 81.3% weakness; a two-part scorer (version-ID accuracy as primary, text overlap as
  secondary, plus abstention accuracy for T6) is easier to defend.

### Gaps
- Raji et al.'s concrete recommendations section was not retrievable (abstract only).
- No 2026 survey on benchmark checklists newer than Bean et al. (Nov 2025) was retrieved.

## 5. Legal and ethical points specific to ViLexTime

### Takeaway
Vietnamese legal normative documents are excluded from copyright (Law on IP, Art. 15), and Decree 52/2015 gives everyone the
right to use texts from the National Legal Database free of charge, so redistributing provision text is legally low-risk; the
team's own questions/labels can be licensed openly. vbpl.vn has no visible terms of use; the governing decree is being replaced
(draft discussed Sep 2026), so snapshots are essential. LLM roles in data creation must be disclosed at both venues.

### Cited Findings
- Law on IP Art. 15 — objects not protected by copyright: pure news reporting; "văn bản quy phạm pháp luật, văn bản hành chính,
  văn bản khác thuộc lĩnh vực tư pháp và bản dịch chính thức của văn bản đó"; processes, systems, methods, concepts, principles,
  data — [Thư viện Pháp luật Q&A](https://thuvienphapluat.vn/hoi-dap-phap-luat/cac-doi-tuong-khong-thuoc-pham-vi-bao-ho-quyen-tac-gia-235097.html);
  [LuatVietnam](https://luatvietnam.vn/tin-phap-luat/3-doi-tuong-khong-duoc-bao-ho-quyen-tac-gia-230-30625-article.html)
  (search-result summaries; primary page returned 403)
- The exclusion is detailed by Decree 17/2023/NĐ-CP; it covers texts of state agencies, political and socio-political
  organisations and armed-forces units — [Luật sư Việt Nam (lsvn.vn)](https://lsvn.vn/doi-tuong-nao-khong-thuoc-pham-vi-bao-ho-quyen-tac-gia-1683458018.html)
- Decree 52/2015/NĐ-CP on the National Legal Database: Art. 4 texts in the database "được sử dụng chính thức"; Art. 18 "Các cơ
  quan, tổ chức, cá nhân được quyền khai thác, sử dụng miễn phí văn bản"; Art. 6 prohibits damaging infrastructure "hoặc cản
  trở quá trình vận hành" and illegal access to alter/delete data —
  [Decree 52/2015 text (caselaw.vn)](https://caselaw.vn/van-ban-phap-luat/116826-nghi-dinh-52-2015-nd-cp-ve-co-so-du-lieu-quoc-gia-ve-phap-luat);
  [original PDF on vbpl.vn](https://vbpl.vn:443/FileData/TW/Lists/vbpq/Attachments/67193/VanBanGoc_52.2015.NĐ.CP.pdf)
- vbpl.vn is run by the Ministry of Justice; no terms of use / copyright / reuse text visible on the homepage —
  [vbpl.vn](https://vbpl.vn/)
- A decree replacing Decree 52/2015 is in drafting: drafting team set up by Decision 1097/QĐ-BTP (2026); workshop 18 Sep 2026;
  draft has 4 chapters, 26 articles, scope extended to commune-level documents —
  [LuatVietnam, QĐ 1097/QĐ-BTP](https://luatvietnam.vn/co-cau-to-chuc/quyet-dinh-1097-qd-btp-2026-thanh-lap-to-soan-thao-nghi-dinh-thay-the-nghi-dinh-52-2015-nd-cp-434564-d1.html);
  [MOJ workshop news](https://moj.gov.vn/portal/tin-tuc/chi-tiet/hoi-thao-lay-y-kien-du-thao-nghi-inh-thay-the-nghi-inh-so-522015n-cp-tai-tinh-ha-tinh-tk98vx0b9a.html);
  commentary (19 Sep 2026) mentions "dữ liệu tạo lập một lần tại nguồn" and mandatory "gắn nhãn nhận biết AI" —
  [Dân chủ & Pháp luật](https://danchuphapluat.vn/doi-moi-co-so-du-lieu-quoc-gia-ve-phap-luat-trong-ky-nguyen-so-10337.html)
- LLM disclosure: NeurIPS checklist item 16 + methods-section description —
  [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist), [NeurIPS LLM policy](https://neurips.cc/Conferences/2025/LLM);
  ARR E1 + Acknowledgements — [ARR checklist](https://aclrollingreview.org/responsibleNLPresearch/),
  [ACL ethics policy](https://www.aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics); NeurIPS RAI
  "synthetic data indicator" — [NeurIPS 2026 hosting](https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting)
- Annotators: ARR D1 (full instructions), D2 (recruitment, pay, adequacy), D5 (demographics), D4 (ethics board or exempt);
  NeurIPS item 14 (instructions, compensation) and 15 (IRB "or equivalent ... if applicable") —
  [ARR checklist](https://aclrollingreview.org/responsibleNLPresearch/); [NeurIPS checklist](https://neurips.cc/public/guides/PaperChecklist)

### Inferences
- Licence: provision texts are not copyright-protected (Art. 15), so they can be redistributed; the team's own layer (questions,
  as_of dates, version labels, T-group tags, no-answer reasons) is the authored work. CC BY 4.0 for data + MIT/Apache-2.0 for
  code is the least-friction choice and matches the "open data licenses" recommendation. CC BY-SA would force share-alike on
  derived benchmarks and is not needed; ND licences conflict with the open-licence expectation. (CC licence semantics stated from
  background knowledge; not fetched this session.)
- State the Art. 15 / Decree 52 Art. 18 basis explicitly in the paper (answers NeurIPS item 12 and ARR B2/B3) and cite vbpl.vn as
  the creator (B1).
- Crawling: document a rate-limited, read-only crawl (Decree 52 Art. 6 prohibits obstructing operations). Because the decree and
  possibly the portal are changing, keep raw snapshots with sha256 and retrieval dates (already planned in the earlier notes).
- PII (ARR B4, RAI "personal/sensitive information"): legal documents carry signatories' names (public officials acting in office)
  and no private persons' data; say so rather than leave it blank.
- Annotators are authors: answer D2/item 14 honestly ("annotation performed by the authors as part of the research; no
  payment"), state the legal advisor's role, qualifications and whether paid; D3 consent is N/A for public legal texts; D4: state
  whether UIT required review, else "not applicable: no human-subject data".
- Per project memory (2 Oct 2026), annotator A of the D4 cross-check is now an LLM jury. Then agreement A–B is *human–LLM
  agreement*, not inter-annotator agreement; reporting it as IAA would misstate D1/D5 and the RAI annotation field. A
  human–human κ on a subset (or advisor vs annotator B) is still needed for the "IAA" claim.

### Gaps
- vbpl.vn terms of use page (if any) was not found; robots.txt not checked.
- Exact text of Decree 17/2023/NĐ-CP article detailing Art. 15 not retrieved.
- Whether UIT/VNU-HCM has an ethics review requirement for annotation-only research by students: not researched.
- Whether the new decree will change reuse terms or the portal URL: unknown (still a draft on 2 Oct 2026).

## 6. Contamination and leakage expectations

### Takeaway
Top venues do not mandate a canary or private test set, but both BetterBench and Bean et al. score contamination preparedness,
and NeurIPS allows a described private hold-out as long as the public part is the main contribution.

### Cited Findings
- Jacovi et al. (EMNLP 2023): "Test data made public should be encrypted with a public key and licensed to disallow derivative
  distribution"; demand training-exclusion controls from closed API holders "and protect your test data by refusing to evaluate
  without them"; "avoid data which appears with its solution on the internet, and release the web-page context of
  internet-derived data along with the data" — [Jacovi et al., arXiv 2305.10160](https://arxiv.org/abs/2305.10160)
- BetterBench implementation criteria: contamination prevention via unique identifiers or encryption, training-on-test-set
  detection; "pioneered by only a few of the assessed benchmarks" — [BetterBench](https://arxiv.org/html/2411.12990v1)
- Bean et al. rec. 5 "Prepare for contamination — Implement detection tests and maintain held-out evaluation sets" —
  [Bean et al.](https://arxiv.org/html/2511.04703)
- NeurIPS: private hold-out allowed if described; public portion must be the main contribution —
  [NeurIPS 2025 D&B FAQ](https://nips.cc/Conferences/2025/DatasetsBenchmarks-FAQ)
- Canary GUID convention (BIG-bench) — see earlier notes, [BIG-bench docs](https://github.com/google/BIG-bench/blob/main/docs/doc.md)

### Inferences
- ViLexTime's answers (provision text) are on the open web by construction, so Jacovi's "avoid data with its solution on the
  internet" cannot be met for the answer text; what is novel and contaminable is the (question, as_of) → version mapping. Protect
  that: canary GUID in README and every file, test split shipped as an encrypted/password zip (password in README; trivial but
  blocks crawlers), and no plain-text test answers in the GitHub repo.
- Temporal design gives a natural contamination probe: as_of dates or amendments after a model's training cutoff. Tagging each
  item with the latest relevant amendment date lets the paper report pre- vs post-cutoff accuracy.
- A small private held-out test slice (e.g., one-fifth of each group) is optional; with only 1,500 items it costs statistical
  power on the public test, so it is [N] for v1.

### Gaps
- No venue rule found that *requires* a canary or encryption; this is reviewer expectation/best practice only.

## 7. Requirement → ViLexTime mapping

### Takeaway
Most mandatory items are cheap documentation; the expensive items are the evidence reviewers actually score: human-verified gold
independent of the KG, real IAA, baselines with uncertainty, and replication scripts.

### Cited Findings
- Sources for every row are in sections 1–6 above (NeurIPS 2026 E&D CFP and hosting guidelines; NeurIPS Paper Checklist; ARR
  Responsible NLP checklist and reviewer guidelines; ACL ethics policy; BetterBench; Bean et al.; Jacovi et al.; Law on IP Art. 15;
  Decree 52/2015).

### Inferences

| Tier | Requirement (venue) | What ViLexTime must produce | Effort |
|---|---|---|---|
| M | Croissant core fields valid (NeurIPS) | HF/Dataverse repo with auto Croissant; check `license`, `conformsTo`, RecordSets per split; run validator | Low |
| M | 8 RAI fields (NeurIPS 2026) | Fill limitations, biases, personal/sensitive info, use cases, social impact, synthetic-data indicator, source datasets (vbpl.vn), provenance (crawl, preprocessing, annotation incl. LLM jury); pass RAI checker | Med |
| M | Data + code reachable by reviewers at submission (NeurIPS) | Anonymous review copy (Dataverse/Kaggle private link or anonymous HF account) + anonymised GitHub | Low |
| M | Paper checklist present (NeurIPS) / Responsible NLP checklist answered (ARR) | Every item answered with section pointers; justified N/A for D3/D4 | Low |
| M | Public release + documented executable code by camera-ready (NeurIPS) | Loader, scorer, baseline runners, README quick-start | Med |
| M/S | LLM use in data creation disclosed (NeurIPS item 16, ARR E1, ACL policy) | Methods paragraph: which fields LLM-drafted, models/versions/prompts, human checks; per-item provenance flag; acknowledgement line | Low |
| S | Clear open licence (NeurIPS hosting; ARR B2) | CC BY 4.0 data, MIT/Apache code; paragraph citing Law on IP Art. 15 and Decree 52 Art. 18 | Low |
| S | Construct definition + validity argument (Bean recs 1, 2, 8; Raji) | Define the construct per T1–T6, what is not measured, why as_of → in-force text is the right operationalisation | Low |
| S | Gold independent of the proposed system (Bean rec 2; BetterBench validation of automatic evaluation) | Human-verified subset checked against source text, not the KG; report disagreement rate with KG-derived gold | High |
| S | Representative sampling (Bean rec 3) | Documented sampling frame over vbpl.vn chains (doc type, domain, year, chain length); justify 300/group | Med |
| S | Full annotation guidelines (ARR D1; NeurIPS item 14) | Publish `docs/vilextime-annotation.md` final version as appendix + repo | Low |
| S | Agreement statistics (ARR Soundness) | Human–human κ/AC1 on a doubly-annotated subset; human–LLM-jury agreement reported separately; adjudication rate by legal advisor | Med–High |
| S | Annotator info, pay, ethics (ARR D2, D4, D5; NeurIPS 14–15) | Who annotated (authors, legal advisor's qualification), compensation statement, ethics-review statement | Low |
| S | PII/offensive content check (ARR B4; RAI) | Statement: only public officials' names as signatories; no private data | Low |
| S | Statistics and splits (ARR B6) | Table per T group × split: counts, chain length, answer length, no-answer share; lineage-grouped dev/test | Low |
| S | Baselines incl. floor/ceiling (BetterBench design) | Trivial (latest version / no-answer), closed-book LLMs, standard RAG, oracle-retrieval ceiling, small human baseline | Med |
| S | Uncertainty + significance (BetterBench; Bean rec 6) | Bootstrap 95% CIs per group, paired tests, ≥3 runs for stochastic systems | Low |
| S | Metric beyond exact match (Bean finding 81.3%) | Version-ID accuracy primary, text overlap secondary, abstention accuracy for T6 | Med |
| S | Error analysis (Bean rec 7) | Error taxonomy by T group (wrong version, stale version, false abstention) | Med |
| S | Replication script (BetterBench most-failed) | One command reproduces every table in the paper | Med |
| S | Datasheet / documentation alongside assets (NeurIPS item 13; ARR B5) | HF dataset card structured as a datasheet + language/register statement (Vietnamese, legal) | Med |
| S | Limitations section (NeurIPS item 2; ARR A1) | Gold–KG circularity, T5 coverage, only amend/repeal relations, single portal source | Low |
| S | Maintenance plan (RAI; BetterBench maintenance) | Maintainer contact, issue tracker, semantic versioning, errata log, retirement statement | Low |
| S | Contamination preparedness (Bean rec 5; BetterBench) | Canary GUID, encrypted test zip, post-cutoff slice tag | Low |
| S | Source provenance (Datasheets; RAI) | Raw snapshots + sha256 + retrieval timeframe; rate-limited crawl note (Decree 52 Art. 6) | Low |
| N | Persistent DOI | Zenodo or Dataverse deposit mirroring the HF release | Low |
| N | English examples for non-Vietnamese reviewers | English glosses of examples in the paper/appendix | Med |
| N | Private hold-out / leaderboard | Hidden test slice and evaluation server | High |
| N | Separate Data Card / nutrition label | Skip; the datasheet-style card covers it | — |

Venue fit, as inference: NeurIPS 2026, LREC 2026, NLLP 2026 and the October 2026 ARR cycle (NAACL/COLING 2027) all close
before or around the 16 Nov 2026 freeze. Realistic targets after the freeze: ARR January 2027 cycle (ACL 2027, main or
Findings), ICAIL 2027 (due 28 Jan 2027), NeurIPS 2027 E&D (dates unverified). Building to the NeurIPS 2026 E&D bar (Croissant+RAI,
checklist) also satisfies ARR's checklist, so one documentation pass covers all of them.

### Gaps
- Effort estimates are judgement, not sourced.
- Venue requirements of JURIX/ICAIL/NLLP were not retrieved; if one of them is the target, check its CFP directly.
