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


def battery(sub, tag, h0, grid, state, rows):
    """Full RDD battery on one stratum; rows carry (state, outcome, spec, stat, value)."""
    def add(outcome, spec, stat, val):
        rows.append((state, outcome, f"{tag} {spec}", stat, val))

    for oc in OUTCOMES:
        if oc not in sub.columns or sub[oc].notna().sum() < 10:
            continue
        r = llr(sub, oc, h0)
        add(oc, "primary", "tau", r["tau"])
        add(oc, "primary", "se", r["se"])
        add(oc, "primary", "t", r["tau"] / r["se"] if r["se"] else np.nan)
        add(oc, "primary", "n", r["n"])
        add(oc, "primary", "n_treated_in_window", r["n_left"])
        add(oc, "primary", "bandwidth", h0)
        for h in grid:
            rr = llr(sub, oc, h)
            add(oc, f"h={h}", "tau", rr["tau"])
            add(oc, f"h={h}", "se", rr["se"])

    m = mccrary(sub, h0 * 2)
    add("running_density", "primary", "mccrary_z", m["z"])

    for cov in COVARIATES:
        if cov in sub.columns and sub[cov].nunique(dropna=True) > 1 and sub[cov].notna().sum() > 50:
            r = llr(sub, cov, h0)
            add(f"cov:{cov}", "primary", "tau", r["tau"])
            add(f"cov:{cov}", "primary", "t", r["tau"] / r["se"] if r["se"] else np.nan)

    if sub["econ_disadv_share"].notna().sum() > 50:
        med = sub["econ_disadv_share"].median()
        for grp, g in (("high_poverty", sub[sub.econ_disadv_share >= med]),
                       ("low_poverty", sub[sub.econ_disadv_share < med])):
            for oc in ("got_funds", "next_score"):
                if oc not in sub.columns or sub[oc].notna().sum() < 10:
                    continue
                r = llr(g, oc, h0)
                add(f"{oc}|{grp}", "primary", "tau", r["tau"])
                add(f"{oc}|{grp}", "primary", "se", r["se"])
                add(f"{oc}|{grp}", "primary", "n_treated_in_window", r["n_left"])
        near = sub[sub["running"].abs() <= h0]
        add("margin_density", "primary", "share_near_cutoff_high_poverty",
            float((near.econ_disadv_share >= med).mean()))
        add("margin_density", "primary", "n_near_cutoff", int(len(near)))
    return m


def main():
    df_all = pd.read_csv(PANEL, dtype={"ncessch": str})
    rows = []
    summary = {}
    for state, df in df_all.groupby("state"):
        # bandwidth is scale-aware: each state's index has its own units, so the primary
        # window is half the running-variable SD (keeps WA near h=1.0, scales CT to ~6).
        h0 = round(0.5 * df["running"].std(), 2)
        grid = sorted({round(f * h0, 3) for f in (0.5, 0.75, 1.0, 1.5, 2.0)})
        # PRIMARY stratum: elementary/middle, a homogeneous achievement/growth running
        # variable; high schools (graduation-based score) are reported separately.
        mid = df[df["is_high"] == 0].copy()
        m_mid = battery(mid, "elem_middle", h0, grid, state, rows)
        if (df["is_high"] == 1).sum() >= 30:
            battery(df[df["is_high"] == 1].copy(), "high", h0, grid, state, rows)
        battery(df, "pooled", h0, grid, state, rows)
        for oc in OUTCOMES:  # pooled covariate-adjusted (control is_high)
            if oc in df.columns and df[oc].notna().sum() >= 10:
                r = llr(df, oc, h0, covars=["is_high"])
                rows.append((state, oc, "pooled+cov", "tau", r["tau"]))
                rows.append((state, oc, "pooled+cov", "se", r["se"]))
        summary[state] = (h0, len(mid), m_mid["z"], df["design"].iloc[0])

    out = pd.DataFrame(rows, columns=["state", "outcome", "specification",
                                      "statistic", "value"])
    out.to_csv(OUT, index=False)

    for state, (h0, nmid, mz, design) in summary.items():
        print(f"{state} RDD ({design}), elem/middle n={nmid}, h0={h0}:")
        for oc in OUTCOMES:
            s = out[(out.state == state) & (out.outcome == oc) &
                    (out.specification == "elem_middle primary")].set_index("statistic")["value"]
            if "tau" in s.index and pd.notna(s["tau"]):
                print(f"  {oc:<22} tau={float(s['tau']):+.4g}  se={float(s['se']):.4g}")
        cov = out[(out.state == state) & (out.specification == "elem_middle primary") &
                  out.outcome.str.startswith("cov:") & (out.statistic == "t")]
        if len(cov):
            print(f"  covariate |t| max = {cov['value'].abs().max():.2f}  McCrary z = {mz:.2f}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
