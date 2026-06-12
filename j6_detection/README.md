# J6 — How Universities Govern a Biased Writing Detector

An algorithm audit of AI-writing detectors deployed for academic integrity, and of the
institutional policy that gives their output force. Two layers:

1. **Detector layer (audit).** AI-writing detectors classify human prose as "AI-generated"
   at rates that differ by the author's language background. We re-score a corpus of
   **human-written** essays (so any positive is a false accusation) with current open-source
   detectors and measure the false-positive rate by native vs non-native English status.
2. **Governance layer (policy).** A skewed false-positive rate becomes an equity problem only
   when an institution treats the detector's output as evidence. We code a sample of public
   university academic-integrity / AI policies for whether detector output is admissible, who
   carries the burden of proof, what appeal exists, and whether multilingual writers are
   protected.

The object of the paper is the **joint exposure**: where a group-skewed false-positive rate
meets a policy that makes the flag consequential. Middle-range claim: detection accuracy is
not procedural fairness; an automated gate converts language background into suspicion only
through the rules that admit it as evidence.

This is not a replication of detector-bias (Liang et al., 2023 and follow-ups established the
bias). The contribution is the governance layer and the joint-exposure framing.

## Pipeline
```
fetch_anchor_data.py    # download Liang et al. (2023) public human-essay corpora (verbatim)
build_essay_panel.py    # assemble essays -> panel + native/non-native label + provenance
run_detectors.py        # score every human essay with current open detectors -> AI-probability
analyze_detection.py    # false-positive (false-accusation) rate by L1 status; calibration -> data/results_summary.csv
build_policy_corpus.py  # collect public university integrity/AI policies -> coded panel
analyze_policy.py       # joint exposure (FPR gap x policy admissibility) -> data/results_summary.csv
make_figures.py         # Figures -> ../paper/blinded-manuscript/j6_figure{1,2,3}.{pdf,png}
```

## Data
- `data/essays_panel.csv` — one row per human essay: native/non-native label, source corpus, length, and the seven 2023 detectors' AI-probability scores (provenance via corpus).
- `data/results_summary.csv` — detector-layer numbers (FPR by L1 status, per-detector + pooled + unanimous-flag, threshold sensitivity).
- `data/policy_registry.csv` — input: curated real institution policy URLs (institution, state, control, policy_type, url).
- `data/policy_corpus.csv` — fetched policies with provenance + the four codebook columns, coded per `CODEBOOK_policy.md`.
- `data/policy_results.csv` — governance-layer numbers (code distributions, permissiveness index, joint exposure).

Detectors are open-source and version-pinned (see `SOURCES.md`). Essay corpora are public. The
policy coding protocol (admissibility, burden of proof, appeal, L2 protection) is in
`CODEBOOK_policy.md`; codes are auditable against the fetched text under `data/policy_raw/`.

## Headline
**Detector layer (baseline, seven 2023 detectors over 249 human essays).** At the
0.50 decision threshold the pooled false-accusation rate is **61.2% for non-native
(TOEFL) writers vs 3.6% for native (US) writers, a 16.9-fold gap**. Eighteen of 91
non-native essays are flagged as AI by **all seven** detectors; **zero** of 158
native essays are flagged unanimously at any threshold (0.25-0.90). The gap is not
an artifact of the cutoff: the fold-difference widens from 10.4x at tau=0.25 to
26.4x at tau=0.90. This reproduces Liang et al. (2023); the paper's contribution is
the governance layer and joint-exposure framing layered on top.

**Governance layer (50 state-flagship public universities).** No
flagship keeps the bias out of the misconduct process by trusting detectors less:
the gate is left open. Only **1** bans detector evidence (UT-Austin), **7** name
multilingual writers as a protected group, and **3** bar a detector flag from being
the sole basis; the other **39 of 50 (78%)** sit in a governance vacuum, where the
detector stance is non-binding guidance, the decision is delegated to individual
instructors, and no multilingual protection exists. One flagship (Georgia)
institutionally approves a detector with no L2 protection. The vacuum does not track
exposure: governance-vacuum rate is 76% / 81% / 76% across low / mid / high
international-enrollment terciles (Spearman with the vacuum index = 0.08, p = 0.59),
so protection is not allocated where the harm concentrates. Codes of record carry
verbatim support passages (`data/policy_corpus.csv`, reconciled against the stored
text in `data/policy_raw/`). Reliability: an independent second coder re-coded a
random fifth of the census from the stored text (`data/policy_corpus_secondcoder.csv`,
per-dimension kappa in `data/kappa_results.csv`: 0.81--1.00 on the floor dimensions),
and the author re-coded the same ten by hand (`data/policy_corpus_handcoder.csv`);
the governance-floor classification is identical under all three sets of codes.

**Current-classifier extension.** The penalty is not an artifact of one panel's tools. The local
re-run of roberta-base-openai-detector reproduces the panel's released HFOpenAI scores (r = 0.999), a
consistency check; the two classifiers independent of the panel (Fakespot 65.9%/13.3%, Hello-SimpleAI
36.3%/0.0%) still skew (pooled **51% vs 7%, 7.7-fold**); roberta-large-openai-detector flags 97.5% of
native human essays and so does not discriminate at all (excluded). None of the four is a product
universities license, so the claim is about the classifier family, not any campus tool. CS224N robustness: over the five
detectors common to all corpora, the pooled false-accusation rate is 3.3% native, 2.6% for fluent
graduate technical writing (CS224N), and 57.1% non-native, so the penalty tracks developing-English
fluency, not international authorship.
