# J7 vendor consequence-mapping codebook

Coding unit: one **vendor product line** (five rows). Evidence: only the vendor's own
public documentation, fetched and archived verbatim by `build_vendor_corpus.py` under
`data/vendor_raw/` (live pages change; the stored text at the access date is the
evidence of record). Every code carries a verbatim support passage and the source
document slug. Pages authored by client universities are out of scope.

## Dimensions

1. **noface_flag** — does documentation state that a face-detection failure (no face /
   missing from frame) produces a recorded event?
   - `automatic_flag` — the system itself records a flag/incident without human initiation.
   - `proctor_alert` — detection failure routes to a live proctor in real time.
   - `not_documented` — no statement found in the archived pages.
   Rule: code the strongest documented automatic pathway; quote the triggering sentence.

2. **id_gate** — what happens when automated identity verification fails?
   - `blocks_entry` — documentation states the exam cannot begin until verification passes.
   - `flag_proceed` — exam proceeds; the failure is recorded for later review.
   - `human_fallback` — a human completes verification when the automated step fails.
   - `not_documented`.

3. **consequence_path** — the documented downstream of a face flag:
   - `suspicion_score` — flags aggregate into a numeric suspicion/priority metric
     shown to the instructor.
   - `vendor_review` — vendor staff review flagged video before reporting out.
   - `instructor_review` — raw flags go to the instructor/administrator to interpret.
   - `not_documented`.
   Rule: code the terminal documented recipient of the flag.

4. **human_review** — does the vendor state that a human (proctor, vendor reviewer, or
   instructor) sees the flag before any consequence for the student?
   - `yes_documented` / `not_documented`.
   Rule: marketing statements like "we never make decisions" count only if the
   document states who does review.

5. **lighting_burden** — does student-facing documentation instruct the student to
   secure adequate lighting (well-lit room, no backlighting, no dark room)?
   - `yes` / `no`.
   Rationale: instructing students to fix lighting is the vendor acknowledging that
   detection degrades in dim light while assigning the remedy to the student; J7's
   exposure sweep measures whose faces that remedy fails first.

6. **bias_acknowledgment** — does the archived public documentation acknowledge that
   face detection/verification can perform differently across demographic groups
   (skin tone, race)?
   - `acknowledged` — names differential performance as a risk or known issue.
   - `deflected` — addresses the controversy by re-describing the technology
     (e.g., "we use facial detection, not facial recognition") without acknowledging
     differential performance.
   - `silent` — no mention.

## Provenance columns
`vendor, products, docs (slugs), access_date`, then for each dimension a code column
and a `_support` column holding the verbatim passage plus `[slug]`.
