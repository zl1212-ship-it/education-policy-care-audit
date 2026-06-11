"""Verification-layer analysis: who fails to be confirmed as themselves.

Operating point: for each verifier, the decision threshold tau is set where
impostor pairs (different people, both faces detected) at NATIVE exposure produce
FMR = 1%, then tau is held fixed across all exposure conditions, mirroring a
deployed system calibrated under good light. A strict FMR = 0.1% point is reported
as sensitivity.

Outcomes on genuine pairs (same person; any rejection is wrong):
- fnmr        P(similarity < tau | both faces detected)   -- "you are not you"
- cannot_verify P(any cascade failure: either face undetected OR sim < tau)
                -- the proctoring-relevant union (no verification happens at all)

Strata: ITA terciles (T1 lightest, T3 darkest) computed once over genuine pairs'
native-exposure ita_pair, held fixed across conditions. LFW is demographically
skewed toward light-skinned subjects, so absolute Del Bino bins would leave the
dark cells thin; within-sample terciles keep contrasts powered. Continuous-ITA
Spearman trend is reported as the binning-free check. The FairFace detection layer
(analyze_detection.py) carries the perceived-race replication; LFW has no race
labels, which is stated as a limitation.

Output: data/verification_results.csv (kind in {rate, contrast, trend, threshold}).
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUTCOMES_CSV = os.path.join(HERE, "data", "verification_outcomes.csv")
OUT_CSV = os.path.join(HERE, "data", "verification_results.csv")

FMR_POINTS = {"fmr1pct": 0.01, "fmr01pct": 0.001}
TERCILES = ["T1_light", "T2_mid", "T3_dark"]


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    den = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    return center - half, center + half


def fisher(k1, n1, k0, n0):
    _, p = stats.fisher_exact([[k1, n1 - k1], [k0, n0 - k0]])
    return p


def main():
    d = pd.read_csv(OUTCOMES_CSV)
    gen = d[d["genuine"] == 1].copy()

    # terciles fixed from genuine pairs (one row per pair; ita is exposure-invariant)
    base = gen[gen["exposure"] == 1.0].drop_duplicates("pair_idx")
    qs = base["ita_pair"].quantile([1 / 3, 2 / 3]).values
    def tercile(v):
        return TERCILES[0] if v <= qs[0] else (TERCILES[1] if v <= qs[1]
                                               else TERCILES[2])
    gen["tercile"] = gen["ita_pair"].apply(tercile)

    rows = []
    for ver, dv in d.groupby("verifier"):
        # thresholds from native-exposure impostor pairs, both faces detected
        imp = dv[(dv["genuine"] == 0) & (dv["exposure"] == 1.0)
                 & (dv["detect_enroll"] == 1) & (dv["detect_probe"] == 1)]
        for pname, fmr in FMR_POINTS.items():
            tau = float(imp["similarity"].quantile(1 - fmr))
            rows.append({"kind": "threshold", "verifier": ver, "point": pname,
                         "value": round(tau, 5), "n": len(imp)})
            gv = gen[gen["verifier"] == ver].copy()
            gv["detected"] = (gv["detect_enroll"] == 1) & (gv["detect_probe"] == 1)
            gv["match"] = gv["detected"] & (gv["similarity"] >= tau)
            for exp, g in gv.groupby("exposure"):
                for outcome in ("fnmr", "cannot_verify"):
                    if outcome == "fnmr":
                        sub = g[g["detected"]]
                        fail = (sub["similarity"] < tau)
                    else:
                        sub = g
                        fail = ~sub["match"]
                    for t in TERCILES:
                        s = fail[sub["tercile"] == t]
                        k, n = int(s.sum()), len(s)
                        lo, hi = wilson(k, n)
                        rows.append({"kind": "rate", "verifier": ver,
                                     "point": pname, "exposure": exp,
                                     "outcome": outcome, "group": t, "n": n,
                                     "failures": k,
                                     "rate": round(k / n, 4) if n else np.nan,
                                     "wilson_lo": round(lo, 4),
                                     "wilson_hi": round(hi, 4)})
                    k3 = int(fail[sub["tercile"] == "T3_dark"].sum())
                    n3 = int((sub["tercile"] == "T3_dark").sum())
                    k1 = int(fail[sub["tercile"] == "T1_light"].sum())
                    n1 = int((sub["tercile"] == "T1_light").sum())
                    if min(n1, n3) > 0:
                        r3, r1 = k3 / n3, k1 / n1
                        rows.append({"kind": "contrast", "verifier": ver,
                                     "point": pname, "exposure": exp,
                                     "outcome": outcome,
                                     "group": "T3_dark vs T1_light",
                                     "n": n1 + n3, "rate": round(r3, 4),
                                     "comparison_rate": round(r1, 4),
                                     "risk_diff": round(r3 - r1, 4),
                                     "ratio": round(r3 / r1, 2) if r1 > 0
                                     else np.inf,
                                     "p_fisher": fisher(k3, n3, k1, n1)})
                rho, p = stats.spearmanr(g["ita_pair"], g["match"].astype(int))
                rows.append({"kind": "trend", "verifier": ver, "point": pname,
                             "exposure": exp, "outcome": "match",
                             "group": "spearman_ita", "n": len(g),
                             "ratio": round(rho, 4), "p_fisher": p})

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {len(out)} rows -> {OUT_CSV}\n")

    show = out[(out["kind"] == "contrast") & (out["point"] == "fmr1pct")]
    for ver, g in show.groupby("verifier"):
        print(f"=== {ver} (tau at FMR=1%, native) ===")
        for outcome, gg in g.groupby("outcome"):
            gg = gg.sort_values("exposure", ascending=False)
            line = f"  {outcome}: "
            for _, r in gg.iterrows():
                line += (f"| {r['exposure']}: {r['rate']:.2%}/"
                         f"{r['comparison_rate']:.2%} x{r['ratio']} "
                         f"p={r['p_fisher']:.1g} ")
            print(line)
        print()

if __name__ == "__main__":
    main()
