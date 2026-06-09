"""
Editor revision #6: archive the ACT-submission and Pell TWFE benchmark cells that appear in the
manuscript text but were not in revision_twfe.csv. Uses the same deterministic double-demeaning
TWFE estimator (cluster-robust SE) as reviewer_revisions.py, then appends the two rows.
"""
import os, importlib.util, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
spec = importlib.util.spec_from_file_location("rr", os.path.join(HERE, "reviewer_revisions.py"))
rr = importlib.util.module_from_spec(spec); spec.loader.exec_module(rr)

adm = rr.load()
adm["act_pct_submit"] = pd.to_numeric(adm["act_pct_submit"], errors="coerce")
pell = pd.read_csv(os.path.join(DATA, "pell_panel.csv"))
adm = adm.merge(pell, on=["unitid", "year"], how="left")

rows = pd.read_csv(os.path.join(DATA, "revision_twfe.csv")).to_dict("records")
have = {r["outcome"] for r in rows}
for oc in ["act_pct_submit", "pell_share"]:
    if oc in have:
        continue
    b, se = rr.twfe(adm, oc)
    rows.append({"outcome": oc, "twfe_att": round(b, 3), "se": round(se, 3), "z": round(b / se, 2)})
    print(f"  {oc:16s} TWFE {b:+.3f} (SE {se:.3f}, z={b/se:+.2f})")
pd.DataFrame(rows).to_csv(os.path.join(DATA, "revision_twfe.csv"), index=False)
print("appended ACT and Pell TWFE to data/revision_twfe.csv")
