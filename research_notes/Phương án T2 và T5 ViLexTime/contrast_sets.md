# Contrast sets / minimal pairs / counterfactually-augmented data: construction protocols and paired reporting

Scope note on verification level, used throughout:
- **[full-text]** = I read the paper PDF/HTML myself in this session and the quote is verbatim.
- **[abstract/page]** = I read only the landing page or abstract.
- **[snippet]** = the claim comes from a search-engine summary of a source I did not open; treat as a lead to verify, not as a citable fact.

---

## Q1. Gardner et al. 2020 — construction protocol, metric name, exact definition, reported numbers

### Takeaway
The metric is called **contrast consistency**, and it is defined as the model being correct on *every* element of a contrast set (original pivot included). For a two-element group (original + one perturbation) it is literally "correct at both members of the pair" — i.e. the benchmark author's TCS is contrast consistency with |C(x)| = 1 perturbation, and Gardner et al. 2020 is its origin citation. Construction is **expert, author-written, model-free, ~1,000 examples per dataset, 1–5 items per set**.

### Cited findings

**Citation.** Matt Gardner, Yoav Artzi, Victoria Basmov, Jonathan Berant, Ben Bogin, Sihao Chen, Pradeep Dasigi, Dheeru Dua, Yanai Elazar, Ananth Gottumukkala, Nitish Gupta, Hanna Hajishirzi, Gabriel Ilharco, Daniel Khashabi, Kevin Lin, Jiangming Liu, Nelson F. Liu, Phoebe Mulcaire, Qiang Ning, Sameer Singh, Noah A. Smith, Sanjay Subramanian, Reut Tsarfaty, Eric Wallace, Ally Zhang, Ben Zhou. 2020. *Evaluating Models' Local Decision Boundaries via Contrast Sets.* Findings of the Association for Computational Linguistics: EMNLP 2020, pages 1307–1323. DOI 10.18653/v1/2020.findings-emnlp.117 — [ACL Anthology](https://aclanthology.org/2020.findings-emnlp.117/) [abstract/page]

**Definitions (verbatim, §2.2 "Definitions").** [full-text, arXiv:2004.02709v2]
- Local decision boundary: "A **local decision boundary** around some **pivot** x is the set of all points x′ and their associated labels y′ that are within some distance ε of x. That is, a local decision boundary around x is the set {(x′, y′) | d(x, x′) < ε}." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- Contrast set: "A **contrast set** C(x) is any sample of points from a local decision boundary around x. In other words, C(x) consists of inputs x′ that are similar to x according to some distance function d. Typically these points are sampled such that y′ ≠ y." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- **Contrast consistency (the metric, verbatim):** "To evaluate a model using these contrast sets, we define the **contrast consistency** of a model to be whether it makes correct predictions ŷ on every element in the set: all({ŷ = y′ ∀(x′, y′) ∈ C(x)})." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- **Operational definition (verbatim, Table 2 caption):** "We also report *contrast consistency*: the percentage of the '# Sets' contrast sets for which a model's predictions are correct for all examples in the set (*including* the original example)." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)

**Construction protocol (verbatim fragments).** [full-text]
- "after a dataset is constructed, we recommend that the dataset authors manually perturb the test instances in small but meaningful ways that (typically) change the gold label, creating *contrast sets*." (abstract) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- "These perturbations should be small, so that they preserve whatever lexical/syntactic artifacts are present in the original example, but change the true label. They should be created *without* a model in the loop, so as not to bias the contrast sets towards quirks of particular models." (§1) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- "The contrast sets were constructed by NLP researchers who were deeply familiar with the phenomena underlying the annotated dataset; in most cases, these were the original dataset authors. Our contrast sets consist of up to about 1,000 total examples and average 1–5 examples per contrast set." (§4.2) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- "We recommend that the dataset authors construct contrast sets themselves rather than using crowd workers. The original authors are the ones who best understand their dataset's intended phenomena…" (§2.4) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- "This is best done by first identifying a list of phenomena that characterize their dataset… After the standard dataset collection process, the authors should sample pivots from their test set and perturb them according to the listed phenomena." (§2.3) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- Contrast sets ≠ adversarial examples: "A contrast set is *not* a collection of adversarial examples (Szegedy et al., 2014). Adversarial examples are almost the methodological opposite of contrast sets: they change the input such that a model's decision changes but the gold label does not… contrast sets are model-agnostic." (§2.2) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- Lineage to minimal pairs: "In linguistics, for instance, the term *minimal pair* is used to denote two words with different meaning that differ by a single sound change… (Pike, 1946)… We additionally generalize the idea of a minimal *pair* to a *set*, and use a *consistency* metric, which we contend more closely aligns with what NLP researchers mean by 'language understanding'." (§5) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)

**Reported numbers (Table 2, verbatim transcription).** [full-text] Metrics per the caption: "percentage accuracy for NLVR2, IMDb, PERSPECTRUM, MATRES, and BoolQ; F1 scores for DROP and QUOREF; Exact Match (EM) scores for ROPES and MC-TACO; and unlabeled attachment score on modified attachments for the UD English dataset."

| Dataset | # Examples | # Sets | Model | Original test | Contrast | Consistency |
|---|---|---|---|---|---|---|
| NLVR2 | 994 | 479 | LXMERT | 76.4 | 61.1 (−15.3) | 30.1 |
| IMDb | 488 | 488 | BERT | 93.8 | 84.2 (−9.6) | 77.8 |
| MATRES | 401 | 239 | CogCompTime2.0 | 73.2 | 63.3 (−9.9) | 40.6 |
| UD English | 150 | 150 | Biaffine + ELMo | 64.7 | 46.0 (−18.7) | 17.3 |
| PERSPECTRUM | 217 | 217 | RoBERTa | 90.3 | 85.7 (−4.6) | 78.8 |
| DROP | 947 | 623 | MTMSN | 79.9 | 54.2 (−25.7) | 39.0 |
| QUOREF | 700 | 415 | XLNet-QA | 70.5 | 55.4 (−15.1) | 29.9 |
| ROPES | 974 | 974 | RoBERTa | 47.7 | 32.5 (−15.2) | 17.6 |
| BoolQ | 339 | 70 | RoBERTa | 86.1 | 71.1 (−15.0) | 59.0 |
| MC-TACO | 646 | 646 | RoBERTa | 38.0 | 14.0 (−24.0) | 8.0 |

Source: [arXiv:2004.02709](https://arxiv.org/abs/2004.02709), Table 2.

**Human ceiling check (Table 3, verbatim transcription).** "For four datasets, we choose at least 100 test instances and one corresponding contrast set instance… We (the authors) test ourselves on these examples (ensuring that those who were tested were different from those who created the examples)." IMDb 94.3 → 93.9 (−0.4); PERSPECTRUM 91.5 → 90.3 (−1.2); QUOREF 95.2 → 88.4 (−6.8); ROPES 76.0 → 73.0 (−3.0). — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]

**Effort/cost.** "using about a person-week of work can yield high-quality perturbed test sets of approximately 1000 instances for many commonly studied NLP benchmarks"; "For most datasets, the average time to perturb each example was 1–3 minutes, which translates to approximately 17–50 hours of work to create 1,000 examples. However, some datasets, particularly those with complex output structures, took substantially longer: each example for dependency parsing took an average of 15 minutes." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]

**Release.** Contrast sets released at https://allennlp.org/contrast-sets. — [AllenNLP](https://allennlp.org/contrast-sets) [snippet]

### Inferences
- A T2 group of exactly two items (same question, two `as_of` dates straddling one amendment) is a contrast set with pivot = the pre-amendment instance and |C(x)| = 1, i.e. a *contrast pair*. Gardner et al.'s IMDb and PERSPECTRUM rows have `# Examples == # Sets`, which is exactly this one-perturbation-per-pivot regime, so the paired case is attested in the original paper and the benchmark author does not need to claim a novel configuration.
- Because the Table 2 caption says consistency counts the original example too, the T2 metric should be reported as "correct at both dates," not "correct at the post-amendment date given correct at the pre-amendment date." These differ and only the former is contrast consistency.
- The IMDb contrast set (488 examples / 488 sets) has exactly the size of Kaushik et al.'s counterfactually-revised IMDb test set, which strongly suggests Gardner et al. reused it rather than writing fresh perturbations. I did not verify this in the appendix — treat as an inference.

### Gaps
- I did not read Appendices A/B (per-dataset dataset descriptions and metric details), so per-dataset annotation guidelines beyond the three walkthroughs (DROP, NLVR2, UD parsing) in §3 are unverified.
- The paper gives no inter-annotator agreement figure for contrast-set construction, and no statistical test or confidence interval on any consistency number.

---

## Q2. Kaushik, Hovy & Lipton 2020 (CAD) and Ribeiro et al. 2020 (CheckList) — protocols and metrics, and how they differ from contrast sets

### Takeaway
Neither CAD nor CheckList defines a "whole group must be right" metric. CAD reports **separate accuracies on the original and the counterfactually-revised test sets** and is primarily a *training-data* intervention; CheckList reports a **per-test failure rate** over MFT/INV/DIR tests and never aggregates to a joint per-group score. The joint metric is Gardner et al.'s contribution — this matters for the citation the benchmark author needs.

### Cited findings

**Kaushik, Hovy & Lipton citation.** Divyansh Kaushik, Eduard Hovy, Zachary C. Lipton. 2020. *Learning the Difference That Makes a Difference with Counterfactually-Augmented Data.* ICLR 2020 (conference paper). arXiv:1909.12434. — [arXiv](https://arxiv.org/abs/1909.12434); [ML Anthology record](https://mlanthology.org/iclr/2020/kaushik2020iclr-learning) [abstract/page + ar5iv]

- Protocol (abstract, verbatim): the authors "task humans with revising each document so that it accords with a counterfactual target label, retains internal coherence, and avoids unnecessary changes." — [arXiv:1909.12434](https://arxiv.org/abs/1909.12434) [abstract]
- Worker instruction wording, sentiment: "revise this negative movie review to make it positive, without making any gratuitous changes." — [ar5iv:1909.12434](https://ar5iv.labs.arxiv.org/html/1909.12434) [full-text via ar5iv summarizer]
- Scale: 2,500 IMDb reviews revised; 1,750 SNLI sentence pairs revised; resulting splits include 1,707 sentiment training examples and 3,332 NLI pairs per revision type (revised-premise / revised-hypothesis). — [ar5iv:1909.12434](https://ar5iv.labs.arxiv.org/html/1909.12434) [full-text via ar5iv summarizer]
- Cost/time: total $10,778.14; ≈5 minutes per review revision and ≈4 minutes per NLI sentence; $0.65 per revision, $0.15 per verification. — [ar5iv:1909.12434](https://ar5iv.labs.arxiv.org/html/1909.12434) [full-text via ar5iv summarizer]
- Headline drops (models trained on original data, evaluated on revised test data): Bi-LSTM sentiment 79.3 → 55.7; BERT NLI 72.2 → 39.7 on revised-premise; linear model ≈80 → ≈51. Models trained on combined data recover to ≈81–92% across both evaluations. — [ar5iv:1909.12434](https://ar5iv.labs.arxiv.org/html/1909.12434) [full-text via ar5iv summarizer]
- Core claim (abstract, verbatim): "classifiers trained on original data fail on their counterfactually-revised counterparts and vice versa." — [arXiv:1909.12434](https://arxiv.org/abs/1909.12434) [abstract]

**Ribeiro et al. citation.** Marco Tulio Ribeiro, Tongshuang Wu, Carlos Guestrin, Sameer Singh. 2020. *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList.* Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL 2020), pages 4902–4912. (ACL 2020 Best Paper.) — [ACL Anthology](https://aclanthology.org/2020.acl-main.442/) [abstract/page]

- **MFT (verbatim):** "A collection of simple examples (and labels) to check a behavior within a capability." — [ar5iv:2005.04118](https://ar5iv.labs.arxiv.org/html/2005.04118) [full-text via ar5iv summarizer]
- **INV (verbatim):** "When we apply label-preserving perturbations to inputs and expect the model prediction to remain the same." — [ar5iv:2005.04118](https://ar5iv.labs.arxiv.org/html/2005.04118)
- **DIR (verbatim):** "Similar [to INV], except that the label is expected to change in a certain way." — [ar5iv:2005.04118](https://ar5iv.labs.arxiv.org/html/2005.04118)
- Reporting unit: failure rate per test. For INV, a failure is counted when the prediction changes *and* the probability shift exceeds 0.1; for DIR, a failure is counted when the expected directional change does not materialise. — [ar5iv:2005.04118](https://ar5iv.labs.arxiv.org/html/2005.04118) [full-text via ar5iv summarizer; numeric threshold worth re-checking against the paper's Table 1 footnotes]
- Example failure rates: sentiment negation MFT, BERT 18.8% vs RoBERTa 54.2%; QQP vocabulary MFT (modifier changes), BERT 78.4% / RoBERTa 78.0%; machine comprehension comparison MFT, BERT 91.3%. — [ar5iv:2005.04118](https://ar5iv.labs.arxiv.org/html/2005.04118) [full-text via ar5iv summarizer]
- Headline: practitioners using CheckList "created twice as many tests, and found almost three times as many bugs" as users without it. — [ACL Anthology](https://aclanthology.org/2020.acl-main.442/) [abstract]

**Explicit contrast drawn by Gardner et al. themselves.** Gardner et al. cite Ribeiro et al. 2018a/b in their "Automatic Construction of Contrast Sets" discussion and argue automatic rules rarely push pivots *across* a decision boundary: "it is very challenging to come up with rules or other automated methods for pushing pivots *across a decision boundary*—in most cases this presupposes a model that can already perform the intended task." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]

### Inferences
- The three traditions differ along two orthogonal axes that the benchmark author should state explicitly: (a) does the perturbation change the gold label? CAD **yes**, contrast sets **yes (typically)**, CheckList INV **no** / DIR **partially (direction only)**; (b) is the paired structure *scored jointly*? CAD **no**, CheckList **no**, contrast sets **yes**.
- T2 (same question, two `as_of` dates, two different gold answers) is on the "label changes" + "scored jointly" quadrant, i.e. squarely a contrast set, not a CheckList INV test and not CAD. The *source* of the perturbation differs (a real legislative amendment rather than an annotator's edit), which is the novel part and should be framed as a naturally-occurring contrast set rather than a new metric.
- CAD is useful to the benchmark author mainly as the citation for *why* paired data exposes spurious features (confounding vs causal association), and as a protocol precedent for the "minimal edit, retain coherence, no gratuitous changes" instruction, which maps onto the T2 covariate "textual similarity between the two versions."

### Gaps
- I could not confirm the exact split sizes of the Kaushik et al. IMDb test set (I have 488 only via the Gardner Table 2 row and ar5iv's "1,707 training examples"); check the CAD paper's Table 1 before citing split sizes.
- The CheckList per-test failure rates above came from an ar5iv summariser rather than my own reading of the tables; verify the three numbers against Tables 1–3 of the ACL version before quoting them in a thesis.

---

## Q3. Standard vocabulary for "model must get the whole group right"

### Takeaway
**"Contrast consistency"** (Gardner et al. 2020) is the origin term and the one to cite; in practice most follow-up papers shorten it to **"consistency"** and say "(Gardner et al., 2020)" in the same breath. **"Group scoring" / group accuracy** (Elazar et al. 2021) is the same quantity under a different name in the Winograd-schema line. **"Pair accuracy"** is *not* a safe synonym — in MT metric meta-evaluation and in BLiMP it denotes a different ranking-style measure.

### Cited findings

**Origin term — "contrast consistency."** Gardner et al. 2020, §2.2, as quoted in Q1. — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]

**Immediate uptake as plain "consistency", with two concrete variants, in TORQUE.** Qiang Ning, Hao Wu, Rujun Han, Nanyun Peng, Matt Gardner, Dan Roth. 2020. *TORQUE: A Reading Comprehension Dataset of Temporal Ordering Questions.* EMNLP 2020, pages 1158–1172. — [ACL Anthology](https://aclanthology.org/2020.emnlp-main.88/) [full-text PDF]
- Verbatim (§6): "We report the standard macro F1 and exact-match (EM) metrics in question answering, and also EM consistency, the percentage of contrast question sets for which a model's predictions match exactly to all questions in a group (Gardner et al., 2020)." — [aclanthology.org/2020.emnlp-main.88](https://aclanthology.org/2020.emnlp-main.88/)
- Verbatim (Table 4 caption): "C (consistency) is the percentage of contrast groups for which a model's predictions have F1 ≥ 80% for all questions in a group (Gardner et al., 2020)." — [aclanthology.org/2020.emnlp-main.88](https://aclanthology.org/2020.emnlp-main.88/)
- This is the key precedent for a **soft-threshold** group metric: the "all members correct" rule can be relaxed to "all members above a per-item quality threshold" when the per-item metric is not binary.

**"Group scoring" / group accuracy.** Yanai Elazar, Hongming Zhang, Yoav Goldberg, Dan Roth. 2021. *Back to Square One: Artifact Detection, Training and Commonsense Disentanglement in the Winograd Schema.* arXiv:2104.08161. — [arXiv](https://arxiv.org/abs/2104.08161) [full-text via ar5iv summarizer]
- Verbatim: "for an arbitrary scoring function f, and a group of minimal-distance instances xᵢ, score each of the examples xᵢⱼ in the group and assign the group its worse-performing score", i.e. `groupScore(xᵢ) = min_j f(xᵢⱼ)`; applied to the Winograd twin sentences this "assign[s] a point only if they are all correctly predicted by a model." — [ar5iv:2104.08161](https://ar5iv.labs.arxiv.org/html/2104.08161)
- Note: with binary per-item accuracy, `min_j f` is identical to Gardner's `all({ŷ = y′})`. Group scoring is the generalisation that also works for non-binary per-item scores (and subsumes TORQUE's F1 ≥ 80% rule as a thresholded variant).

**"Relative consistency" — a correction term for the metric, not a new name for it.** Jacob K. Johnson, Ana Marasović. 2023. *How Much Consistency Is Your Accuracy Worth?* BlackboxNLP 2023 (workshop at EMNLP 2023). arXiv:2310.13781. — [arXiv](https://arxiv.org/abs/2310.13781) [abstract/page]
- They define consistency as "a robustness measurement that evaluates the rate at which a model correctly responds to all instances in a bundle of minimally different examples relying on the same knowledge." — [arXiv:2310.13781](https://arxiv.org/abs/2310.13781)
- Their proposal: **relative consistency** = "the probability that an equally accurate model would surpass the consistency of the proposed model"; a model at 100% relative consistency has the maximum consistency achievable at its accuracy. — [arXiv:2310.13781](https://arxiv.org/abs/2310.13781)

**Terms that are *false friends*, do not reuse them for a joint metric.**
- "Pair accuracy" in MT metric meta-evaluation: "given a minimal pair of candidates, it measures what percentage of the time a metric prefers the better candidate, with ties giving a half-point" — Deutsch et al., *Ties Matter: Meta-Evaluating Modern Metrics with Pairwise Accuracy and Tie Calibration*, [arXiv:2305.14324](https://arxiv.org/pdf/2305.14324) [snippet]
- BLiMP-style minimal-pair accuracy: "An LM's overall accuracy on BLiMP is simply the proportion of minimal pairs in which the model assigns a higher probability to the acceptable sentence" — a *ranking* comparison within the pair, not a joint-correctness measure. [snippet, surfaced via the BLiMP metric card / MultiBLiMP 1.0, [arXiv:2504.02768](https://arxiv.org/pdf/2504.02768)]

### Inferences
- Recommended wording for the thesis: *"We report **contrast consistency** (Gardner et al., 2020): the proportion of T2 contrast pairs for which the system is correct at **both** `as_of` dates. This is the same quantity as *group accuracy* / *group scoring* (Elazar et al., 2021) specialised to groups of size two."* Then keep the internal shorthand TCS, defined once, rather than presenting TCS as a new metric.
- "Contrast consistency" appears to dominate in the contrast-set lineage, and plain "consistency + (Gardner et al., 2020)" dominates in papers that assume the reader knows the lineage. "Set accuracy" and "joint accuracy" did not surface at all in this literature in my searches — "joint accuracy" in NLP is strongly associated with dialogue state tracking (joint goal accuracy), so avoid it.
- TORQUE's thresholded variant is the right template if the Vietnamese legal answers are scored with a soft metric (span F1, citation overlap) rather than exact match: state the per-item threshold explicitly in the metric definition, as TORQUE does.

### Gaps
- I did **not** run a quantitative citation-frequency study (e.g. a Semantic Scholar citation-graph count of how many of Gardner et al.'s citers say "contrast consistency" vs "consistency" vs "group accuracy"). The dominance claim above is a qualitative reading of the sources I opened, not a measured frequency. If the thesis needs to assert dominance, that count should be run.
- I found no canonical origin for "pair accuracy" or "set accuracy" as names for the joint-correctness metric in the contrast-set literature. Treat them as non-standard here.
- The Elazar et al. 2021 venue (EMNLP 2021 vs *SEM/other) was not confirmed in this session — I only have the arXiv record. Verify before citing a venue.

---

## Q4. The gap between per-item accuracy and all-items-in-the-group accuracy

### Takeaway
The gap is large and systematic: across Gardner et al.'s ten datasets, contrast consistency sits **6 to 31 points below** the per-item contrast-set score, and **9 to 41 points below** the original i.i.d. test score. For a 2-item group, consistency near accuracy² is the "no extra robustness" baseline, and several published results sit close to it.

### Cited findings

**Derived from Gardner et al. Table 2** (arithmetic mine, inputs verbatim from the table in Q1) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709):

| Dataset | Contrast score − Consistency | Original test − Consistency |
|---|---|---|
| NLVR2 | 31.0 | 46.3 |
| IMDb | 6.4 | 16.0 |
| MATRES | 22.7 | 32.6 |
| UD English | 28.7 | 47.4 |
| PERSPECTRUM | 6.9 | 11.5 |
| DROP | 15.2 | 40.9 |
| QUOREF | 25.5 | 40.6 |
| ROPES | 14.9 | 30.1 |
| BoolQ | 12.1 | 27.1 |
| MC-TACO | 6.0 | 30.0 |

- Gardner et al.'s own framing of this gap, verbatim: "state-of-the-art models perform dramatically worse on our contrast sets than on the original test sets, **especially when evaluating consistency**." (§1) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]
- Their interpretation, verbatim: "our results suggest that models have 'overfit' to artifacts that are present in existing datasets; they achieve high test scores but do not completely capture a dataset's intended phenomena." (§4.3) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]
- They explicitly warn against cross-dataset comparison of these numbers: "note that these numbers are not directly comparable due to differences in dataset size, model architecture, contrast set design, etc." (§4.3) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]

**TORQUE (Table 4, test set, verbatim transcription)** — [aclanthology.org/2020.emnlp-main.88](https://aclanthology.org/2020.emnlp-main.88/) [full-text]:

| System | F1 | EM | C (consistency) |
|---|---|---|---|
| Human | 95.3 | 84.5 | 82.5 |
| BERT-base | 67.2 | 39.8 | 23.6 |
| BERT-large | 71.9 | 45.9 | 29.1 |
| RoBERTa-base | 72.6 | 45.7 | 29.9 |
| RoBERTa-large | 75.2 | 51.1 | 34.5 |

- So on TORQUE the EM→C gap is 16.6 points for RoBERTa-large but only **2.0 points for humans** (84.5 → 82.5). The human gap being near zero while the model gap is large is the strongest single argument that the joint metric measures something real and not just item-count arithmetic.
- Gardner et al. make the same point for their own four human-evaluated datasets: human performance drops only 0.4 to 6.8 points from original to contrast instances (Table 3, Q1 above). — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]

**The accuracy-conditioned view.** Johnson & Marasović (2023) argue the raw gap is partly an artefact of accuracy itself, and propose reporting relative consistency so that "an equally accurate model" is the comparison point. — [arXiv:2310.13781](https://arxiv.org/abs/2310.13781) [abstract/page]

**Robustness-gap evidence in the LLM era.** SCORE (Systematic COnsistency and Robustness Evaluation) reports accuracy fluctuations of up to 10% from prompt paraphrasing on MMLU-Pro and up to 6.1% from answer-choice reordering on AGIEval — [arXiv:2503.00137](https://arxiv.org/html/2503.00137v1) [snippet]. ELECTRA-small reportedly falls from ~90% on SNLI to ~75% on an out-of-distribution contrast set — [arXiv:2503.06648](https://arxiv.org/abs/2503.06648v1) [snippet].

### Inferences
- **Independence baseline, for a 2-item pair** (my derivation, not from any paper): if per-item accuracy is p and the two items of a pair were statistically independent, expected pair consistency = p². For Gardner's IMDb, mean per-item accuracy across original and contrast is (93.8 + 84.2)/2 = 89.0, so p² = 79.2 against an observed consistency of 77.8 — essentially at or slightly below independence. This is a cheap and defensible sanity line to print next to TCS in the thesis: *TCS vs p² tells the reader whether getting the first date right helps at all with the second.*
- For the T2 group specifically, the per-item covariates the benchmark author already records (textual similarity between versions, number of versions, chance level of a random version pick) are exactly what would let them report TCS *conditioned on difficulty*, which is a stronger result than a single TCS number and pre-empts the "spurious difficulty" criticism in Q6.
- Expect the T2 TCS to land well below per-date accuracy. A 10–30 point gap would be unremarkable by the published record; a gap near zero would itself be the finding (and should prompt a check that the two dates are not trivially distinguishable, e.g. by date-string leakage into the answer).

### Gaps
- I found no paper that reports a *meta-analysis* of the accuracy-to-consistency gap across many benchmarks; the "typical size" above is my own tabulation from two primary papers, not a cited summary statistic.
- Johnson & Marasović's concrete relative-consistency numbers (which models are at 100% relative consistency) are in the full paper, which I did not open.

---

## Q5. How many contrast pairs are enough

### Takeaway
There is **no explicit power analysis anywhere in the contrast-set literature that I could find**. The de-facto standard is Gardner et al.'s "approximately 1,000 instances", with published contrast sets running from **70 sets (BoolQ) to 974 sets (ROPES)**. For an actual justification the benchmark author must borrow from the NLP power-analysis literature (Card et al. 2020; Bowman & Dahl 2021), which is about test-set size in general, not contrast pairs specifically.

### Cited findings

**Sizes actually published** (from Gardner et al. Table 2, the `# Sets` column, which is the number of *groups* and therefore the denominator of consistency) — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]:
- Smallest: BoolQ 70 sets (339 examples). UD English 150 sets. MATRES 239 sets. PERSPECTRUM 217 sets.
- Largest: ROPES 974 sets, MC-TACO 646 sets, DROP 623 sets, IMDb 488 sets, NLVR2 479 sets, QUOREF 415 sets.
- The design target, verbatim: "Our contrast sets consist of up to about 1,000 total examples and average 1–5 examples per contrast set." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709)
- The only explicit sizing *rationale* given, verbatim: "Perturbed test sets only need to be large enough to draw substantiated conclusions about model behavior and thus do not require undue labor on the original dataset authors." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) — note this is an assertion, not a power calculation.

**CAD sizes.** 2,500 revised IMDb reviews and 1,750 revised SNLI pairs; ≈3,332 NLI pairs per revision type. — [ar5iv:1909.12434](https://ar5iv.labs.arxiv.org/html/1909.12434) [full-text via ar5iv summarizer]

**Legal-domain minimal-pair size point of comparison.** LexFlip reports "373 minimal perturbations of Quebec statutory French that reverse legal force while preserving 0.93 of the tokens." — [arXiv:2609.05296](https://arxiv.org/pdf/2609.05296) [snippet — very recent, unverified; open the paper before citing]

**General NLP power guidance to borrow.**
- Dallas Card, Peter Henderson, Urvashi Khandelwal, Robin Jia, Kyle Mahowald, Dan Jurafsky. 2020. *With Little Power Comes Great Responsibility.* EMNLP 2020. arXiv:2010.06595. Key figure: "typical test sets of 2000 sentences have approximately 75% power to detect differences of 1 BLEU point"; they also find "small test sets mean that most attempted comparisons to state of the art models will not be adequately powered" on several GLUE tasks, and release notebooks for power analysis. — [arXiv:2010.06595](https://arxiv.org/abs/2010.06595) [abstract/page]
- Samuel R. Bowman, George E. Dahl. 2021. *What Will it Take to Fix Benchmarking in Natural Language Understanding?* NAACL 2021. arXiv:2104.02145. Reported guidance: a benchmark should be "large and discriminative enough to detect any qualitatively relevant performance difference between two models"; for a 1% absolute minimum detectable effect in NLU, "an evaluation set of a few thousand examples would suffice under typical conditions." — [arXiv:2104.02145](https://arxiv.org/pdf/2104.02145) [snippet — the abstract/body phrasing should be checked before verbatim quotation]
- Reported smaller-benchmark limits: "A 164-item benchmark cannot reliably distinguish models less than about 15 points apart, and detecting a two-point difference at all takes on the order of ten thousand items." — [snippet, surfaced from a power-analysis cookbook; I could not trace this to a peer-reviewed primary source, so do not cite it as published — recompute it instead, it is a standard two-proportion calculation.]

### Inferences
- **A defensible sample-size argument the benchmark author can actually write**, with no new citation needed beyond standard statistics: contrast consistency is a binomial proportion over *n pairs* (each pair is one Bernoulli trial). The normal-approximation half-width of a 95% CI at the worst case p = 0.5 is 1.96·√(0.25/n): n = 100 → ±9.8 pp; n = 200 → ±6.9 pp; **n = 300 → ±5.7 pp**; n = 400 → ±4.9 pp; n = 1000 → ±3.1 pp. (Arithmetic mine; verify with an exact Clopper–Pearson interval, which is wider at small n.)
- The pair, not the item, is the unit of analysis. Reporting a CI computed over 2n items would understate uncertainty because the two dates of a pair are strongly dependent. This is worth one sentence in the methods section.
- For *comparing two systems* on the same pairs, the correct test is **McNemar's test** on the paired binary outcomes (discordant pairs only), not an unpaired two-proportion z-test. I did not find a contrast-set paper that does this, so it is a methodological improvement the thesis can claim.
- Given the published range (70–974 sets) and the ~1,000-instance norm, a T2 group in the low hundreds of pairs is squarely within precedent; a T2 group below ~70 pairs would be below the smallest published contrast set and should be flagged as exploratory.

### Gaps
- **I found no paper in the contrast-set literature that performs or reports a power analysis for the number of contrast pairs.** This is a genuine hole in the literature, and the benchmark author should say so explicitly rather than implying a standard exists.
- I did not open Card et al.'s notebooks or the body of Bowman & Dahl; the "few thousand examples" figure is snippet-level and should be verified before being quoted.
- No source I found gives guidance specific to *paired* / within-item designs in NLP benchmarking (the gain in power from pairing). The classic reference for that is the biostatistics literature on McNemar sample size, which is outside the sources I searched.

---

## Q6. Criticisms and limitations of contrast sets (for a Limitations section)

### Takeaway
The sharpest criticisms are (a) Gardner et al.'s own admission that contrast sets have **solely negative predictive power** and are **dataset-specific**; (b) that counterfactual/contrast data does not reliably transfer as *training* data; (c) that minimal-pair evaluation can produce **false positives** and suffers a **distribution mismatch** with deployment; (d) that consistency is partly an artefact of accuracy; (e) that robustness evaluations themselves can be "easily thwarted."

### Cited findings

**Self-stated, from Gardner et al. §2.5 (verbatim).** — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]
- *Solely Negative Predictive Power*: "Contrast sets only have negative predictive power: they reveal if a model *does not* align with the correct local decision boundary but cannot confirm that a model *does* align with it. This is because annotators cannot exhaustively label all inputs near a pivot and thus a contrast set will necessarily be incomplete."
- *Dataset-Specific Instantiations*: "The process for creating contrast sets is *dataset-specific*: although we present some general guidelines that hold across many tasks, experts must still characterize the type of phenomena each individual dataset is intended to capture."
- *Post-hoc risk* (§2.4): "post-hoc contrast sets may be biased by existing models."
- *Model-in-the-loop risk* (§2.4): "observing model outputs while perturbing data creates subtle, undesirable biases towards the idiosyncrasies of that model."
- *Scope discipline* (§3, Summary): "the purpose of a contrast set is not to introduce new challenges, but to more thoroughly evaluate the original intent of the test set."

**Counterfactual augmentation does not reliably transfer (training-side criticism).** William Huang et al. 2020. *Counterfactually-Augmented SNLI Training Data Does Not Yield Better Generalization Than Unaugmented Data.* arXiv:2010.04762. Finding: models trained on counterfactually-augmented SNLI do not generalise better than unaugmented data of similar size, and augmentation can *hurt* robustness to challenge examples. — [ar5iv:2010.04762](https://ar5iv.arxiv.org/html/2010.04762) [snippet]

**Minimal pairs can mislead.** Jannis Vamvas, Rico Sennrich. 2021. *On the Limits of Minimal Pairs in Contrastive Evaluation.* BlackboxNLP 2021 (workshop at EMNLP 2021). — [ACL Anthology](https://aclanthology.org/2021.blackboxnlp-1.5/) [abstract/page]
- Two limitations stated: (1) contrastive evaluation "can lead to false positives" when the hypothesis being tested is not well-motivated — a model can look right on the pair for the wrong reason; (2) a distributional discrepancy between human-written reference sentences used to build pairs and the machine-generated text seen at deployment time. Their remedy is to build minimal pairs from machine-generated text instead of human references. — [ACL Anthology](https://aclanthology.org/2021.blackboxnlp-1.5/)

**Robustness evaluations themselves are fragile.** Ashim Gupta, Rishanth Rajendhran, Nathan Stringham, Vivek Srikumar, Ana Marasović. 2024. *Whispers of Doubt Amidst Echoes of Triumph in NLP Robustness.* NAACL 2024 (main). arXiv:2311.09694. They report that "evaluating with CheckLists and contrast sets shows significant gaps in model performance" while arguing that "current approaches for adversarial evaluations of models are themselves problematic: they can be easily thwarted." — [arXiv:2311.09694](https://arxiv.org/abs/2311.09694) [abstract/page]

**Consistency conflated with accuracy.** Johnson & Marasović 2023 — raw consistency comparisons across models of different accuracy are not like-for-like; relative consistency is the correction. — [arXiv:2310.13781](https://arxiv.org/abs/2310.13781) [abstract/page]

**Cost as a practical limitation.** Contrast sets are expensive and labour-intensive to build and so limited in diversity, which is the stated motivation for the 2025 wave of LLM-generated contrast sets. — [arXiv:2503.06648](https://arxiv.org/abs/2503.06648v1) [snippet]

### Inferences
- The limitations most likely to be raised against a T2 contrast-pair group specifically:
  1. **Negative predictive power** — a high TCS does not prove the system tracks the law correctly, only that it was not caught failing on these pairs. Gardner et al.'s own wording covers this and should be cited directly.
  2. **Non-representative perturbation** — T2 pairs are selected around amendments, so they over-sample a non-random slice of the law. Report TCS alongside the overall benchmark accuracy, never instead of it.
  3. **Spurious difficulty / shortcut leakage** — the two dates of a T2 pair may be separable by a surface cue (a date string, a version number, differing formatting), which would make TCS easy for the wrong reason. The recorded covariate "textual similarity between the two versions" is the natural way to measure and report this.
  4. **Chance-level inflation** — the recorded "chance level of a random version pick" covariate is exactly the per-item chance floor, and TCS's chance floor for a 2-item pair is the product of the two per-item floors, which is much lower. Stating both floors forestalls the "is this gap just arithmetic?" objection.
  5. **No model in the loop** — Gardner et al. are emphatic about this; if any part of the T2 pair selection used model outputs (e.g. picking amendments a baseline got wrong), that must be disclosed, because it converts the contrast set into an adversarial set with different semantics.
- One criticism in the literature does **not** apply cleanly to T2: annotator artefacts from hand-written perturbations. A T2 pair's "perturbation" is a real legislative amendment, not an annotator's edit, so there is no annotator writing style to leak. That is a genuine strength to claim — but it comes with the trade-off that the perturbation is not minimal by construction (hence the textual-similarity covariate).

### Gaps
- I did not verify Joshi & He's ACL 2022 investigation of the (in)effectiveness of CAD, which I believe exists and is a frequently cited criticism; it did not surface in my searches and I will not cite it unverified.
- I found no study measuring whether contrast-set *consistency* correlates with downstream deployment reliability, which would be the strongest form of validity evidence for the metric. If such a study exists I did not locate it.

---

## Q7. Contrast sets / minimal pairs applied to temporal or versioned knowledge

### Takeaway
The closest established precedent is **TORQUE** (contrast sets over *temporal ordering* questions, with an explicit group consistency metric) and the **MATRES** contrast set inside Gardner et al. Both are about temporal *language*, not about versioned knowledge changing over time. For the "same question, different `as_of` date, different gold answer" design I found **no established contrast-set-framed benchmark** — the 2024–2026 temporal-knowledge benchmarks exist but, as far as I verified, do not adopt Gardner-style joint pair scoring. This is a real opening for the thesis.

### Cited findings

**TORQUE — temporal contrast sets with a consistency metric.** Ning et al., EMNLP 2020 (full citation in Q3). — [ACL Anthology](https://aclanthology.org/2020.emnlp-main.88/) [full-text]
- Construction, verbatim: "Note the 3 warm-up questions form a contrast set, and we treat the first as 'original' and the others 'modified.'" Contrast questions were elicited during crowdsourcing: workers answered "at least 12 questions (including contrast questions)" per passage, with "$6 plus $0.5 for each extra question."
- Scale: 3.2k passage annotations (~50 tokens/passage), 24.9k events, 21.2k user-provided questions, "half of them were labeled by crowd workers as modifications of existing ones." Total cost $15k, "an average of $0.70/question."
- Quality: Worker Agreement With Aggregate (WAWA) F1 of 94.2% for events and 84.7% for answer annotations.
- Results (Table 4, test, transcribed in Q4): RoBERTa-large F1 75.2 / EM 51.1 / C 34.5 vs Human F1 95.3 / EM 84.5 / C 82.5.

**MATRES contrast set inside Gardner et al.** Perturbations of temporal relation extraction; "for the MATRES dataset we tracked whether a perturbation changed appearance order, tense, or temporal conjunction words. These fine-grained labels show that the model does comparatively better at modeling appearance order (66.5% of perturbed examples correct) than temporal conjunction words (60.0% correct)." Contrast consistency 40.6 (CogCompTime2.0). Example perturbation (Table 1): "Colonel Collins followed a normal progression once she was picked as a NASA astronaut" → "…**before** she was picked…", flipping the gold label from "picked was before followed" to "picked was after followed." — [arXiv:2004.02709](https://arxiv.org/abs/2004.02709) [full-text]
- This is the single most T2-like published example: **a one-token change to the input that flips the temporal gold answer, scored with contrast consistency.**

**Temporal / evolving-knowledge benchmarks found (leads, not verified as contrast-set-framed).**
- TeCFaP (Temporally Consistent Factuality Probe) with the TEMP-COFAC dataset of prefix-style English query paraphrases — [ACL Anthology 2024.emnlp-main.887](https://aclanthology.org/2024.emnlp-main.887) [snippet]
- *Question Answering under Temporal Conflict: Evaluating and Organizing Evolving Knowledge with LLMs* — introduces Temporal Wiki (factual drift across historical Wikipedia snapshots) and Unified Clark (timestamped news), building question–document pairs for time-dependent questions — [arXiv:2506.07270](https://arxiv.org/html/2506.07270v1) [snippet]
- evolveQA — built from timestamped corpora (AWS/Azure change logs, WHO outbreak reports), generating questions with gold answers tailored to different LLM knowledge cut-off dates — [arXiv:2510.19172](https://arxiv.org/html/2510.19172v1) [snippet]
- *Temporal Referential Consistency* — [arXiv:2510.15513](https://arxiv.org/html/2510.15513v1) [snippet]
- A strict composite metric reported in this space: "the average temporal factuality (soft accuracy) only if the model's responses are identical across all paraphrases for a given query" — this is a group-style metric, but over *paraphrases*, not over *dates*. [snippet, attributed to the TeCFaP line of work; verify the source before citing]
- Lineage for paraphrase-consistency metrics commonly cited alongside: Ravichander et al. (2020) on paired probes and Elazar et al. (2021) on consistency of factual knowledge in PLMs (ParaRel). [snippet — surfaced secondhand, not verified in this session]

**Legal-domain minimal pairs and amendment chains (leads).**
- LexFlip: "373 minimal perturbations of Quebec statutory French that reverse legal force while preserving 0.93 of the tokens" — described as a dissociation diagnostic for legal meaning-preservation metrics — [arXiv:2609.05296](https://arxiv.org/pdf/2609.05296) [snippet, very recent, unverified]
- *Risks and Limits of Automatic Consolidation of Statutes*, NLLP 2025: automated metrics show 93–99% textual similarity for amendment chains, yet only 50.3% exact match for single-step amendments and 20.51% for multi-step, and "even small divergences can carry legal significance" per expert assessment — [ACL Anthology, NLLP 2025](https://preview.aclanthology.org/setup/2025.nllp-1.29) [snippet, unverified]
- The NLLP 2025 numbers are directly relevant to the T2 "textual similarity between the two versions" covariate: they are published evidence that **high surface similarity between statute versions coexists with legally decisive differences**, which is precisely the argument for why a T2 pair is hard and why similarity must be reported as a covariate rather than used as a difficulty proxy.

### Inferences
- Framing to use: *T2 is a contrast set in the sense of Gardner et al. (2020), where the perturbation is not an annotator edit to the question but a change to the `as_of` date that moves the pivot across a legislative amendment. The gold label changes because the governing norm changed, which is exactly the "small but meaningful change that changes the gold label" condition.* TORQUE and the MATRES contrast set are the precedents for contrast sets whose perturbation is temporal; the novelty is that the perturbation is to the *query time*, not to the *text*.
- Because the perturbation is a date rather than a text edit, the T2 pair is *perfectly* minimal on the question side (the question string is identical) and *not* minimal on the evidence side (the statute text differs). That is an unusual and defensible position in this literature and worth stating as a design property: it eliminates the annotator-artefact confound at the question level entirely.
- The LexFlip and NLLP 2025 leads suggest legal minimal pairs are an emerging 2025–2026 topic; the thesis should check them for priority claims before asserting novelty.

### Gaps
- **I could not find any published benchmark that applies Gardner-style contrast consistency to point-in-time / `as_of`-dated legal QA.** This is a genuine negative result from my searching, not a claim that none exists — my searches were English-language and did not cover Vietnamese-language venues.
- The 2024–2026 temporal-knowledge benchmarks above (TeCFaP, evolveQA, Temporal Wiki, KairosQA, TDBench) were surfaced only at snippet level. I did **not** verify whether any of them scores a question jointly across two dates, which is the specific thing the benchmark author needs to know for a related-work section. These should be opened individually before the related-work paragraph is written.
- Two of the arXiv IDs returned by search (2608.08512, 2605.22769, and the LexFlip 2609.05296) are dated within the last few months relative to today's date and I did not open any of them; confirm they exist and say what the snippets claim.

---

## Summary: the three deliverables the benchmark author asked for

1. **Framing.** T2 is a contrast set (Gardner et al., 2020, Findings of EMNLP 2020, pp. 1307–1323) with groups of size two, i.e. contrast *pairs*; precedent for size-two groups exists in the original paper (IMDb 488 examples / 488 sets; PERSPECTRUM 217/217). The temporal precedents are TORQUE (Ning et al., EMNLP 2020) and the MATRES contrast set.
2. **Metric name.** Call it **contrast consistency** and cite Gardner et al. 2020 §2.2: "the **contrast consistency** of a model to be whether it makes correct predictions ŷ on every element in the set: all({ŷ = y′ ∀(x′, y′) ∈ C(x)})", with the operational form from their Table 2 caption ("the percentage of the '# Sets' contrast sets for which a model's predictions are correct for all examples in the set, *including* the original example"). Secondary names worth a parenthetical: *group accuracy / group scoring* (Elazar et al., 2021). If the per-item score is soft rather than binary, follow TORQUE's thresholded form. Keep TCS as an internal abbreviation, defined once; do not present it as a new metric. Consider also reporting *relative consistency* (Johnson & Marasović, BlackboxNLP 2023) to separate robustness from raw accuracy.
3. **Sample size.** No power analysis exists in this literature — say so. Justify instead on (a) precedent: published contrast sets range 70–974 groups with a ~1,000-instance design target (Gardner et al. 2020); (b) binomial precision on the pair as the unit of analysis: n = 300 pairs gives a ±5.7 pp worst-case 95% CI half-width; (c) general NLP power guidance (Card et al., EMNLP 2020; Bowman & Dahl, NAACL 2021). Use McNemar's test for system-vs-system comparison on the same pairs.
