"""Merge the US panel (47) with the cross-national panel (UK/AU/CA, 35) into a
4-system table and compute endpoint provision prevalence by national system
(restriction and procedure provisions, including appeal and multilingual protection).

Note: the US panel and the cross-national panel are scored on the same localized
provision lexicon (build_panel.py)."""
import pandas as pd, os
HERE = os.path.dirname(os.path.abspath(__file__))

US = pd.read_csv(os.path.join(HERE, "..", "data", "panel.csv"))
PILOT = pd.read_csv(os.path.join(HERE, "data", "panel.csv"))
US["country"] = "US"
PILOT["country"] = PILOT["state"]  # UK/AU/CA
panel = pd.concat([US, PILOT], ignore_index=True)

prov = ["prohibition_present", "detector_surveillance_present", "misconduct_framing_present",
        "sanction_present", "permitted_use_present", "disclosure_present",
        "appeal_present", "l2_protection_present"]
short = {"prohibition_present": "prohibition", "detector_surveillance_present": "detector",
         "misconduct_framing_present": "misconduct", "sanction_present": "sanction",
         "permitted_use_present": "permitted", "disclosure_present": "disclosure",
         "appeal_present": "appeal", "l2_protection_present": "L2_protect"}

last = panel.sort_values("event_q").groupby("unitid").tail(1)
order = ["US", "UK", "AU", "CA"]
g = last.groupby("country")
summ = pd.DataFrame({
    "n": g.size(),
    "address_AI": g["ai_addressed"].mean().round(2),
    "restrictive_idx": g["restrictive_idx"].mean().round(2),
    "procedural_idx": g["procedural_idx"].mean().round(2),
}).reindex(order)
print(f"=== 4-system endpoint summary ({last['unitid'].nunique()} institutions) ===")
print(summ.to_string())

prev = last.groupby("country")[prov].mean().reindex(order).round(2)
prev.columns = [short[c] for c in prev.columns]
print("\n=== endpoint provision prevalence by system (RESTRICTIVE | PROCEDURAL) ===")
print(prev.T.to_string())

print("\n=== Endpoint prevalence: appeal and multilingual protection by system ===")
gap = last.groupby("country").agg(
    misconduct=("misconduct_framing_present", "mean"),
    detector=("detector_surveillance_present", "mean"),
    appeal=("appeal_present", "mean"),
    L2_protect=("l2_protection_present", "mean")).reindex(order).round(2)
print(gap.to_string())
