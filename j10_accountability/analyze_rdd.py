"""Sharp regression discontinuity at a state's identification line.

Estimand. A school is identified for comprehensive support when its state
accountability index falls below the identification cutoff (the lowest five percent).
Because identification is a deterministic step in the published index, this is a sharp
RDD: the treatment is crossing the line. The estimate is the jump in a downstream
school-level outcome at the cutoff,

    tau = lim_{x->c^-} E[Y | index = x]  -  lim_{x->c^+} E[Y | index = x],

estimated by local linear regression with a triangular kernel and separate slopes on
each side. The running variable is centered so the cutoff is at zero and treated
schools are below it.

Identification assumptions (stated, not assumed away):
- No precise manipulation of the index at the cutoff (schools cannot sort just below
  the line). Tested by a McCrary-style density-continuity test.
- Predetermined characteristics are continuous at the cutoff (schools just above and
  just below are otherwise comparable). Tested by running the same RDD on covariates,
  which should show no jump.
- Bandwidth and polynomial choices do not drive the estimate (robustness.py).

Primary moderator (pre-registered): whether the jump, and the density of schools at the
margin, differ for high-poverty versus low-poverty schools.

Outputs data/results_rdd.csv (tall: outcome / specification / statistic / value).

Run:  python3 analyze_rdd.py [--bandwidth 1.0]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = Path(__file__).parent
PANEL = HERE / "data" / "rdd_panel.csv"
OUT = HERE / "data" / "results_rdd.csv"

OUTCOMES = {
    "treat": "treatment (sharp first stage)",
    "got_funds": "received 1003 improvement funds",
    "award": "1003 improvement award ($)",
    "next_score": "next-cycle accountability score",
}
COVARIATES = ["enrollment", "achievement", "is_high", "econ_disadv_share"]
GRID = [0.5, 0.75, 1.0, 1.5, 2.0]


def llr(df, outcome, h, kernel="tri", poly=1, donut=0.0, covars=None):
    """Local polynomial RDD jump at running == 0; treated are running < 0.

    poly=1 local linear (default), poly=2 local quadratic. donut drops schools within
    +/- donut of the cutoff (manipulation robustness). covars = predetermined columns
    added linearly (covariate-adjusted RDD)."""
    cols = ["running", outcome] + (covars or [])
    d = df.loc[df["running"].between(-h, h), cols].dropna()
    if donut > 0:
        d = d[d["running"].abs() >= donut]
    if len(d) < 10:
        return dict(tau=np.nan, se=np.nan, n=len(d), n_left=0, n_right=0)
    x = d["running"].to_numpy(float)
    y = d[outcome].to_numpy(float)
    t = (x < 0).astype(float)
    w = (1 - np.abs(x) / h) if kernel == "tri" else np.ones_like(x)
    terms = [t]
    for p in range(1, poly + 1):
        terms += [x ** p, t * x ** p]
    if covars:
        terms.append(d[covars].to_numpy(float))
    X = sm.add_constant(np.column_stack(terms))
    res = sm.WLS(y, X, weights=w).fit(cov_type="HC1")
    return dict(tau=res.params[1], se=res.bse[1], n=int(len(d)),
                n_left=int(t.sum()), n_right=int((1 - t).sum()))


def mccrary(df, h, b=0.2):
    """Density-continuity test: jump in the running-variable density at the cutoff."""
    d = df.loc[df["running"].between(-h, h), "running"].to_numpy(float)
    edges = np.arange(-h, h + b, b)
    counts, _ = np.histogram(d, bins=edges)
    centers = (edges[:-1] + edges[1:]) / 2
    dens = counts / (len(d) * b)
    rows = []
    for side, mask in (("L", centers < 0), ("R", centers >= 0)):
        cx, cy = centers[mask], dens[mask]
        if len(cx) < 3:
            return dict(log_diff=np.nan, z=np.nan)
        X = sm.add_constant(cx)
        r = sm.OLS(cy, X).fit()
        # predict density at the boundary (x -> 0)
        pred = r.params[0]
        se = r.bse[0]
        rows.append((max(pred, 1e-9), se))
    (fl, sl), (fr, sr) = rows
    log_diff = np.log(fl) - np.log(fr)
    se = np.sqrt((sl / fl) ** 2 + (sr / fr) ** 2)
    return dict(log_diff=float(log_diff), z=float(log_diff / se) if se else np.nan)


def battery(sub, tag, h0, rows):
    """Full RDD battery on one stratum; specification carries the stratum tag."""
    def add(outcome, spec, stat, val):
        rows.append((outcome, f"{tag} {spec}", stat, val))

    for oc in OUTCOMES:
        if oc not in sub.columns:
            continue
        r = llr(sub, oc, h0)
        add(oc, f"h={h0}", "tau", r["tau"])
        add(oc, f"h={h0}", "se", r["se"])
        add(oc, f"h={h0}", "t", r["tau"] / r["se"] if r["se"] else np.nan)
        add(oc, f"h={h0}", "n", r["n"])
        add(oc, f"h={h0}", "n_treated_in_window", r["n_left"])
        for h in GRID:
            if h == h0:
                continue
            rr = llr(sub, oc, h)
            add(oc, f"h={h}", "tau", rr["tau"])
            add(oc, f"h={h}", "se", rr["se"])

    m = mccrary(sub, max(h0, 1.0))
    add("running_density", f"h={max(h0,1.0)}", "mccrary_z", m["z"])

    for cov in COVARIATES:
        if cov in sub.columns and sub[cov].nunique(dropna=True) > 1 and sub[cov].notna().sum() > 50:
            r = llr(sub, cov, h0)
            add(f"cov:{cov}", f"h={h0}", "tau", r["tau"])
            add(f"cov:{cov}", f"h={h0}", "t", r["tau"] / r["se"] if r["se"] else np.nan)

    if sub["econ_disadv_share"].notna().sum() > 50:
        med = sub["econ_disadv_share"].median()
        for grp, g in (("high_poverty", sub[sub.econ_disadv_share >= med]),
                       ("low_poverty", sub[sub.econ_disadv_share < med])):
            for oc in ("got_funds", "next_score"):
                r = llr(g, oc, h0)
                add(f"{oc}|{grp}", f"h={h0}", "tau", r["tau"])
                add(f"{oc}|{grp}", f"h={h0}", "se", r["se"])
                add(f"{oc}|{grp}", f"h={h0}", "n_treated_in_window", r["n_left"])
        near = sub[sub["running"].abs() <= h0]
        add("margin_density", f"h={h0}", "share_near_cutoff_high_poverty",
            float((near.econ_disadv_share >= med).mean()))
        add("margin_density", f"h={h0}", "n_near_cutoff", int(len(near)))
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bandwidth", type=float, default=1.0)
    args = ap.parse_args()
    df = pd.read_csv(PANEL, dtype={"ncessch": str})
    h0 = args.bandwidth
    rows = []

    # PRIMARY stratum: elementary/middle schools, where the running variable is a
    # homogeneous achievement/growth composite (high schools add a graduation-based
    # score and behave differently on the outcomes, so they are reported separately).
    mid = df[df["is_high"] == 0].copy()
    m_mid = battery(mid, "elem_middle", h0, rows)
    battery(df[df["is_high"] == 1].copy(), "high", h0, rows)
    battery(df, "pooled", h0, rows)

    # pooled covariate-adjusted (control for is_high), as a robustness on the full sample
    for oc in OUTCOMES:
        r = llr(df, oc, h0, covars=["is_high"])
        rows.append((oc, f"pooled+cov h={h0}", "tau", r["tau"]))
        rows.append((oc, f"pooled+cov h={h0}", "se", r["se"]))

    out = pd.DataFrame(rows, columns=["outcome", "specification", "statistic", "value"])
    out.to_csv(OUT, index=False)

    # console summary (primary stratum)
    def show(oc, tag="elem_middle"):
        s = out[(out.outcome == oc) & (out.specification == f"{tag} h={h0}")
                ].set_index("statistic")["value"]
        if "tau" in s.index:
            print(f"  {oc:<26} tau={float(s['tau']):+.4g}  se={float(s['se']):.4g}")
    print(f"WA sharp RDD, PRIMARY = elementary/middle (n={len(mid)}), bandwidth {h0}:")
    for oc in OUTCOMES:
        if oc in df.columns:
            show(oc)
    mid_cov = out[(out.specification == f"elem_middle h={h0}") &
                  out.outcome.str.startswith("cov:") & (out.statistic == "t")]
    print(f"  covariate-continuity |t| max = {mid_cov['value'].abs().max():.2f} (was 2.34 pooled)")
    print(f"  McCrary z = {m_mid['z']:.2f}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
