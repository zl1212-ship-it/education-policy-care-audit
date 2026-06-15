# Provision codebook: scoring policy-text restrictiveness toward student AI use

`build_panel.py` applies this codebook deterministically to every snapshot's
extracted text. Every code is a regular-expression family; the codes are
auditable against the archived text under `data/snapshots_raw/`. Nothing here is
hand-entered: the panel columns are produced by the script.

## Scoping rule (AI-proximity)

The page tracked for each institution is its **durable** academic-integrity /
honor-code / conduct page, which carries integrity language (misconduct, sanction,
appeal) that has nothing to do with AI and predates the shock. To measure
**AI-specific** governance, every provision below except `ai_addressed` is counted
only when its pattern co-occurs with an AI term **inside the same proximity
window** (a sliding window of `WINDOW` characters, default 400, re-centered on
each AI-term hit). This gives a clean pre-shock baseline: before AI terms appear
on the page, the AI-scoped provisions are zero by construction, so the event study
measures AI language that the durable page gained, not the page's standing
integrity boilerplate.

`AI term` family: `artificial intelligence`, `generative ai`, `gen ai`,
`chatgpt` / `chat gpt`, `large language model`, `\bLLMs?\b`, `\bGPT\b`,
and the standalone token `\bA\.?I\.?\b` (word-bounded, so `aid`, `Dubai`, `email`
do not match).

## Codes

Each code is recorded as **presence (0/1)** per snapshot (length-robust), plus a
raw hit count for diagnostics. AI-scoped unless noted.

### Restrictive / surveillant (raise restrictiveness)

| code | what it captures | pattern family (illustrative) |
|---|---|---|
| `prohibition` | AI use banned or not allowed | prohibit, forbidden, not permitted, not allowed, may not use, ban(ned), unauthorized use |
| `detector_surveillance` | detection tools / detector output | ai detection, detector, turnitin, gptzero, originality (report), detection software |
| `misconduct_framing` | AI use framed as cheating / plagiarism / misconduct | plagiarism, academic misconduct, academic dishonesty, cheating, unauthorized assistance |
| `sanction` | explicit penalty attached | sanction, penalty, fail(ing grade), suspension, expulsion, disciplinary action |

### Permissive / procedural / protective (lower restrictiveness, raise due process)

| code | what it captures | pattern family (illustrative) |
|---|---|---|
| `permitted_use` | AI may be used, possibly with conditions | permitted, may use, allowed, encouraged, with permission, instructor('s) discretion, depends on the course |
| `disclosure` | disclosure / citation / acknowledgment route rather than a ban | disclose, cite, acknowledge, attribute, document (your) use, transparency |
| `appeal` | due-process channel | appeal, hearing, grievance, review board, contest the finding |
| `l2_protection` | explicit protection for multilingual / English-learner writers | english language learner, multilingual, non-native, first language, ESL, second language |

### Gate / intensity (not directional)

| code | what it captures |
|---|---|
| `ai_addressed` | any AI term appears anywhere on the page (1/0) |
| `n_ai_terms` | count of AI-term hits (intensity diagnostic) |
| `text_len` | extracted token count (length control / diagnostic) |

## Union across an institution's pages

Each snapshot of each page is scored independently. The institution-quarter row in
`data/panel.csv` is the **max** of each presence code across the institution's
tracked pages (integrity page and AI-guidance page), forward-filled from the most
recent snapshot of each page on or before the quarter end. A provision is therefore
"present at the institution" in a quarter if it appears on any of its pages then.
The derived indices below are recomputed from the maxed presence codes.

## Derived indices (columns in `data/panel.csv`)

- `restrictive_idx` = `prohibition` + `detector_surveillance` + `misconduct_framing` + `sanction` (0..4)
- `procedural_idx` = `permitted_use` + `disclosure` + `appeal` + `l2_protection` (0..4)
- `net_restrictiveness` = `restrictive_idx` - `procedural_idx` (-4..+4)
- `ai_governance_intensity` = count of the eight directional provisions present (0..8); the "how much AI policy" measure
- Primary event-study outcomes: `ai_addressed` (activation), `ai_governance_intensity` (development), `net_restrictiveness` (direction). Sub-indices are secondary.

## Reliability

The lexicon is deterministic, so re-running reproduces the codes exactly. Face
validity is checked in `robustness.py` by re-scoring a random sample of snapshots
against (a) a widened proximity window and (b) a held-out hand check of the
extracted text, reporting the share of codes that flip. Pattern families live in
one block at the top of `build_panel.py` so the codebook and the code cannot drift.
