"""Income disparate-impact audit: Pell vs non-Pell completion (IPEDS Outcome
Measures, 6-year completion, total cohort). Pell=fed_aid_type 1; non-recipient=4."""
import urllib.request, json, time
from collections import defaultdict
def fetch(u,t=6):
    for a in range(t):
        try:
            with urllib.request.urlopen(u,timeout=120) as r: return json.load(r)
        except Exception:
            if a==t-1: raise
            time.sleep(4*(a+1))
def pull(path):
    u=f"https://educationdata.urban.org/api/v1/college-university/ipeds/{path}"; out=[]
    while u:
        d=fetch(u); out+=d["results"]; u=d.get("next")
    return out
YEAR=2022
rate=defaultdict(dict); coh=defaultdict(dict)
for x in pull(f"outcome-measures/{YEAR}/?ftpt=99&class_level=99"):
    fa=x.get("fed_aid_type"); rt=x.get("completion_rate_6yr"); cz=x.get("cohort_rev_6yr") or x.get("cohort_adj_6yr") or 0
    if fa in (1,4) and rt is not None:
        rate[x["unitid"]][fa]=rt; coh[x["unitid"]][fa]=cz
tot=fail=0
for uid,m in rate.items():
    if 1 in m and 4 in m and coh[uid].get(1,0)>=30 and coh[uid].get(4,0)>=30 and m[4]>0:
        tot+=1
        if m[1]/m[4] < 0.80: fail+=1
print(f"Pell income audit ({YEAR}, OM 6yr): auditable={tot}; Pell completion < 0.80x non-Pell = {fail} ({round(100*fail/tot) if tot else 0}%)")
