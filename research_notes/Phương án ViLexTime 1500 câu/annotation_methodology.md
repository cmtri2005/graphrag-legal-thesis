# Manual expert annotation methodology for ViLexTime (2 annotators + 1 legal advisor, deadline 16 Nov 2026)

Scope note. These notes cover how to run manual annotation for the rebuilt ViLexTime: about 1,500 question lineages and about 3,300–3,800 rows, with 2 student annotators and a part-time legal advisor, over about 6.5 weeks (2 Oct to 16 Nov 2026). Project context comes from `docs/vilextime-annotation.md` (guideline v1.2) and `scripts/review/crosscheck.py`. Both were read only. The current D4 design is 300 rows: every T5 and T6 row (150 together) plus 50 random rows from each of T2, T3 and T4, drawn by lineage. `crosscheck.py kappa` already reports raw agreement, Cohen κ and Gwet AC1, overall, per group and per lineage. The guideline sets a target of κ ≥ 0.6.

Labelling conventions:
- **Simulation (own computation)** marks results from my own Monte Carlo script, run in the scratchpad. These are not literature values.
- **Not re-fetched** marks a source cited from well-established knowledge that I did not open during this session.

---

## 1. Annotation lifecycle: MATTER, guideline iteration, pilots, calibration, and what top dataset papers do

### Takeaway
Established practice is an iterative, batch-wise cycle: pilot, measure, revise the guideline, then annotate production batches with quality checks after each batch. Expert legal datasets add heavy upfront training, multi-layer review and escalation to a senior lawyer. A 2-person team should run two short pilot rounds stratified by group, with T3 over-sampled, and freeze the guideline before production starts.

### Cited Findings
- MATTER (Pustejovsky & Stubbs 2013) has six steps: Model, Annotate, Train, Test, Evaluate, Revise. "Multiple iterations can be required for defining the tasks, annotations, and evaluations." — [Finlayson & Erjavec, Overview of Annotation Creation (arXiv 1602.05753)](https://arxiv.org/pdf/1602.05753)
- Klie, Eckart de Castilho & Gurevych (2024, *Computational Linguistics* 50(3)) studied 591 dataset papers (314 with human annotation). Their recommendations:
  - "Use an agile, iterative annotation process and annotate in batches"
  - "Conduct pilot studies to validate the annotation setup before starting the actual annotation"
  - "Quality estimates after each batch should guide the improvement of guidelines"
  - annotators "should be trained before and during the annotation process for the best results, even experts"
  
  — [Klie et al. 2024 (arXiv 2307.08153)](https://arxiv.org/abs/2307.08153); [ACL Anthology 2024.cl-3.1](https://aclanthology.org/2024.cl-3.1)
- Klie et al. on pilots: "We recommend that experts or project managers conduct the initial pilot study iterations." Pilot data "should be selected to contain as [many difficult/diverse cases]" (paraphrased; the sentence is truncated in my extract). — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)
- What the field actually does, from Klie et al.'s survey:
  - only 22% of papers mention a pilot study;
  - 22% report an iterative refinement loop;
  - 52% of papers with human annotation report any agreement;
  - 18% report an error rate (mean 8.27%, median 6.0%);
  - in 46% of labelling datasets, adjudication was "not reported clearly or at all";
  - about 30% of studies had "subpar" quality management.
  
  — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)
- **CUAD (legal contracts).**
  - It was "a year-long effort by dozens of law student annotators, lawyers, and machine learning researchers".
  - Annotators attended "70–100 hours of contract review sessions" and followed "more than 100 pages of detailed annotation guidelines". Training included video instruction, live workshops with experienced lawyers, and quizzes.
  - "Each annotation was verified by three additional annotators".
  - Each of the 9,283 pages was reviewed at least 4 times, at 5–10 minutes per page. The value is estimated at over $2M at $500/h.
  
  — [Hendrycks et al. 2021, CUAD (arXiv 2103.06268)](https://arxiv.org/pdf/2103.06268)
- **MAUD (merger agreements).**
  - More than 10,000 hours of work; 70–100 hours of training per law student, with quizzes.
  - Law students worked in teams of three and annotated "collectively, by a consensus". Disagreements were escalated to an experienced M&A lawyer, and "every law student annotation was reviewed by an experienced M&A lawyer".
  - Lawyers "agreed about 80% of the time with student annotations".
  
  — [Wang et al. 2023, MAUD (arXiv 2301.00876)](https://arxiv.org/pdf/2301.00876); [EMNLP 2023](https://aclanthology.org/2023.emnlp-main.1019)
- Klie et al. recommend publishing raw per-annotator labels as well as the adjudicated labels: "For reproducibility, it is suggested to not only publish the adjudicated corpus but also raw annotations by the respective annotators." ViLexTime guideline §5.4 already requires this (ADR 0003 §9). — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)

### Inferences
- MAUD shows that student work under lawyer review is an accepted expert-dataset pattern, but MAUD had far more lawyer time than ViLexTime has. The 80% lawyer–student agreement in MAUD is a useful honest reference: students and experts disagree on about 1 in 5 hard legal items. Expect at least that on T5, T6 and transitional-rule rows, so route those to the advisor.
- Suggested lifecycle for 6.5 weeks (inference; adapts MATTER and Klie et al.):
  1. **Week 1 (2–9 Oct): Model and Pilot 1.**
     - Write guideline v1.3 (or 2.0), adding the new "write or rewrite question" task and decision rules for T3.
     - Pilot 1: about 60 lineages, stratified (about 12 per group, more for T3). Both students annotate blind.
     - Compute agreement, then hold a 1–2 h calibration meeting that walks through every disagreement.
  2. **Week 2 (9–14 Oct): Pilot 2 and freeze.**
     - Run another 40–60 lineages that focus on T3 and on whatever pilot 1 showed to be confusable.
     - The advisor signs off the legal rules (T5 retroactivity, T6 partial repeal, transitional rules).
     - Freeze the guideline version. Later changes create a new version and are logged.
  3. **Weeks 2–5 (14 Oct to about 8 Nov): Production in weekly batches.**
     - Each student annotates their own share.
     - A blind overlap subset is mixed into each batch.
     - Run a weekly agreement and drift check, plus a short weekly sync.
  4. **Weeks 5–6 (about 8–14 Nov): Close-out.**
     - Adjudicate the remaining disagreements and run the error-rate audit on the final data.
     - Freeze the release. Keep 2 days of buffer before 16 Nov.
- Pilot items should not be counted in the reported agreement. Klie et al. imply this: the guideline changes between pilot and production, so pilot agreement measures a different instrument. Report pilot agreement separately as evidence that the guideline improved.

### Gaps
- I could not open the Pustejovsky & Stubbs book itself. The MATTER description comes from a secondary overview.
- ContractNLI's annotation and agreement details were not in the snippets I retrieved ([arXiv 2110.01799](https://arxiv.org/abs/2110.01799)). I found no verified protocol details for LegalBench, COLIEE, MultiEURLEX or CaseHOLD in this session.

---

## 2. Agreement statistics: κ vs AC1 vs α vs raw agreement, the prevalence/bias paradoxes, thresholds, multi-label reasons, item vs lineage

### Takeaway
At a "pass" prevalence of about 85–95%, Cohen κ (and Scott π / Krippendorff α, which use pooled marginals) are mechanically deflated even when annotators agree on 90%+ of rows. Honest reporting therefore needs the full 2×2 table plus several statistics, each with a confidence interval:
- observed agreement;
- positive- and negative-specific agreement (the negative one is agreement on `khong_dat`);
- κ;
- AC1 or PABAK;
- the prevalence and bias indices.

Define the target in advance, justified by the task, rather than by Landis & Koch labels.

### Cited Findings
- **Formulas for 2 raters and 2 categories.**
  - Write A1, B1 for each rater's count of category 1, and N for the number of items.
  - Cohen: e(κ) = (A1/N)(B1/N) + (A2/N)(B2/N), and κ = (p − e)/(1 − e).
  - Gwet AC1: e(γ) = 2q(1 − q), with q = (A1 + B1)/2N, and AC1 = (p − e)/(1 − e).
  
  — [Wongpakaran et al. 2013, BMC Med Res Methodol 13:61](https://pmc.ncbi.nlm.nih.gov/articles/PMC3643869/). The same formulas are implemented in `scripts/review/crosscheck.py` (`cohen_kappa`, `gwet_ac1`).
- **The paradox.** Feinstein & Cicchetti: "a high value of observed agreement can be drastically lowered by substantial imbalance in marginal totals." In Wongpakaran et al.'s data (67 patients, 9 raters), Cohen κ ranged from 0 to 1.00 across criteria while AC1 ranged from .752 to 1.000. AC1 "remained close to the percentage of agreement" as prevalence changed. — [Wongpakaran et al. 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3643869/), citing Feinstein & Cicchetti 1990 ([J Clin Epidemiol 43:543](https://doi.org/10.1016/0895-4356(90)90158-L), not re-fetched)
- **PABAK and the indices (Byrt, Bishop & Carlin 1993).**
  - PABAK "assumes fifty percent prevalence ... and absence of any bias". For 2 categories it equals 2·p_o − 1.
  - Byrt et al. recommend reporting, alongside κ, a bias index BI = (x₁₂ − x₂₁)/N and a prevalence index PI = (x₁₁ − x₂₂)/N.
  - "If the prevalence index is high ... chance agreement is also high and the value of kappa is reduced accordingly."
  - Bias works the other way: "when there is a large amount of bias, kappa is higher".
  
  — [epiR::epi.kappa documentation](https://search.r-project.org/CRAN/refmans/epiR/html/epi.kappa.html); [Chen et al. 2009, BMC Med Res Methodol 9:5](https://pmc.ncbi.nlm.nih.gov/articles/PMC2636838)
- **Positive- and negative-specific agreement.** Cicchetti & Feinstein (1990, part II) proposed resolving the paradoxes by reporting p_pos = 2a/(2a + b + c) and p_neg = 2d/(2d + b + c) next to κ. Here a = both pass, d = both fail, and b, c = the two kinds of disagreement. — [Cicchetti & Feinstein 1990, J Clin Epidemiol 43:551](https://doi.org/10.1016/0895-4356(90)90159-M) (not re-fetched)
- **Gwet AC1 and its variance.** Gwet's original paper is [Gwet 2008, BJMSP 61:29–48, "Computing inter-rater reliability and its variance in the presence of high agreement"](https://doi.org/10.1348/000711006X126600). Not re-fetched: the agreestat PDF returned 404.
- **Klie et al. on thresholds and coefficients.**
  - They list Landis & Koch (0.61–0.80 "substantial", 0.81–1.00 "almost perfect") and Krippendorff (α ≥ 0.8 reliable, later called "the absolute lower limit and should better be 0.9"; 0.667–0.8 only "tentative conclusions").
  - They warn: "those boundaries are arbitrary ... and have no theoretical foundation" and "Using thresholds from the literature like the ones from Landis and Koch (1977) is not recommended".
  - "The agreement value targeted should be chosen beforehand", for example from a pilot expert study.
  - They recommend Krippendorff α "in almost all circumstances". Cohen κ "can additionally be used" when every item has the same two annotators.
  - "Percent agreement should rarely be used and never the only employed agreement measure."
  - "Confidence intervals should be employed", closed-form or by bootstrap.
  - Common errors they found: κ reported in percent, Cohen κ used with more than 2 annotators, and correlation used as agreement (2% of papers).
  - They note that "annotations with near-perfect percent agreement can have low Cohen's κ".
  - Artstein & Poesio (2008) "state that these limits work well in their experience".
  
  — [Klie et al. 2024](https://arxiv.org/abs/2307.08153); [Artstein & Poesio 2008, CL 34(4)](https://aclanthology.org/J08-4004/)
- McHugh (2012) argues that Cohen's and Landis & Koch's scales are too lenient for health research. She treats κ < 0.60 as inadequate and maps κ bands to a share of "reliable data" (κ > 0.90 → 82–100%). — [McHugh 2012, Biochemia Medica 22(3):276](https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052)
- Klie et al. recommend computing agreement "per label" and "pairwise", and visualising disagreements with confusion matrices, "to identify ... particularly difficult-to-decide labels". — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)
- **Set-valued (multi-label) codes.** MASI distance (Passonneau 2006) lets Krippendorff α be computed on set-valued labels such as `reasons`. NLTK implements `masi_distance` and `AnnotationTask`. — [Passonneau 2006, LREC](http://www.lrec-conf.org/proceedings/lrec2006/pdf/636_pdf.pdf); [NLTK metrics.distance](https://www.nltk.org/api/nltk.metrics.distance.html) (not re-fetched)

**Simulation (own computation):** how big the paradox is for ViLexTime-like numbers.
- Model: the latent true "pass" rate is π, and each annotator independently flips the true label with probability e.
- At π = 0.90 and e = 0.05:
  - observed agreement p_o = 0.905
  - κ = 0.605 (because chance agreement e_κ = 0.759)
  - AC1 = 0.875
  - PABAK = 0.81
  - p_pos = 0.945
  - p_neg = 0.66
- At π = 0.95 and e = 0.05:
  - p_o stays at 0.905
  - κ falls to 0.448
  - AC1 = 0.885
- So κ can fall below the guideline's 0.6 target purely because prevalence rose, with no change in annotator quality.
- Script: `scratchpad/kappa_sim.py`.

### Inferences
- **Recommended reporting block** for the thesis, per stratum (group) and overall:
  1. the 2×2 table (dat/dat, dat/khong_dat, khong_dat/dat, khong_dat/khong_dat);
  2. p_o;
  3. p_pos and p_neg;
  4. κ with 95% CI;
  5. AC1 (or PABAK) with 95% CI;
  6. PI and BI;
  7. n items and n lineages.
  
  Put p_neg in the headline. It answers the benchmark-relevant question directly: "when one annotator flags a row as defective, does the other also flag it?" Do not present AC1 alone. It has critics (see Gaps), and reviewers often see AC1-only reporting as threshold-shopping.
- **Krippendorff α** for 2 coders with nominal labels and no missing data is essentially Scott π with a small-sample correction. It therefore uses pooled marginals and is deflated by prevalence just like κ. This is my inference from the definitions. Report it if a reviewer expects it, but it does not solve the prevalence problem.
- **Target.** Pre-register the target in the guideline before production, for example "AC1 ≥ 0.80 and p_neg ≥ 0.6, with κ reported for transparency". Justify it from pilot results and cite Klie et al.'s advice against Landis & Koch. The current "κ ≥ 0.6" target in the guideline is fragile at this prevalence: the simulation shows true κ ≈ 0.45–0.6 for annotators who each err only 5% of the time.
- **Reason codes (multi-label).** Use three layers.
  1. Treat each code as a binary per-row label ("did the annotator use `gold_wrong`?"). Report per-code p_pos (agreement on presence), because codes are rare and κ is meaningless at near-zero prevalence.
  2. Report conditional agreement on rows that both annotators marked `khong_dat`: exact-set match, and Krippendorff α with MASI distance.
  3. Give a confusion matrix between codes, to find codes that annotators confuse, for example `group_mismatch` vs `question_ambiguous`.
  
  Exclude `meta_issues` from agreement, as the guideline already does.
- **Item vs lineage level.** Rows in a lineage share the question, so their verdicts are not independent. Report:
  - row-level statistics with a **lineage-clustered bootstrap CI** (resample lineages, not rows);
  - lineage-level agreement, with the lineage counted as `khong_dat` if any row is (`crosscheck.py` already does this).
  
  Unclustered row-level CIs are too narrow. The effective n is somewhere between the number of lineages and the number of rows.

### Gaps
- I could not verify a published critique of AC1 in this session. A critique exists (I recall Vach & Gerke 2023, MethodsX, "Gwet's AC1 is not a substitute for Cohen's kappa"), but the search failed, so treat it as unverified.
- I did not find a source that explicitly compares α and AC1 under prevalence skew in NLP annotation. The α ≈ π equivalence above is my inference.

---

## 3. Sample size: how many double-annotated items for a given CI half-width at prevalence about 0.9

### Takeaway
At pass prevalence about 0.9 with good annotators:
- **κ ± 0.10 needs about 570–600 independent items, and κ ± 0.05 needs about 2,300.**
- **AC1 ± 0.10 needs about 60–70, and AC1 ± 0.05 needs about 230–270.**

So the planned 300 double-annotated rows give roughly κ ± 0.13 and AC1 ± 0.05 overall. Per-group subsets of 50–60 give κ ± 0.3, which is essentially uninformative, and AC1 ± 0.11. Klie et al. recommend at least about 500 double-annotated items, with the sample size justified by a CI calculation.

### Cited Findings
- **Klie et al. on agreement subsets.**
  - "For a reliable estimate, agreement should be either computed on the whole dataset, or a sufficiently large (⪆ 500 instances) subset should be annotated by multiple annotators. Subset sample sizes should be statistically grounded ... and justified."
  - Of 91 papers that computed agreement on a subset, the median subset was 200; 51% used ≤ 200 items and 28% used ≤ 100.
  - "We did not find any work that based their choice of sample size on a statistical footing."
  
  — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)
- **Klie et al. on error-rate audits.** "We suggest inspecting at least 500 instances ... or the whole dataset", and report a binomial CI. Footnote: a true error rate of 5% with n = 456 gives a 95% CI half-width of about 0.02. Their cautionary case: TACRED's 300-item audit estimated about 6.7% errors, while a full re-inspection later found 23.9%. — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)
- Klie et al. cite Shoukri, Asyali & Donner (2004) and Sim & Wright (2005) for the warning that an agreement value computed on too small a sample "might have only limited explanatory power". — [Klie et al. 2024](https://arxiv.org/abs/2307.08153); Sim & Wright 2005, [Phys Ther 85(3):257](https://doi.org/10.1093/ptj/85.3.257) (not re-fetched)
- **Donner & Eliasziw goodness-of-fit method.** It sizes a study from a CI perspective, given:
  - an anticipated κ₀;
  - the desired lower and upper CI limits;
  - the anticipated prevalence;
  - 2–6 raters.
  
  It is implemented in R `kappaSize::CIBinary(kappa0, kappaL, kappaU, props, raters, alpha)` (assumes equal marginals). The package's own example is `CIBinary(kappa0=0.4, kappaL=0.3, kappaU=0.5, props=0.30)`. — [kappaSize CIBinary docs](https://search.r-project.org/CRAN/refmans/kappaSize/html/CIBinary.html); Donner & Eliasziw 1992, Stat Med 11:1511 (not re-fetched)
- **Closed-form approximation (large-sample, ignores variance of the chance term):**

  SE(κ) ≈ √(p_o(1−p_o)/n) / (1 − p_e), which gives **n ≈ z² · p_o(1−p_o) / (h² · (1 − p_e)²)**.

  The same expression works for AC1, with p_e = 2q(1−q).
  - With p_o = 0.905, p_e(κ) = 0.759 and p_e(AC1) = 0.241:
    - h = 0.10 → n_κ ≈ 570, n_AC1 ≈ 57
    - h = 0.05 → n_κ ≈ 2,280, n_AC1 ≈ 230
  - This is my own computation from the standard Cohen (1960) large-sample SE. Gwet's (2008) variance formula is the proper one for AC1.

**Simulation (own computation): 95% interval half-widths, 20,000 replicates, independent rows.** Script: `scratchpad/kappa_sim.py`. π is the true pass rate; e is each annotator's independent error rate.

| π (true pass) | e | n | true κ | κ half-width | true AC1 | AC1 half-width |
|---|---|---|---|---|---|---|
| 0.90 | 0.05 | 60 | 0.605 | ±0.31 | 0.875 | ±0.11 |
| 0.90 | 0.05 | 150 | 0.605 | ±0.19 | 0.875 | ±0.07 |
| 0.90 | 0.05 | 300 | 0.605 | ±0.13 | 0.875 | ±0.047 |
| 0.90 | 0.05 | 600 | 0.605 | ±0.09 | 0.875 | ±0.034 |
| 0.90 | 0.05 | 1000 | 0.605 | ±0.07 | 0.875 | ±0.026 |
| 0.90 | 0.03 | 300 | 0.732 | ±0.12 | 0.926 | ±0.036 |
| 0.90 | 0.10 | 300 | 0.390 | ±0.13 | 0.745 | ±0.07 |
| 0.85 | 0.05 | 300 | 0.685 | ±0.11 | 0.864 | ±0.05 |
| 0.95 | 0.05 | 60 | 0.448 | ±0.42 | 0.885 | ±0.10 |
| 0.95 | 0.05 | 300 | 0.448 | ±0.17 | 0.886 | ±0.044 |
| 0.95 | 0.05 | 600 | 0.448 | ±0.12 | 0.885 | ±0.031 |

**Negative-specific agreement p_neg (agreement on `khong_dat`), same model** (script: `scratchpad/pneg_sim.py`):

| π | e | n | p_neg (median) | 95% half-width | median number of disagreeing rows | median rows both failed |
|---|---|---|---|---|---|---|
| 0.90 | 0.05 | 60 | 0.67 | ±0.29 | 6 | 5 |
| 0.90 | 0.05 | 300 | 0.66 | ±0.12 | 28 | 28 |
| 0.90 | 0.05 | 600 | 0.66 | ±0.08 | 57 | 55 |
| 0.85 | 0.05 | 300 | 0.74 | ±0.09 | 28 | 41 |

### Inferences
- **Recommendation (inference):** double-annotate about 600 rows, which is about 250–280 lineages and about 17% of the data.
  - **Stratified by group**, roughly 110–130 rows per group. The 5-group design (300 lineages per group) makes this about 50–55 lineages per group.
  - **Hard cases on top of that:** every T3 row is in a double-annotated lineage only if the budget allows; otherwise over-sample T3 to about 150 rows because of the earlier disagreement.
  - Overall this gives κ about ±0.09, AC1 about ±0.035 and p_neg about ±0.08. That meets Klie et al.'s "⪆ 500".
  - Per group (about 120 rows) it gives AC1 about ±0.08 and κ about ±0.2. **Report per-group statistics descriptively, with CIs. Do not claim per-group reliability levels from κ.**
- **The existing D4 set (300 rows: all T5 and T6, plus 50 each from T2–T4)** is not proportional to the release. An overall κ on it is a mix weighted toward T5/T6. Report per stratum and a release-weighted overall value, or state the sampling design explicitly.
- **The overlap set must be random within strata and blind to annotators** (they should not know which rows are double-annotated). Otherwise it is not representative of the single-annotated rest.
- The half-widths above assume independent rows. With lineages of 2–4 correlated rows, real CIs from a lineage-clustered bootstrap will be wider. Plan on about 10–30% wider; this is a guess and the true design effect depends on within-lineage correlation. Simulating or bootstrapping the actual data is the authoritative check.
- Error rate is different from agreement. After adjudication, inspect a random sample of at least about 300–500 final items for correctness (Klie et al.) and report the binomial CI. With n = 400 and an observed 5% error rate, the exact 95% CI is about ±2.2 points. Part of this audit can be done by the student who did *not* annotate the item, with the advisor checking only the flagged and legal rows.

### Gaps
- I did not find a published sample-size table for AC1 specifically (Gwet's book has one, but I did not access it). The AC1 numbers here come from my own simulation and the delta approximation.
- I did not run `kappaSize::CIBinary` itself (R was not used). Its numbers will differ somewhat because it assumes equal marginals and a different CI method.

---

## 4. Single vs double annotation under a budget

### Takeaway
Full double annotation is the gold standard but rarely affordable. The literature supports a cheaper middle path: single annotation plus a random double-annotated subset (for agreement) plus targeted second review of the items most likely to be wrong (for quality). Dligach & Palmer show that targeted selection can cut the second round by more than half with almost no loss.

### Cited Findings
- Dligach & Palmer (2011), "Reducing the Need for Double Annotation", on OntoNotes word-sense data:
  - "it is possible to reduce the amount of the second round of annotation by more than half without sacrificing the performance."
  - Their best selector "detects 75% of the errors". It reached 83.82% accuracy against 84.15% for full double annotation and 82.84% for single annotation only, with a 54% reduction in second-round annotation.
  - In one selector, 16.93% of items were flagged and they contained 60.32% of all single-annotation errors. A random draw of the same size recalled 16.79%.
  - About 7% of first-annotator labels were errors.
  
  — [Dligach & Palmer 2011, LAW V (W11-0408)](https://aclanthology.org/W11-0408)
- Dligach, Nielsen & Palmer (2010), "To Annotate More Accurately or to Annotate More", LAW IV, studies the quantity-vs-quality trade-off. — [W10-1808](https://aclanthology.org/W10-1808) (title only seen; content not verified)
- Klie et al.: "collecting more than one label per instance needs to be weighed against annotating more instances when working on a limited budget". Manual adjudication by domain experts is "slow and expensive" but gives high quality. Curation "can be sped up ... by automatically merging instances for which there is no disagreement". — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)
- Snow et al. (2008): for affect recognition, about 4 non-expert labels per item matched expert quality. This is relevant only as evidence that redundancy can substitute for expertise; it is not directly comparable to legal QA. — [Snow et al. 2008, EMNLP (D08-1027)](https://aclanthology.org/D08-1027/) (not re-fetched)
- Northcutt, Athalye & Mueller (2021) estimated an average of 3.3% test-set label errors across 10 benchmark datasets (6% in the ImageNet validation set). Only 54% of algorithmically flagged candidates were confirmed as errors by humans. With corrected labels, model rankings can flip; for example, ResNet-18 beats ResNet-50 if mislabelled test examples increase by just 6%. — [Northcutt et al. 2021, NeurIPS (arXiv 2103.14749)](https://arxiv.org/abs/2103.14749)
- The legal-dataset precedents both used heavy redundancy:
  - CUAD: each annotation verified by 3 more annotators. — [CUAD](https://arxiv.org/pdf/2103.06268)
  - MAUD: three-student consensus plus review by a lawyer. — [MAUD](https://arxiv.org/pdf/2301.00876)

### Inferences
- **Proposed design for ViLexTime** (inference, combining the above):
  1. **Single annotation** of every lineage by one student.
  2. **Blind random overlap** of about 600 rows (Section 3) for the agreement statistics.
  3. **Targeted second review** of every row the first annotator marked `khong_dat` or "unsure", and of every row flagged by `check_validity.py` or by the earlier LLM pass. This is Dligach-style selection: errors concentrate in flagged rows.
  4. **Advisor adjudication** only for the legal categories (Section 8).
  
  Because about 85–95% of rows pass, the second-review queue (fails, unsure and flags) is probably 15–30% of rows. That is affordable.
- A benchmark test set needs label quality more than label quantity. Northcutt et al. show that 3–6% error can change model rankings. So spend the margin on the second review of flagged items, and on the post-adjudication error audit, rather than on more lineages beyond 1,500.
- Use the earlier LLM pre-labels only as a **selection signal for second review**, never shown during first-pass annotation of the agreement subset (see Section 6).

### Gaps
- I found no study that measures the single- vs double-annotation trade-off specifically for expert legal verification tasks.

---

## 5. Throughput and workload for about 3,500 rows in 6.5 weeks

### Takeaway
Published legal-expert timings range from about 3–4 minutes per QA item (expert review of LegalBench answers) to 5–10 minutes per contract page (CUAD), and up to hours per item for rubric-heavy tasks. A realistic ViLexTime budget is about 2–4 minutes per row when the source is not opened and 6–10 minutes when the amending documents must be checked. Writing or rewriting a question costs about 5–12 minutes per lineage. The row-based model in the table below totals **about 305–560 student-hours plus about 12–20 advisor-hours**. The per-lineage discount and targeted review bring this down to about 265 h at the low end. Capacity is only about 260–325 person-hours, so the plan fits only the low scenario.

### Cited Findings
- "A manual review by a human legal expert of the LegalBench dataset would take a little under eight hours, with around 3 to 4 minutes on average spent per question." This was in the context of evaluating 150 LegalBench QA pairs for correctness and relevance. — [LeMAJ (arXiv 2510.07243)](https://arxiv.org/abs/2510.07243)
- CUAD: each page required 5–10 minutes, and each of the 9,283 pages was reviewed at least 4 times. — [CUAD](https://arxiv.org/pdf/2103.06268)
- PLawBench reports an average of about three hours of expert annotation per data instance for rubric-based legal-practice tasks. This comes from a search snippet and was not verified in full text. — [PLawBench (arXiv 2601.16669)](https://arxiv.org/abs/2601.16669)
- MAUD: more than 10,000 hours in total for more than 39,000 examples and 47,000 annotations, with 70–100 training hours per student. — [MAUD](https://arxiv.org/pdf/2301.00876)
- Klie et al. found 11 papers whose filtering relied on "unsound, improbably low annotation times". Logging per-item time is a known quality signal. — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)

**Workload model (inference; every per-item time is an assumption to be replaced by pilot measurements):**

| Activity | Volume | Minutes per unit (low–high) | Hours (low–high) |
|---|---|---|---|
| Pilot rounds (2 rounds, both annotators, plus calibration meetings) | ~110 lineages × 2 people ≈ 500 row-judgements | 3–5 | 25–40 (incl. ~6 h meetings) |
| First-pass verification, rows not needing source lookup | ~70% of ~3,500 = 2,450 rows | 2–3 | 80–120 |
| First-pass verification, rows needing source/amending-document check (T2/T4 "before" side, T5, T6, transitional rules) | ~30% = 1,050 rows | 6–10 | 105–175 |
| Second annotation of the blind overlap set | ~600 rows | 3–5 | 30–50 |
| Writing or rewriting questions (assume 15–25% of lineages fail or need a rewrite) | 225–375 lineages | 6–12 | 25–75 |
| Student-side adjudication of disagreements and flagged rows (both students together) | ~150–250 rows | 5–8 (× 2 people) | 25–65 |
| Post-adjudication error audit (cross-checking the other student's rows) | 300–500 rows | 3–4 | 15–35 |
| **Student total** | | | **≈ 305–560 person-hours** |
| Advisor: guideline sign-off, 2 calibration sessions, legal adjudication of ~60–100 rows, spot audit | | 6–10 per row | **≈ 12–20 hours** |

The low end assumes the "lineage discount" described next is achieved.

- **Lineage discount.** The question is shared across a lineage, so the 2nd–4th rows cost less than the first. A per-lineage view: about 5–8 minutes for 2-row lineages (1,200 of them, so 100–160 h) and about 9–14 minutes for T3 (300 lineages, so 45–70 h). That gives about 145–230 h for first-pass verification, which is close to the row-based figure.
- **Capacity.** 2 students × 6.5 weeks × 20 focused annotation hours per week = 260 person-hours (or 2 × 6.5 × 25 = 325). That **covers the low-to-middle scenario only**.

### Inferences
- The plan is feasible only if:
  1. per-row time is measured in pilot 1 and the plan is re-budgeted;
  2. second review is targeted, not universal (Section 4);
  3. question rewriting is capped. Dropping a lineage and drawing a replacement from the surplus pool is often cheaper than rewriting.
- Measure time per row in both pilots (start and stop timestamps in the sheet). Use the median from pilot 2, after the learning effect, as the production rate. Use the pilot to decide whether 1,500 lineages are reachable. If the median is above about 4 minutes per row, cut the target before cutting the double-annotation subset.
- Fatigue and drift (opinion, not sourced): cap sessions at about 90–120 minutes with breaks, and at about 4–5 focused hours per day.

### Gaps
- I found no published per-item timing for verifying statutory-version QA (date-dependent legal text with amending documents), and none for Vietnamese legal text. All ViLexTime times above are assumptions.
- The LeMAJ timing is for answer-correctness review of LegalBench, not for constructing LegalBench.

---

## 6. Bias risks: LLM pre-annotation and anchoring, fatigue and drift, annotators as authors

### Takeaway
Showing model labels to annotators measurably shifts human labels toward the model. It also inflates the reported model performance on data created that way. Keep the agreement set fully blind to model labels, randomise order, inject control items and repeated items, never let a person verify a question they wrote, and disclose authorship and expertise in the datasheet.

### Cited Findings
- **Schroeder et al. (ACL Findings 2025).** Pre-registered, with 350 annotators and 7,000 annotations across 4 conditions.
  - LLM suggestions "did not make them faster annotators, but did improve their self-reported confidence".
  - "Annotators strongly took the LLM suggestions, significantly changing the label distribution".
  - When LLM-assisted labels are used to evaluate LLMs, "reported model performance significantly increases".
  
  — [Schroeder et al. 2025 (arXiv 2507.15821)](https://arxiv.org/abs/2507.15821)
- Choi et al. (2024), "The LLM Effect": agreement between expert annotations and LLM annotations rose from 43.9% (control) to 71.5% (with LLM suggestions). "Experts tended to heavily align with and be biased by the LLM's initial suggestions." — [Choi et al. 2024 (arXiv 2410.04699)](https://arxiv.org/abs/2410.04699)
- Beck (2025, LMU dissertation): with pre-annotations framed as AI-generated, adjudicators "who reported greater skepticism toward AI were more accurate". — [Beck 2025](https://edoc.ub.uni-muenchen.de/36241/)
- Klie et al. recommend injecting control instances "for measuring individual annotator performance and batch quality". They also note that when project managers annotate pilots, "they may use implicit knowledge" that the written guideline does not contain. — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)
- **Disclosure standards.**
  - Datasheets for Datasets asks who was involved in data collection (for example students), how they were compensated, and what review processes were applied. — [Gebru et al. (arXiv 1803.09010)](https://arxiv.org/abs/1803.09010) (not re-fetched)
  - Data Statements asks for annotator demographics and expertise. — [Bender & Friedman 2018, TACL (Q18-1041)](https://aclanthology.org/Q18-1041/) (not re-fetched)
- Project status: guideline §6.4 already states that the model wrote the questions, so its own pass rate is an upper bound. §6.1 keeps model labels out of the κ set until both humans have labelled. — `docs/vilextime-annotation.md`

### Inferences
- **Anchoring.**
  - Hide the model's verdict and reasons during first-pass human annotation of every row, not only the κ set. Reveal them only at adjudication, as a flag.
  - If a model output must be shown (for example, a suggested legal citation for T5), show the evidence text, not the verdict. Record which rows were shown model output.
  - Schroeder et al. imply that a "human-approved" LLM-labelled set will overstate model performance on ViLexTime. Disclose this.
- **If annotator A is now an LLM panel** (project memory, 2 Oct):
  - κ between model and human is *model–human agreement*. It is not inter-annotator reliability among humans and cannot be reported as such.
  - The guideline's §6.1 rule, "κ is always between two humans", would then need an explicit decision.
  - The honest framing is "one human annotator plus model agreement plus expert adjudication". Report the human–model agreement as a secondary analysis.
- **Annotators as authors.**
  - When the students write or rewrite a question, the *other* student verifies it (cross-assignment). This works like a separation-of-duties rule.
  - Rewritten lineages carry `question_by: human:<code>`. Report agreement separately for model-written and human-written questions.
  - Disclose in the datasheet that the annotators are the dataset authors and thesis authors, that they are not lawyers, and what the advisor's credentials and hours were.
  - Report the advisor's agreement with the students on the rows the advisor reviewed, as MAUD reported its ~80% lawyer–student agreement.
- **Fatigue and drift.**
  - Randomise lineage order across groups within each batch (`crosscheck.py build` already shuffles lineages).
  - Re-insert about 3–5% of earlier rows unannounced to measure intra-annotator consistency over time.
  - Seed about 20–40 control items with known defects (for example a deliberately wrong gold version, or a leaked "Điều" number). Measure each annotator's defect recall. At 85–95% pass prevalence, defect recall is the quality number that matters most.
  - Plot weekly p_neg, fail rate and median time per row per annotator. A falling fail rate together with falling time per row is the classic fatigue signature.

### Gaps
- I found no study of anchoring specifically in legal annotation, or with Vietnamese annotators.
- I did not verify how large drift effects are in expert annotation over multi-week projects.

---

## 7. Tooling for a 2-person team with Vietnamese text and side-by-side source documents

### Takeaway
For a closed-label, row-level verification task like ViLexTime, the lowest-risk option is the existing TSV pipeline: `crosscheck.py` build/kappa plus `labels.py`, opened as a spreadsheet with locked columns and data validation. A full annotation server earns its setup cost only if it is needed to enforce blind overlap or to show the source documents side by side. Of the servers, Argilla has built-in overlap distribution, and Label Studio and INCEpTION are heavier.

### Cited Findings
- **Argilla (v2).** `TaskDistribution(min_submitted=2)` makes each record require 2 submissions. Completed records then leave the pending queue of every team member. Argilla v1's metrics module offered only Krippendorff α. — [Argilla distribution guide](https://docs.argilla.io/v2.0/how_to_guides/distribution/); [Argilla annotation metrics (v1)](https://docs.argilla.io/en/latest/reference/python/python_annotation_metrics.html)
- **doccano** supports classification, sequence labelling and seq2seq. It "admits multiple users, but apart from that there are no additional features for collaborative labeling". **INCEpTION** "is a more heavyweight tool ... can handle both text files and PDFs" and is highly configurable. **Label Studio** integrates ML-model predictions into the annotation UI. — [dida.do comparison of free text annotation tools](https://dida.do/blog/the-best-free-labeling-tools-for-text-annotation-in-nlp)
- INCEpTION was designed for "machine-assisted and knowledge-oriented interactive annotation" and has a curation workflow. — [Klie et al. 2018, COLING demo (C18-2002)](https://aclanthology.org/C18-2002/)
- Showing model predictions in the UI (a Label Studio feature) is exactly the anchoring risk described in Section 6. — [Schroeder et al. 2025](https://arxiv.org/abs/2507.15821)

### Inferences
- **Recommendation (inference, ponytail-consistent):** keep spreadsheets plus scripts.
  - The project already has deterministic builders (`crosscheck.py build` writes A/B files with shuffled lineages and refuses to overwrite labelled files), agreement computation (κ, AC1, per group and per lineage) and an append-only label log with provenance (`labels.tsv`, `labeler`, guideline version).
  - Add only:
    1. data-validation dropdowns for `verdict` and `reasons`, and locked question and answer columns;
    2. per-annotator files generated by script, so the overlap set is hidden in the normal flow;
    3. a `minutes` or start/stop column for throughput;
    4. a `source_url` hyperlink, plus the consolidated-text link, opened in a second window for side-by-side reading.
  - Vietnamese text is plain UTF-8 and is not a problem for spreadsheets or any of these tools.
- **Where a server tool fits:**
  - Choose Argilla if you need enforced overlap or a web UI that a third party can use.
  - Choose INCEpTION if annotators must highlight evidence spans in the source document PDFs (span-level `accepted_evidence`).
  - Neither is needed for verdict and reason labelling.
- Whatever the tool, do not render model verdicts in the annotator view.

### Gaps
- I did not verify which Label Studio quality features (agreement matrix, overlap distribution) are open-source and which are Enterprise-only. The docs page redirected and was not fetched.
- I did not verify INCEpTION's built-in agreement coefficients in its current user guide.

---

## 8. How to use the legal advisor's time, and how to report expert involvement

### Takeaway
Advisor time is the scarcest resource, so use it where legal expertise changes the label and where students are least reliable:
- signing off the guideline's legal rules;
- calibration sessions;
- adjudicating legally contested rows (T5 retroactivity, T6 and ancestor repeal, transitional rules, `gold_wrong` disputes);
- a small blind spot-audit that yields an expert-agreement number.

Report hours, credentials, which rows the advisor touched, and the advisor's agreement with the students.

### Cited Findings
- **MAUD:** unresolved student disagreements were escalated to an experienced M&A lawyer, and every student annotation was lawyer-reviewed. Lawyers agreed with students about 80% of the time. — [MAUD](https://arxiv.org/pdf/2301.00876)
- **CUAD:** training came from experienced lawyers (videos, workshops, quizzes), and the guidelines ran to more than 100 pages. — [CUAD](https://arxiv.org/pdf/2103.06268)
- **Klie et al.:** "expert curation or majority voting with experts breaking ties can be used to create a high-quality gold standard". The final error-rate check should be done by experts: "it is crucial to have experts check the actual percentage of errors". — [Klie et al. 2024](https://arxiv.org/abs/2307.08153)
- **Project rule:** legal judgments (Điều 152 retroactivity for T5, transitional provisions) are decided by the advisor in the `LUẬT SƯ:` columns of `data/review/t5_documents.tsv` and `t5_items.tsv`. The model only proposes them, with a quoted citation. — `docs/vilextime-annotation.md` §6

### Inferences
- **Suggested advisor budget, about 12–20 h** (inference):

| Task | Hours |
|---|---|
| Review and sign off the legal sections of the guideline (before production) | 2–3 |
| Two calibration sessions with both students, on pilot disagreements and T3/T5/T6 examples | 2–4 |
| Legal adjudication queue, about 60–100 rows at 6–10 min each (T5, T6/ancestor repeal, transitional rules, `gold_wrong` disputes the students cannot resolve) | 6–12 |
| Blind spot-audit of about 50–100 random final rows, stratified by group, to report expert–student agreement and an expert-estimated error rate | 3–5 |

- Batch the advisor's queue weekly, with each row prepared in advance (question, as_of, gold, links to source and amending documents, and both students' notes). The advisor then spends time on judgement, not on lookup.
- **Adjudication protocol** (inference, consistent with guideline §5):
  1. Each annotator labels independently.
  2. The script lists disagreements.
  3. The two students discuss and reconcile non-legal disagreements (wording, leaks, ambiguity). They record the reconciled label and the reason, and keep the raw labels.
  4. Legal disagreements, and any reconciled row that still carries `gold_wrong` or `transitional_rule`, go to the advisor, whose decision is final.
  5. Record who decided each final label (`adjudicated_by`) and keep every raw label in the release.
  6. Report the agreement statistics on the **raw pre-adjudication** labels, not on post-discussion labels.
- **Reporting expert involvement** in the thesis and datasheet:
  - advisor credentials and affiliation;
  - total advisor hours;
  - the number and share of rows the advisor adjudicated or audited, by group;
  - advisor–student agreement on the audited sample, with CI;
  - the explicit statement that the annotators are non-lawyer students who are also the authors.
  
  With about 50–100 audited rows, the CI on advisor–student agreement is wide, about ±0.06–0.10 at 85–90% agreement. Say so.

### Gaps
- I found no published norm for the minimum share of rows that a legal expert must review before a dataset can be called "expert-annotated". MAUD (100% lawyer review) and CUAD (multiple verification passes) are well above what this project can afford, so state the coverage plainly instead of using the label.
