"""Build a single self-contained packet for the intra-rater (test-retest) reliability re-coding.

Writes data/SECONDCODER_packet.md: a one-page rule sheet followed by the full stored
policy text for each of the ten sampled institutions, with a blank coding line under
each. The coder reads top to bottom and records five codes per institution, blind to
the codes of record in policy_corpus.csv. Run analyze_kappa.py on the filled result.
"""
import csv
import re
from pathlib import Path

HERE = Path(__file__).parent
TEMPLATE = HERE / "data" / "policy_corpus_secondcoder_template.csv"
RAW = HERE / "data" / "policy_raw"
OUT = HERE / "data" / "SECONDCODER_packet.md"

RULES = """# Second-coder packet (intra-rater / test-retest reliability)

Code the ten institutions below WITHOUT looking at `policy_corpus.csv` (the codes of
record). For each institution read its policy text and choose one value per dimension.
There are no blank cells. When done, send the ten lines back (or fill
`data/policy_corpus_secondcoder.csv`); kappa is then computed by `analyze_kappa.py`.

## The five dimensions and their values

1. **detector_admissibility** -- is detector output usable as evidence of misconduct?
   - `prohibited` = a binding ban ("prohibits", "may not be used / may not be the basis").
   - `advisory`   = discredited but not banned ("instructors should refrain / avoid / are
     discouraged"; "not reliable proof").
   - `silent`     = no rule on using detector output as evidence (even if it merely notes
     that detection tools exist).
   - `admissible` = approved or encouraged to use ("the only detector approved for use",
     "faculty are encouraged to explore detectors").

2. **burden_of_proof** -- once a flag triggers a case, who must establish what?
   - `institution` = a binding rule that the flag cannot stand alone ("not the sole / single
     basis", "may not be the single measure", corroboration required).
   - `student`     = the student must rebut / prove authorship (e.g. produce drafts).
   - `unspecified` = anything else (DEFAULT; never leave blank).

3. **appeal_pathway** -- is there a route to contest a finding?
   - `formal`   = a named appeal / grievance process or body.
   - `informal` = mentions review / reconsideration but no formal route.
   - `none`     = no appeal described (DEFAULT; never leave blank).

4. **l2_protection** -- are multilingual / non-native writers acknowledged? (binary)
   - `explicit` = names multilingual / ELL / non-native / international writers, OR warns
     that detector output may misread writing by people whose first language is not English.
   - `none`     = otherwise (general fairness / equity / bias language with no link to
     language background counts as `none`).

5. **decision_locus** -- who SETS the rule on AI / detector use?
   - `institutional` = a binding institution-wide rule governs.
   - `delegated`     = the rule is left to instructors / syllabi.
   - `silent`        = neither. (A central honor/conduct office that only adjudicates cases is
     NOT, by itself, `institutional`.)

## How to record each institution
Write one line: `Institution: admissibility, burden, appeal, l2, locus`
e.g. `University of Iowa: advisory, unspecified, none, none, delegated`

---
"""


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    with open(TEMPLATE, newline="", encoding="utf-8") as f:
        insts = [r["institution"] for r in csv.DictReader(f)]
    parts = [RULES]
    for i, inst in enumerate(insts, 1):
        p = RAW / f"{slug(inst)}.txt"
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else "(text missing)"
        parts.append(f"## {i}. {inst}\n\n```\n{text.strip()}\n```\n\n"
                     f"**YOUR CODES ({inst}):** admissibility=____  burden=____  appeal=____  "
                     f"l2=____  locus=____\n\n---\n")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT}  ({len(insts)} institutions)")


if __name__ == "__main__":
    main()
