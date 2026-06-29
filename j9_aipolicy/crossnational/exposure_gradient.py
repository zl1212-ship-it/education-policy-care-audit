"""Endpoint net restrictiveness vs international-student share, per national system
(UK n=14, AU n=8). Small-n descriptive: per-system slope and correlation of endpoint
restrictiveness on the international-enrollment share."""
import csv
import numpy as np, os
HERE = os.path.dirname(os.path.abspath(__file__))

PANEL = os.path.join(HERE, "data", "panel.csv")
FRAME = os.path.join(HERE, "data", "sample_frame.csv")

share = {r["unitid"]: float(r["intl_share"]) for r in csv.DictReader(open(FRAME)) if r["intl_share"]}
rows = list(csv.DictReader(open(PANEL)))
last = {}
for r in rows:
    u = r["unitid"]
    if u not in last or int(r["event_q"]) > int(last[u]["event_q"]):
        last[u] = r

for sysname in ("UK", "AU"):
    x, yR, yN = [], [], []
    for u, r in last.items():
        if r["state"] == sysname and u in share:
            x.append(share[u]); yR.append(int(r["restrictive_idx"])); yN.append(int(r["net_restrictiveness"]))
    x, yR, yN = np.array(x), np.array(yR), np.array(yN)
    print(f"\n=== {sysname} (n={len(x)}; intl_share {x.min():.0%}-{x.max():.0%}) ===")
    if len(x) >= 4:
        print(f"  r(intl, restrictive_idx)    = {np.corrcoef(x, yR)[0,1]:+.2f}")
        print(f"  r(intl, net_restrictiveness) = {np.corrcoef(x, yN)[0,1]:+.2f}")
