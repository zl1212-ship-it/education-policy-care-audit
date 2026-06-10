# J6 governance-layer codebook

Coding protocol for the academic-integrity / AI policy corpus. One row per
institution per policy document. Every code must be supported by a verbatim
passage from the fetched policy text (stored in `data/policy_raw/<slug>.txt`,
provenance in `data/policy_corpus.csv`). Codes are content analysis, not
inference: if the text does not say it, it is coded `silent`/`none`, never
guessed. The supporting passage and its source URL are the evidence.

This layer exists because a group-skewed false-positive rate (the detector layer:
non-native writers are falsely flagged at 61.2% vs 3.6% for native writers,
pooled over seven detectors) becomes an equity problem only where an institution
treats the flag as actionable. The codebook measures, per institution, how
actionable the flag is and whether multilingual writers are shielded.

## Unit and provenance
- **Unit:** institution x governing policy document (academic-integrity code,
  provost/teaching-center AI guidance, or syllabus-policy template, whichever is
  the binding institutional rule). If an institution has both an integrity code
  and separate AI guidance, code the one that governs misconduct adjudication and
  note the other in `secondary_url`.
- **Provenance columns (filled by `build_policy_corpus.py`, never by hand):**
  `institution, state, control, policy_type, url, secondary_url, access_date,
  http_status, sha256, n_chars`.

## Coded dimensions

Each dimension has an ordered value set and an explicit decision rule. Code
`uncodable` only if the document failed to fetch (track, exclude from rates).

### 1. `detector_admissibility` — is detector output usable as evidence?
| value | decision rule |
|---|---|
| `prohibited` | Policy states detector output may **not** be the basis of an allegation, or bans detector use. |
| `advisory` | Detector output may prompt a review / conversation but is explicitly **not** proof on its own. |
| `admissible` | Policy permits detector output as evidence of misconduct (sole or contributing). |
| `silent` | No mention of AI detectors / detection tools. |

### 2. `burden_of_proof` — once a flag triggers a case, who must establish what?
| value | decision rule |
|---|---|
| `institution` | Instructor/institution must establish misconduct by evidence beyond the flag (e.g. corroboration required). |
| `student` | Student must rebut the flag or demonstrate authorship (e.g. produce drafts/version history) to avoid sanction. |
| `unspecified` | Process described without locating the burden, or silent. |

### 3. `appeal_pathway` — is there a defined route to contest a finding?
| value | decision rule |
|---|---|
| `formal` | Named appeal/grievance process with steps or a body. |
| `informal` | Mentions review/reconsideration but no formal route. |
| `none` | No appeal mechanism described, or silent. |

### 4. `l2_protection` — are multilingual / non-native writers acknowledged?
| value | decision rule |
|---|---|
| `explicit` | Names multilingual / ELL / non-native / international writers, or warns of detector bias against them. |
| `generic_fairness` | General fairness/equity/due-process language only, no L2-specific mention. |
| `none` | Neither. |

### 5. `decision_locus` — who decides whether a flag becomes a case?
The governance-vacuum thesis turns on delegation: a binding institutional rule is a
floor; pushing the call onto each instructor removes it.
| value | decision rule |
|---|---|
| `institutional` | A binding institution-wide rule governs detector use / AI-misconduct adjudication. |
| `delegated` | The institution defers the rule to individual instructors / syllabi. |
| `silent` | No institution-wide rule and no explicit delegation. |

## Derived: governance-vacuum index (computed in `analyze_policy.py`)
A 0-5 ordinal index of how exposed a non-native writer is to an unchecked biased
tool at this institution (higher = more vacuum). The framing is not "does the
policy admit detectors" (the pilot shows flagships rarely do) but "does any
binding institutional floor stand between a 16.9x-biased flag and the writer":
- `detector_admissibility`: admissible = 1, silent = 1, advisory = 0.5, prohibited = 0
  (a binding ban is a floor; advisory guidance discredits detectors but does not bind
  adjudication; silence/admission leaves the flag usable)
- `decision_locus`: delegated = 1, silent = 1, institutional = 0
- `l2_protection`: none = 1, generic_fairness = 0.5, explicit = 0
- `burden_of_proof`: student = 1, unspecified = 0.5, institution = 0
- `appeal_pathway`: none = 1, informal = 0.5, formal = 0

Weights are a documented modeling choice; `analyze_policy.py` also reports the raw
dimension distributions and cross-tabs so no conclusion rests on the index alone.

## The governance vacuum (the paper's object)
The detector layer fixes the group-level false-flag gap (16.9x, group-level, not
institution-specific). The governance layer asks whether any institutional floor
checks it. The headline cell is the vacuum: institutions where the biased flag can
reach a non-native writer with no protective floor, operationalized as

  `detector_admissibility != prohibited`  (no binding restriction on detector evidence)
  AND `l2_protection != explicit`          (no multilingual-specific protection)
  AND (`decision_locus != institutional` OR `burden_of_proof == student`).

`analyze_policy.py` reports the share of institutions in that cell, the
`detector_admissibility x l2_protection` and `decision_locus x l2_protection`
cross-tabs, and the vacuum-index distribution, so the claim is "at K of N flagships
a 16.9x group-skewed false-flag rate meets no binding floor and no multilingual
protection." The IPEDS international-enrollment share is merged per institution to
test whether the most-exposed campuses have more or less protective governance.

## Reliability
Codes are auditable because the raw text is committed. For the manuscript, a
second coder independently codes a random 20% subsample; report Cohen's kappa per
dimension. Disagreements resolved against the verbatim passage and the rule above.
