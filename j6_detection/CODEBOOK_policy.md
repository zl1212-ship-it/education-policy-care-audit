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

## Derived: accusation-permissiveness index (computed in `analyze_policy.py`)
A 0-5 ordinal index of how readily a policy lets a detector flag become a
sanction against the writer (higher = more permissive):
- `detector_admissibility`: admissible = 2, advisory = 1, prohibited/silent = 0
- `burden_of_proof`: student = 1, else 0
- `appeal_pathway`: none = 1, else 0
- `l2_protection`: none = 1, generic_fairness = 0.5, explicit = 0

`silent` admissibility scores 0 because an unstated rule gives the accused no
written protection but also no written license; it is reported separately so the
"silent" cell is never hidden inside the index.

## Joint exposure (the paper's object)
The detector layer fixes the group-level false-flag gap (group-level, not
institution-specific). The governance layer fixes how consequential the flag is.
Joint exposure is the cell where both bite: institutions that are
`admissible` AND (`burden_of_proof == student` OR `appeal_pathway == none`) AND
`l2_protection != explicit`. `analyze_policy.py` reports the share of institutions
in that cell and the cross-tab of admissibility x L2-protection, so the claim is
"at K of N institutions a 16.9x group-skewed false-flag rate meets a policy that
makes the flag actionable and offers multilingual writers no specific protection."

## Reliability
Codes are auditable because the raw text is committed. For the manuscript, a
second coder independently codes a random 20% subsample; report Cohen's kappa per
dimension. Disagreements resolved against the verbatim passage and the rule above.
