# Small diagnostic subsets (sub-50 items) in published benchmarks: precedent, reporting convention, and venue guidance

Scope note: this file collects only externally verifiable precedent and venue text. The
T5 situation itself (194 candidate chains / 148 clean / 21 chains / 42 rows against a
planned 50-row quota) was given and is not researched here.

Terminology used below, consistently:
- **REQUIREMENT** = enforced by a venue (desk rejection, mandatory submission field).
- **CONVENTION** = widely imitated practice in published benchmark papers, not enforced.

---

## Q1. Concrete precedents: a subset well under 100 items reported separately and excluded from the headline/macro average

### Takeaway
The canonical precedent is not "a sub-50 benchmark subset" but "a diagnostic set whose
*per-category cells* are far under 50, reported outside the headline average with an
explicit instruction that it is an analysis tool and not a benchmark." GLUE and SuperGLUE
established this; LegalBench carries it into the legal domain with the most quotable
sentence for a small-n slice. I could **not** find a top-venue benchmark paper that ships a
*named, standalone* sub-50 subset with a verbatim justification sentence — this is a real
gap, stated plainly in Gaps below.

### Cited Findings

**GLUE diagnostic set (Wang et al., ICLR 2019 / BlackboxNLP 2018) — the founding precedent**
- Framing sentence, verbatim: "The set is provided not as a benchmark, but as an analysis tool for error analysis, qualitative model comparison, and development of adversarial examples." — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Second framing sentence, verbatim: "The dataset is provided not as a benchmark, but as an analysis tool to paint in broad strokes the kinds of phenomena a model may or may not capture" — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- The reporting rule, verbatim and directly transferable: "Because the distribution of language is somewhat arbitrary, it will not be helpful to compare performance of the same model on different categories. Rather, we recommend comparing performance that different models score on the same category" — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Also verbatim: "performance on the analysis set should be compared between models but not between categories" — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Metric choice is deliberately a correlation, not accuracy: the set is evaluated with "R3, a three-class generalization of the Matthews correlation coefficient, for evaluation." — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Construction: "Each diagnostic example is an NLI sentence pair with tags for the phenomena demonstrated", with "two labeled examples for each pair" (i.e. each pair scored in both directions) — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Hedge on the taxonomy itself, verbatim: "These categories are just one lens that can be used to understand linguistic phenomena" — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Coarse-category counts from the paper's category table: Lexical Semantics 368, Predicate-Argument Structure 424, Logic 364, Knowledge 284 — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Fine-grained category names the paper enumerates (≈21+ listed): Lexical Entailment, Morphological Negation, Factivity, Symmetry/Collectivity, Redundancy, Named Entities, Quantifiers, Syntactic Ambiguity, Prepositional Phrases, Core Arguments, Alternations, Ellipsis/Implicits, Anaphora/Coreference, Intersectivity, Restrictivity, Propositional Structure, Quantification, Monotonicity, Richer Logical Structure, World Knowledge, Common Sense — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)

**SuperGLUE (Wang et al., NeurIPS 2019) — two diagnostic sets, both outside the Avg column**
- AX-b, the broad-coverage diagnostic: **1,104 test examples** — [HuggingFace super_glue dataset card](https://huggingface.co/datasets/aps/super_glue)
- AX-g, the Winogender diagnostic: **356 test examples** — [HuggingFace super_glue dataset card](https://huggingface.co/datasets/aps/super_glue)
- Description, verbatim: "GLUE includes an expert-constructed, diagnostic dataset that automatically tests models for a broad range of linguistic, commonsense, and world knowledge." — [SuperGLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1905.00537)
- Winogender addition, verbatim: "To promote the detection of such biases, we include Winogender (Rudinger et al. 2018) as an additional diagnostic dataset... Performance on Winogender is measured with accuracy and the gender parity score." — [SuperGLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1905.00537)
- Reported alongside, not inside, the headline: "Submissions to the GLUE leaderboard are required to include predictions from the submission's MultiNLI classifier on the diagnostic dataset, and analyses of the results were shown alongside the main leaderboard." The results table keeps AX-b and AX-g in separate columns from the "Avg" score column. — [SuperGLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1905.00537)
- The single most reusable caveat sentence in the whole literature for a small diagnostic set, verbatim: "Like any diagnostic, Winogender has limitations. It offers only positive predictive value: A poor bias score is clear evidence that a model exhibits gender bias, but a good score does not mean that the model is unbiased." — [SuperGLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1905.00537)

**LegalBench (Guha et al., NeurIPS 2023 Datasets & Benchmarks) — closest domain-matched precedent**
- Self-imposed size floor, verbatim: "All tasks consist of at least 50 instances." — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- A second phrasing of the same floor plus the mean, verbatim: "All LegalBench tasks contain at least 50 samples, with an average task size of 563 samples." — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- The small-slice caveat, verbatim — this is the sentence to adapt: slices "are small—and thus not intended for rigorous statistical analysis" — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- Source-concentration disclosure, verbatim, structurally identical to a "T5 comes from only 4 impacting documents" disclosure: "Because 16/17 of our issue-spotting tasks are drawn from one source... average issue performance is skewed by properties of the Learned Hands data distribution." — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- Granularity convention: category-level averages in the body, "Appendix provides full results for each model on each task" — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)

**BIG-bench (Srivastava et al., TMLR 2023) — the only explicit numeric floor found anywhere**
- Verbatim task-submission rule: "Tasks should include a minimum of 32 input-output pairs of examples, and we strongly encourage including many more examples." — [BIG-bench docs](https://github.com/google/BIG-bench/blob/main/docs/doc.md)
- Related criterion, verbatim: "Tasks where each model interaction is very short should have more than 32 examples." — [BIG-bench docs](https://github.com/google/BIG-bench/blob/main/docs/doc.md)
- No special aggregation or exclusion rule for small tasks appears in the BIG-bench documentation; the 32-example floor is the whole policy. — [BIG-bench docs](https://github.com/google/BIG-bench/blob/main/docs/doc.md)

**Precedent for excluding a sub-benchmark from a macro average on noise grounds**
- At least one recent model report separates a sub-benchmark from the macro-average because it "measures a relevant and unique capability but would introduce too much noise" into the aggregate (observed in search snippets of a 2025/2026 model report, Olmo 3, arXiv 2512.13961). Treat as a weakly-sourced data point; I did not fetch and verify the full sentence in context. — [search snippet, Olmo 3 preprint](https://arxiv.org/pdf/2512.13961)
- Independently, in a non-NLP benchmark literature, the practice of quantifying what a small subset contributes to the aggregate is explicit: subsets "are also all rather small, having always less than 100 data points (i.e., less than 2% of the overall data set size), which explains why the omission of the entire subset also has a negligible effect on the overall score" — [search snippet, benchmark subset-influence analysis](https://arxiv.org/pdf/2204.06659)
- A medical-ML position paper documents the standard low-support screen: "removing labels with fewer than 10 positive test examples can shift the resulting macro-averaged metrics non-trivially" — [search snippet, Position: Evaluation of ECG Representations Must Be Fixed](https://arxiv.org/pdf/2602.17531)

### Inferences
- The accepted precedent is *structural*, not *numeric*: no published benchmark defends "n=42 is enough to rank"; they all defend "this cell is reported as a separate, non-aggregated column with an explicit statement of what inference it does and does not license."
- GLUE's diagnostic is the strongest argument available for a sub-50 group. The set is 1,104 examples spread across ~21+ fine-grained categories and 4 coarse ones (368/424/364/284), so the *per-fine-grained-category* n is in the tens — the exact regime T5 sits in — and the authors' published answer to that is not "merge it away" but "compare models within the category, never across categories, and call it an analysis tool."
- Arithmetic inference (mine, not a quoted claim): 1,104 examples at "two labeled examples for each pair" implies 552 underlying sentence pairs. The GLUE paper text I retrieved was paraphrased as "1,100 total examples" by the extraction; cite 1,104 from the dataset card rather than the paper prose.
- LegalBench's 50-instance floor is a useful pressure point to anticipate: a reviewer who knows LegalBench may read 50 as a norm. The 42-row T5 set sits just under it, which argues for naming the group a *diagnostic set* rather than a *task*, since LegalBench's own sub-50 units are called "slices" and are explicitly disclaimed.

### Gaps
- **No named, standalone sub-50 subset in an ACL/EMNLP/NAACL/NeurIPS-D&B benchmark paper was located with its verbatim justification sentence.** Multiple query formulations ("excluded from the macro average" + diagnostic; "diagnostic subset" + "too small" + "not included in the overall score"; "illustrative rather than" + "not intended for" ranking) returned no such paper. The nearest verified precedents are (a) sub-100 *slices inside* a larger benchmark (LegalBench), (b) *per-category cells* in the tens inside a diagnostic set (GLUE), (c) a 32-example *floor* (BIG-bench). The author should expect to be the one setting the precedent, and should lean on the framing precedent rather than a size precedent.
- Exact per-fine-grained-category counts for the GLUE diagnostic were not retrieved (the full category table was truncated in extraction). The claim "many GLUE diagnostic fine-grained categories have fewer than 50 examples" is an inference from 1,104 total over 21+ fine categories, not a quoted number. Verify against the GLUE paper's category table before citing a specific cell size.
- The Olmo 3 "too much noise" exclusion sentence is from a search snippet only, not verified in context.

---

## Q2. How such subsets are presented: raw counts, per-source breakdown, no percentages, CIs, "illustrative"?

### Takeaway
The verified conventions are: (1) a **separate column or table outside the aggregate**, never folded into the headline; (2) a **metric robust to class imbalance** rather than raw accuracy; (3) an **explicit statement of the direction of inference the set supports**; (4) **per-source / per-provenance disclosure** when the small set is concentrated in few sources. Confidence intervals are not the dominant convention in these specific papers; refusing aggregation is.

### Cited Findings
- Separate-column convention: SuperGLUE's results table "clearly separates diagnostic results (AXb and AXg columns) from the main 'Avg' score column." — [SuperGLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1905.00537)
- Metric convention: GLUE scores the diagnostic set with "R3, a three-class generalization of the Matthews correlation coefficient" rather than accuracy — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Direction-of-inference convention, verbatim: "It offers only positive predictive value: A poor bias score is clear evidence that a model exhibits gender bias, but a good score does not mean that the model is unbiased." — [SuperGLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1905.00537)
- Comparison-axis convention, verbatim: "we recommend comparing performance that different models score on the same category" (and explicitly *not* across categories) — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- Per-source disclosure convention, verbatim: "Because 16/17 of our issue-spotting tasks are drawn from one source... average issue performance is skewed by properties of the Learned Hands data distribution." — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- Statistical-analysis disclaimer convention, verbatim: slices "are small—and thus not intended for rigorous statistical analysis" — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- Count-reporting is a venue **requirement**, not a convention — see Q4: "Did you report relevant statistics like the number of examples, details of train / test / dev splits, etc. for the data that you used / created?" — [ARR Responsible NLP Research checklist, item B6](https://aclrollingreview.org/responsibleNLPresearch/)
- Descriptive statistics are also a checklist item: "Did you report descriptive statistics about your results (e.g., error bars around results, summary statistics from sets of experiments)?" — [ARR Responsible NLP Research checklist, item C3](https://aclrollingreview.org/responsibleNLPresearch/)
- HELM's refusal to aggregate at all, verbatim: "we do not believe there exists a universal aggregation that satisfies all preferences, reflects all values, or captures all circumstances appropriately", leaving "the question of aggregating model performance to a single number (or a single number per scenario, or per metric) to future work" — [HELM, Liang et al. 2022/TMLR 2023](https://arxiv.org/pdf/2211.09110)
- HELM's output shape, verbatim: "a more complex collection of results per-model (i.e. a score matrix of scenarios × metrics)" — [HELM](https://arxiv.org/pdf/2211.09110)

### Inferences
- Concretely, for a 42-row group the convention-compliant presentation is: the row count and the number of source documents in the table caption or a dedicated column; the score given as a count-out-of (e.g. "17/42") *and* a rate; no claim of a significant difference between two systems on that group; no inclusion in the macro average; and one sentence stating which direction of conclusion the group supports (failure is informative, success is not proof of competence — the Winogender move).
- The ARR checklist makes **reporting** the counts mandatory while leaving the **decision to exclude from the average** entirely to the author. That asymmetry is the author's leverage: disclosure is the enforced obligation, aggregation is a design choice.
- Percentages on n=42 are not prohibited by anything I found; the defensible form is "percentage accompanied by the raw numerator/denominator," since the checklist requires the counts anyway.

### Gaps
- I found no explicit statement in GLUE, SuperGLUE, LegalBench or HELM forbidding percentages on small subsets, nor a convention of attaching confidence intervals specifically to diagnostic subsets. Claims that CIs are the norm for such sets would be unsupported by what I verified.

---

## Q3. The diagnostic-set tradition: accepted framing for "too small to rank, useful to characterise failure"

### Takeaway
The accepted framing, in the field's own words, is **"not a benchmark, but an analysis tool"** (GLUE) plus **"only positive predictive value"** (SuperGLUE/Winogender) plus **per-task reporting instead of aggregation** (LegalBench, HELM). Sizes in the tradition: GLUE diagnostic 1,104 examples over 4 coarse / 21+ fine categories; SuperGLUE AX-b 1,104, AX-g 356; BIG-bench floor 32 examples per task; LegalBench floor 50 instances per task.

### Cited Findings
- "The set is provided not as a benchmark, but as an analysis tool for error analysis, qualitative model comparison, and development of adversarial examples." — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- "to paint in broad strokes the kinds of phenomena a model may or may not capture" — [GLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.07461)
- "Like any diagnostic, Winogender has limitations. It offers only positive predictive value..." — [SuperGLUE paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1905.00537)
- Sizes: AX-b = 1,104 test examples; AX-g = 356 test examples — [HuggingFace super_glue dataset card](https://huggingface.co/datasets/aps/super_glue)
- BIG-bench floor: "Tasks should include a minimum of 32 input-output pairs of examples, and we strongly encourage including many more examples." — [BIG-bench docs](https://github.com/google/BIG-bench/blob/main/docs/doc.md)
- LegalBench floor: "All tasks consist of at least 50 instances." — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- HELM's scenario-design philosophy makes "what is missing" a first-class deliverable: holistic evaluation should "provide a top-down taxonomy and make explicit all the major scenarios and metrics that are missing"; the method is to taxonomize the space, then select "a broad subset based on coverage and feasibility, noting what's missing or underrepresented" — [HELM](https://arxiv.org/pdf/2211.09110)

### Inferences
- The tradition supplies four named roles, in descending strength of claim: *benchmark task* (rankable, aggregated) → *diagnostic set* (separate column, model-vs-model within category only) → *slice* (per-task, "not intended for rigorous statistical analysis") → *case study / qualitative analysis* (no metric at all). A 42-row group with 21 underlying chains from 4 documents fits "diagnostic set" or "slice"; calling it a *task* invites the LegalBench-50 objection, and calling it a *case study* gives up more than necessary.
- HELM's framing is the argument *for* shipping T5 rather than dropping it: under HELM, naming a scenario that the corpus cannot populate is itself a contribution, because the taxonomy and its gaps are the deliverable, not just the numbers.
- The 32 (BIG-bench) and 50 (LegalBench) floors bracket 42. The honest statement is "42 rows exceeds the floor the largest community benchmark imposes on a task (32) and falls just under the floor one legal benchmark imposed on itself (50)" — which is a defensible position precisely because neither number has any venue force.

### Gaps
- I did not verify a BIG-bench statement about how small tasks are handled in aggregate scoring (BIG-bench Lite selection, keyword-based subsetting). The documentation I fetched contains the 32-example floor and no aggregation rule for small tasks.
- I did not retrieve the original Winogender paper (Rudinger et al., NAACL 2018) for its own size statement; the SuperGLUE recast (356) is what is sourced here.

---

## Q4. Venue guidance and checklists: is there a MINIMUM subset size, or a mandated disclosure?

### Takeaway
**No venue sets a minimum subset size. None.** I checked the ARR call for papers, the ARR Responsible NLP Research checklist, the ARR author guidelines, and the NeurIPS 2026 Evaluations & Datasets (formerly Datasets & Benchmarks) call. What *is* enforced is disclosure: a mandatory Limitations section under threat of desk rejection, and a mandatory checklist item requiring example counts and split details. Those are the two hard requirements that bear on T5.

### Cited Findings

**REQUIREMENT — ARR / ACL-family Limitations section (desk-rejection enforced)**
- "Authors are required to discuss the limitations of their work in a dedicated section titled 'Limitations'." — [ARR Call for Papers](https://aclrollingreview.org/cfp)
- "This section should be included at the end of the paper, before the references, and it will not count toward the page limit." — [ARR CFP](https://aclrollingreview.org/cfp)
- "This includes both, long and short papers." — [ARR CFP](https://aclrollingreview.org/cfp)
- "Papers without a limitations section will be desk rejected." — [ARR CFP](https://aclrollingreview.org/cfp)
- Content restriction: the section "should not introduce new methods, analysis, or results", and misuse can also lead to desk rejection — [ARR CFP](https://aclrollingreview.org/cfp)
- Scope of the section, verbatim: "Generally, the limitations section should focus on the soundness of the study, and answer the question: what are the methodological caveats that the reader should be aware of when interpreting the reported findings?" — [ARR author guidelines](https://aclrollingreview.org/authors)
- Also verbatim: "Limitations section is overall not the place to discuss future work substantively, or any other content that should be part of the main paper." — [ARR author guidelines](https://aclrollingreview.org/authors)

**REQUIREMENT — ARR Responsible NLP Research checklist (submission-form field; false/incomplete answers are desk-rejectable)**
- "Authors must complete [the Responsible NLP Research checklist] as part of their paper submission." — [ARR CFP](https://aclrollingreview.org/cfp)
- "The content of checklists is used in the review process, and incorrect, incomplete or misleading information in the checklist can result in desk rejection." — [ARR CFP](https://aclrollingreview.org/cfp)
- Item B6, verbatim: "Did you report relevant statistics like the number of examples, details of train / test / dev splits, etc. for the data that you used / created?" — [ARR Responsible NLP Research checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- B6 elaboration, verbatim: "Even for commonly-used benchmark datasets, include the number of examples in train / validation / test splits, as these provide necessary context for a reader to understand experimental results." — [ARR checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- Item B5, verbatim: "Be sure to report the language of any language data, even if it is commonly-used benchmarks." — [ARR checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- Item C3, verbatim: "Did you report descriptive statistics about your results (e.g., error bars around results, summary statistics from sets of experiments)?" — [ARR checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- The checklist's own sentence on small test sets, verbatim and directly on point: "small differences in accuracy on large test sets may be significant, while on small test sets they may not be." — [ARR checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- **No minimum size anywhere in the checklist.** The fetched checklist "contains no explicit minimum dataset size requirements" and "prioritizes transparency over absolute thresholds" — there is no "too small" exemption from reporting either. — [ARR checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- The ARR author guidelines likewise "contain no explicit requirements regarding dataset size, subset size, or statistical reporting standards." — [ARR author guidelines](https://aclrollingreview.org/authors)

**REQUIREMENT — NeurIPS Evaluations & Datasets track (2026; successor to Datasets & Benchmarks)**
- "Datasets and code must be properly hosted, accessible, and clearly documented upon submission" — [NeurIPS 2026 Call for Evaluations & Datasets](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- "New datasets should remain available long-term" on a dedicated platform (Dataverse, Kaggle, Hugging Face, OpenML) — [NeurIPS 2026 CFED](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- Machine-readable documentation is mandatory: authors must use the "Croissant machine-readable format to document their datasets", including both core and Responsible AI (RAI) fields, submitted with the paper in OpenReview — [NeurIPS 2026 CFED](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- Only a *large*-data rule exists, and it is about reviewer inspection, not statistical power: "For large datasets (larger than 4GB), authors are required to include a small sample of the data to allow reviewers to inspect the data quality" — [NeurIPS 2026 CFED](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- **No minimum size:** the call "does not specify minimum dataset size requirements, minimum subset sizes, statistical power thresholds, or detailed reporting conventions beyond Croissant metadata standards." — [NeurIPS 2026 CFED](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
- Earlier D&B calls set the review standard without any size rule: the track aims for "an equally stringent review as the main conference, yet better suited to datasets and benchmarks", with accessibility as a key criterion (data obtainable "without a personal request to the PI") and supplementary materials covering "how the data was collected and organized, what kind of information it contains, how it should be used ethically and responsibly, as well as how it will be made available and maintained" — [NeurIPS Call for Datasets & Benchmarks](https://neurips.cc/Conferences/2024/CallForDatasetsBenchmarks)

**CONVENTION (documentation frameworks) — Datasheets for Datasets, Gebru et al.**
Four datasheet questions bear directly on a structurally capped subset; all are verbatim:
- "Does the dataset contain all possible instances or is it a sample (not necessarily random) of instances from a larger set? If the dataset is a sample, then what is the larger set? Is the sample representative of the larger set (e.g., geographic coverage)?" — [Datasheets for Datasets (ar5iv)](https://ar5iv.labs.arxiv.org/html/1803.09010)
- "If the dataset is a sample from a larger set, what was the sampling strategy (e.g., deterministic, probabilistic with specific sampling probabilities)?" — [Datasheets (ar5iv)](https://ar5iv.labs.arxiv.org/html/1803.09010)
- "Are there tasks for which the dataset should not be used? If so, please provide a description." — [Datasheets (ar5iv)](https://ar5iv.labs.arxiv.org/html/1803.09010)
- "Does the dataset identify any subpopulations (e.g., by age, gender)? If so, please describe how these subpopulations are identified and provide a description of their respective distributions within the dataset." — [Datasheets (ar5iv)](https://ar5iv.labs.arxiv.org/html/1803.09010)

**CONVENTION — Data Statements, Bender & Friedman (TACL 2018), schema v3**
- The schema has a dedicated LIMITATIONS element. Schema elements v3, in order: HEADER; EXECUTIVE SUMMARY; CURATION RATIONALE; DOCUMENTATION FOR SOURCE DATASETS; LANGUAGE VARIETIES; LANGUAGE USER DEMOGRAPHIC; ANNOTATOR DEMOGRAPHIC; LINGUISTIC SITUATION AND TEXT CHARACTERISTICS; PREPROCESSING AND DATA FORMATTING; CAPTURE QUALITY; LIMITATIONS; METADATA; DISCLOSURE AND ETHICAL REVIEW; DISTRIBUTION; MAINTENANCE; OTHER; GLOSSARY — [Tech Policy Lab, Data Statements](https://techpolicylab.uw.edu/data-statements/)
- Purpose framing: data statements convey "essential information about the characteristics of datasets, including but not limited to the curation rationale and data sources", and help identify "gaps" in datasets and mitigate "bias in the dataset (such as a mismatch between training datasets and contexts where systems are deployed)" — [Tech Policy Lab](https://techpolicylab.uw.edu/data-statements/)

### Inferences
- **Stated plainly, as requested: no minimum-subset-size rule exists at ACL/ARR or at the NeurIPS datasets track.** The only numeric floors in this entire research space are self-imposed by individual benchmarks (BIG-bench 32, LegalBench 50), and neither carries venue force. A reviewer asserting "n=42 is below the required minimum" would be inventing a rule.
- The enforced obligations that *do* bind T5 are: (a) the counts must appear (ARR B6 — so 194 / 148 / 21 chains / 42 rows / 8 documents / 4 documents all belong in the paper, and they are the author's friend, not the problem); (b) a Limitations section must exist and must be framed as methodological caveats affecting interpretation (ARR CFP + author guidelines); (c) under NeurIPS E&D, the Croissant RAI metadata must document the dataset, and the datasheet questions about "is this a sample of a larger set" and "tasks for which the dataset should not be used" are the natural home for the structural cap.
- The ARR checklist's own sentence — "small differences in accuracy on large test sets may be significant, while on small test sets they may not be" — is the venue's own authority for *not* ranking systems on T5. The author can cite the checklist rather than argue the statistics from scratch.
- Datasheet question 1 ("Does the dataset contain all possible instances or is it a sample...?") is the single best documentation hook for T5: the honest answer is "all possible instances that survive the stated filters," which converts the small n from a sampling weakness into an exhaustiveness claim.

### Gaps
- I did not locate the NeurIPS Datasets & Benchmarks **reviewer** guidelines/review form as a separate document with quotable criteria text; what I verified is the author-facing call. A reviewer-form quote would strengthen the "no minimum exists" claim further.
- The NeurIPS main-track paper checklist (which D&B submissions inherit) was not fetched item-by-item; its experimental-statistics item (error bars / statistical significance) is likely relevant but is not quoted here.
- Bender & Friedman's full prose definition of "curation rationale" was not retrieved (the ACL Anthology PDF did not extract). The v3 element list is sourced from Tech Policy Lab, the authors' own lab page; the TACL paper's v1 wording differs slightly in element names.

---

## Q5. Standard Limitations-section phrasings for an irreducibly rare phenomenon

### Takeaway
I found **verified verbatim caveat sentences from benchmark papers** (below) but did **not** find a harvestable corpus of Limitations-section sentences specifically about "the phenomenon is rare in the world, not under-sampled by us." The honest position: the field's reusable language exists in the diagnostic-set tradition, and the author should adapt those sentences rather than cite a rare-phenomenon template that I cannot evidence.

### Cited Findings (verbatim, verified — safe to quote and cite)
- "The set is provided not as a benchmark, but as an analysis tool for error analysis, qualitative model comparison, and development of adversarial examples." — [GLUE](https://ar5iv.labs.arxiv.org/html/1804.07461)
- "Because the distribution of language is somewhat arbitrary, it will not be helpful to compare performance of the same model on different categories. Rather, we recommend comparing performance that different models score on the same category" — [GLUE](https://ar5iv.labs.arxiv.org/html/1804.07461)
- "Like any diagnostic, Winogender has limitations. It offers only positive predictive value: A poor bias score is clear evidence that a model exhibits gender bias, but a good score does not mean that the model is unbiased." — [SuperGLUE](https://ar5iv.labs.arxiv.org/html/1905.00537)
- slices "are small—and thus not intended for rigorous statistical analysis" — [LegalBench](https://ar5iv.labs.arxiv.org/html/2308.11462)
- "Because 16/17 of our issue-spotting tasks are drawn from one source... average issue performance is skewed by properties of the Learned Hands data distribution." — [LegalBench](https://ar5iv.labs.arxiv.org/html/2308.11462)
- Incompleteness-by-construction framing, verbatim from LegalBench's Limitations: "Legal applications—and what constitutes 'legal reasoning'—is broad. Thus, LegalBench will necessarily be an incomplete effort, and important tasks/document types/reasoning types are not included." — [LegalBench](https://ar5iv.labs.arxiv.org/html/2308.11462)
- "small differences in accuracy on large test sets may be significant, while on small test sets they may not be." — [ARR checklist](https://aclrollingreview.org/responsibleNLPresearch/)
- "we do not believe there exists a universal aggregation that satisfies all preferences, reflects all values, or captures all circumstances appropriately" — [HELM](https://arxiv.org/pdf/2211.09110)

### Cited Findings (weaker sourcing — search snippets only, verify before citing)
- A clinical rare-case retrieval benchmark notes its own temporal fragility: case reports "may no longer satisfy filter criteria as medical knowledge advances, which might make rare cases part of the guideline and reduce the utility of the benchmark over time" — [snippet, "When Cases Get Rare"](https://arxiv.org/pdf/2605.21807)
- A clinical-NLP dataset paper reports frequency imbalance as a stated limitation: "Substantial imbalance exists in phenotype frequencies, with some conditions well-represented while others being extremely rare, which limits the ability to robustly evaluate NLP system performance on rare but clinically important phenotypes." — [snippet, GS-BrainText](https://arxiv.org/pdf/2603.26235)
- A rare-disease prediction paper's caveat on certifying small-n performance: thresholds are "retrospective estimates, not guarantees for new patients", and certifying accuracy on rare cases "would require substantially larger sample sizes" — [snippet, "One Score, Two Decisions"](https://arxiv.org/pdf/2608.14683)
- On why natural-frequency corpora under-serve rare phenomena: "the majority of benchmark datasets in NLP are drawn from text corpora reflecting a natural frequency distribution of language phenomena, and while useful for evaluating system performance in the average case, such datasets may fail to capture a wide range of phenomena" — [snippet, Curriculum benchmark, NAACL 2022](https://arxiv.org/pdf/2204.06283)

### Inferences
- A defensible Limitations paragraph for T5 can be assembled almost entirely from the verified sentences above, recombined. The four moves, in order, each with a precedent: (1) **exhaustiveness, not sampling** — state the corpus census (8 impacting documents → 194 candidates → 4 documents → 148 clean → 21 chains → 42 rows) and that the cap is a property of the corpus, which answers Datasheets Q1 ("all possible instances or … a sample"); (2) **role declaration** — "not a benchmark, but an analysis tool" (GLUE); (3) **direction of inference** — failure on T5 is evidence of a real deficiency, success on T5 is not evidence of competence (the Winogender positive-predictive-value move); (4) **non-aggregation and non-ranking** — reported as a separate column, excluded from the macro average, "not intended for rigorous statistical analysis" (LegalBench), with the ARR checklist's own sentence about small test sets as authority.
- The provenance disclosure matters as much as the size disclosure: LegalBench's "16/17 … drawn from one source" sentence is the template for "T5's 21 chains derive from only 4 impacting documents," and it is the disclosure a reviewer is most likely to demand if the author omits it.
- The given CALRK-Bench (2026) precedent — 8 of 100 temporal-context items concerning statutory amendment, with a disclosed "clarity bias" and exclusion criteria — fits this pattern exactly and is, on the evidence here, *more* generous to the author than the published norm requires: it discloses both the small cell and the selection bias that produced it.

### Gaps
- **No verbatim corpus of "irreducible rarity" Limitations sentences was obtained.** Targeted searches combining "due to the rarity", "small number of instances", "interpret with caution", and "benchmark limitations" returned mostly 2025-2026 arXiv preprints in clinical ML, reachable only as snippets, not ACL-venue benchmark papers. The author should not present snippet-level material as a quoted precedent without fetching the source.
- I did not search ACL Anthology full text systematically (no full-text search endpoint was used); a dedicated Anthology full-text sweep over Limitations sections is the obvious next step and would likely yield the missing verbatim examples.

---

## Q6. The opposite choice: dropping a rare phenomenon and documenting it as out of scope

### Takeaway
Yes — declaring a phenomenon out of scope is fully established practice, and the standard move is to enumerate the exclusions explicitly in the Limitations section rather than to go quiet about them. LegalBench is the cleanest example. The documentation frameworks even provide the dedicated field for it. Note, though, that HELM's philosophy argues the other way: making the gap *visible* in the taxonomy is itself the contribution.

### Cited Findings
- LegalBench's Limitations section is, in form, a list of documented out-of-scope decisions, verbatim: "We note several limitations of our work. Legal applications—and what constitutes 'legal reasoning'—is broad. Thus, LegalBench will necessarily be an incomplete effort, and important tasks/document types/reasoning types are not included. To enumerate a few examples: LegalBench does not include tasks over long documents...LegalBench tasks are skewed towards certain legal domains...LegalBench tasks skew towards US Federal law...LegalBench does not enable evaluation for multilingual, or non-English, legal tasks...LegalBench does not evaluate more subjective legal tasks, or tasks which contain more ambiguity. These tasks are common to the legal field. We hope to work on these limitations as part of future work." — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- LegalBench also records the *cause* of one exclusion (context windows at project inception), i.e. the exclusion is justified by a constraint, not merely asserted — [LegalBench (ar5iv)](https://ar5iv.labs.arxiv.org/html/2308.11462)
- Datasheets provides the designated field for out-of-scope use: "Are there tasks for which the dataset should not be used? If so, please provide a description." — [Datasheets (ar5iv)](https://ar5iv.labs.arxiv.org/html/1803.09010)
- Data Statements schema v3 has a dedicated LIMITATIONS element covering what the dataset does not cover — [Tech Policy Lab](https://techpolicylab.uw.edu/data-statements/)
- The counter-argument from HELM: holistic evaluation should "provide a top-down taxonomy and make explicit all the major scenarios and metrics that are missing", selecting scenarios "based on coverage and feasibility, noting what's missing or underrepresented" — i.e. the missing cell should be *named*, not silently dropped — [HELM](https://arxiv.org/pdf/2211.09110)
- Clinical-NLP example of scope exclusion by category (snippet-level): a brain-imaging report dataset focused on cerebrovascular pathology and common structural abnormalities, "excluding conditions such as infectious processes and traumatic injuries beyond subdural haematoma" — [snippet, GS-BrainText](https://arxiv.org/pdf/2603.26235)
- Linguistic test-suite example of scope exclusion (snippet-level): a Greek NLP test suite focuses "exclusively on standard modern Greek, omitting examples of regional or dialectal language use" — [snippet, OYXOY, EACL 2024](https://arxiv.org/pdf/2309.07009)

### Inferences
- Both options are publishable. The asymmetry is in what each costs: dropping T5 costs the taxonomy a named cell (and under HELM's logic, costs the paper its most interesting negative finding), while keeping it at 42 rows costs only a disclosure paragraph — and the disclosure is mandatory anyway under ARR's Limitations requirement and B6.
- A third option that the precedent supports and that nobody appears to penalise: keep T5 as a named diagnostic set *and* record in the datasheet that it "should not be used" for system ranking or for claims about amendment-handling competence in general. That satisfies Gebru Q3 directly while preserving the cell.
- If the author does drop it, the precedent-compliant form is LegalBench's: a single sentence in Limitations naming the excluded phenomenon, the reason (corpus yields only N instances after filtering), and that it is deferred to future work — not silence.

### Gaps
- I found no paper that explicitly compares the two choices (ship-small vs. drop-and-document) and argues for one. Nothing I retrieved establishes a community preference between them, so the author should present it as a documented design decision rather than appeal to a norm.
