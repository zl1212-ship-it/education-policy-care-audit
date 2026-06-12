"""Interactive terminal filler for a vendor-coding pass (friendly second-coder UI).

Usage:
    python3 fill_coding.py coder_a    # -> data/vendor_corpus_coder_a.csv
    python3 fill_coding.py coder_b    # -> data/vendor_corpus_coder_b.csv

It walks you through all 30 cells one at a time. For each cell it shows the
vendor, the question, the evidence passage from the vendor's documentation, and
the numbered options. You type a number. It saves after every answer, so you can
stop and resume any time (rerun the same command).

At a prompt you can also type:
    b   go back one cell
    t   show the full archived document(s) for this cell
    s   skip (leave blank for now)
    q   save and quit

Code each cell independently from the evidence and the codebook. Do not compare
with anyone else's pass while you fill; that independence is the whole point.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
TEMPLATE = HERE / "data" / "vendor_corpus_secondcoder_template.csv"
RAW = HERE / "data" / "vendor_raw"

QUESTION = {
    "noface_flag": "Does the documentation say a 'no face' / 'missing from frame' "
                   "reading produces a recorded event?",
    "id_gate": "When automated identity verification FAILS, what does the "
               "documentation say happens?",
    "consequence_path": "Where does a face flag ultimately go?",
    "human_review": "Does a human review the flag before it can affect the student?",
    "lighting_burden": "Does student-facing text put the burden of good lighting "
                       "on the STUDENT (well-lit room, no backlight)?",
    "bias_acknowledgment": "Does the public documentation acknowledge face "
                           "detection can perform differently by skin tone or race?",
}

GLOSS = {
    "automatic_flag": "the system records a flag/incident on its own",
    "proctor_alert": "it routes to a live human proctor in real time",
    "not_documented": "the pages do not say",
    "blocks_entry": "the exam cannot start until verification passes",
    "flag_proceed": "the exam proceeds; the failure is recorded for later review",
    "human_fallback": "a human completes the verification",
    "suspicion_score": "flags add up into a score/priority shown to the instructor",
    "vendor_review": "vendor staff review the flag before reporting out",
    "instructor_review": "raw flags go to the instructor to interpret",
    "yes_documented": "yes, the pages state a human reviews",
    "yes": "yes",
    "no": "no",
    "acknowledged": "it names a skin-tone or demographic performance gap",
    "deflected": "it re-describes the tech ('detection, not recognition') "
                 "without addressing a gap",
    "silent": "no mention at all",
}

BAR = "=" * 72


def show_docs(slugs):
    for slug in slugs.split("|"):
        path = RAW / f"{slug.strip()}.txt"
        print(f"\n----- {path.name} -----")
        print(path.read_text()[:4000] if path.exists() else "(file not found)")
        print("----- end -----")
    input("\n(press Enter to go back to the question) ")


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 fill_coding.py <coder_label>   e.g. coder_a  or  coder_b")
    name = sys.argv[1].strip().lower()
    out = HERE / "data" / f"vendor_corpus_{name}.csv"

    df = pd.read_csv(TEMPLATE)
    if out.exists():
        df["code"] = pd.read_csv(out)["code"]
    df["code"] = df["code"].fillna("").astype(str)

    print(f"\nFilling {len(df)} cells as '{name}'. Saves to {out.name} after each "
          "answer.\nType the number of your choice, or b/t/s/q (see prompt).")

    i = 0
    while 0 <= i < len(df):
        r = df.iloc[i]
        opts = [o.strip() for o in r["options"].split("|")]
        print("\n" + BAR)
        print(f"[{i + 1}/{len(df)}]   {r['vendor']}   |   {r['dimension']}")
        already = r["code"].strip()
        if already and already != "nan":
            print(f"   (currently: {already})")
        print(f"\n{QUESTION.get(r['dimension'], '')}\n")
        print("Evidence from the vendor's documentation:")
        print(f"  {r['evidence_passage']}\n")
        for n, o in enumerate(opts, 1):
            print(f"   {n}) {o}  ({GLOSS.get(o, '')})")
        ans = input(f"\nYour choice (1-{len(opts)}, or b/t/s/q): ").strip().lower()

        if ans == "q":
            break
        if ans == "b":
            i = max(0, i - 1)
            continue
        if ans == "t":
            show_docs(r["source_docs"])
            continue
        if ans == "s":
            i += 1
            continue
        if ans.isdigit() and 1 <= int(ans) <= len(opts):
            df.at[i, "code"] = opts[int(ans) - 1]
            df.to_csv(out, index=False)
            i += 1
        else:
            print("  ! please type a number in range, or b/t/s/q")

    df.to_csv(out, index=False)
    blank = (df["code"].str.strip().isin(["", "nan"])).sum()
    print(f"\nSaved {out.name}. {len(df) - blank}/{len(df)} cells filled"
          + (f", {blank} still blank (rerun to finish)." if blank else ", all done."))
    if not blank:
        print("Next: when both human passes are done, run "
              "`python3 analyze_vendor_kappa.py`.")


if __name__ == "__main__":
    main()
