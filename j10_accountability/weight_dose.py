"""Real-state-weights dose-response: do the formulas states actually chose
redistribute the failing label across the poverty distribution?

The weight_space.py sweep shows the lowest-performing label is sensitive to the
indicator weights, with growth-heavy weightings pulling the label off high-poverty
schools (a random Monte-Carlo result). This script replaces the random draws with the
weights states ACTUALLY adopted in their ESSA accountability formulas, transcribed from
NCES Table 1.13 (the elementary/middle column; see SOURCES.md). For each state it
applies that state's real weights to its own Title I elementary/middle schools,
reconstructs the lowest-5% label, and measures how poverty-concentrated the labelled set
is. The dose-response asks whether states that lean on growth (rather than achievement
levels) produce a less poverty-concentrated failing label.

Mapping: the four indicators the panel carries (achievement, growth, quality=SQSS, grad)
are matched to the NCES achievement / growth / school-quality / graduation weights;
English-language-proficiency and residual "other" weight have no school-level indicator
here, so they are dropped and the remaining weights renormalized. The growth-versus-
achievement balance that drives the redistribution is preserved. States with no
summative rating (e.g. CA, NY) are excluded.

Outputs:
  data/state_dose.csv   - one row per state: applied weights, growth share, the poverty
      concentration of the labelled set, within-state poverty-gradient slope.
  data/results_dose.csv - the dose-response regression (concentration on growth share).

Run:  python3 weight_dose.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from weight_space import build_panel, composite, identify, IND_KEYS

HERE = Path(__file__).parent
OUT_STATE = HERE / "data" / "state_dose.csv"
OUT_REG = HERE / "data" / "results_dose.csv"
MIN_SCHOOLS = 30  # Title I elem/middle schools required for a stable state estimate

# Elementary/middle indicator weights as published in each state's ESSA plan, from
# NCES Table 1.13 (https://nces.ed.gov/programs/statereform/tab1_13.asp). Keys:
# ach=academic achievement, grw=growth, sqss=school quality/student success,
# grad=graduation, elp=English-language proficiency, other=residual. Points or
# percentages as published; renormalized in code. States with no summative rating
# are omitted (CA, ID, MN, NE, NH, NY, ND, OR, PA, VA). Kentucky ranges -> midpoints.
NCES_WEIGHTS = {
    "AL": dict(ach=40, grw=40, elp=5, other=15),
    "AK": dict(ach=30, grw=40, elp=15, sqss=5),
    "AZ": dict(ach=30, grw=50, elp=10, other=10),
    "AR": dict(ach=35, grw=50, sqss=15),
    "CO": dict(ach=23.3, grw=48, elp=12, sqss=16.7),
    "CT": dict(ach=300, grw=400, elp=100, other=50),
    "DE": dict(ach=30, grw=40, elp=10, sqss=20),
    "DC": dict(ach=30, grw=40, elp=5, sqss=25),
    "FL": dict(ach=200, grw=200, other=400),
    "GA": dict(ach=22.5, grw=31.5, elp=3.5, other=41.83),
    "HI": dict(ach=40, grw=40, elp=10, other=10),
    "IL": dict(ach=20, grw=50, elp=5, other=25),
    "IN": dict(ach=42.5, grw=42.5, elp=10, other=5),
    "IA": dict(ach=14, grw=47, elp=10, other=29),
    "KS": dict(ach=25, grw=0, elp=25, other=50),
    "KY": dict(ach=20, grw=25, other=42.5),       # midpoints of 15-25 / 20-30 / 30-55
    "LA": dict(ach=50, grw=25, sqss=25, other=5),
    "ME": dict(ach=42, grw=38, elp=10, other=10),
    "MD": dict(ach=20, grw=25, elp=10, other=45),
    "MA": dict(ach=40, grw=25, elp=10, sqss=25),
    "MI": dict(ach=32.22, grw=37.78, elp=11.11, other=8.33),
    "MS": dict(ach=28, grw=54, elp=5, other=13),
    "MO": dict(ach=40, grw=30, elp=20, other=10),
    "MT": dict(ach=25, grw=30, elp=10, sqss=10, other=25),
    "NV": dict(ach=25, grw=35, elp=10, sqss=10, other=20),
    "NJ": dict(ach=30, grw=40, elp=20, other=10),
    "NM": dict(ach=33, grw=42, elp=10, other=15),
    "OH": dict(ach=21.88, grw=29.16, elp=10, other=38.88),
    "OK": dict(ach=30, grw=30, elp=15, sqss=5, other=20),
    "RI": dict(ach=8, grw=6, elp=4, sqss=15),
    "SC": dict(ach=35, grw=35, elp=10, sqss=10, other=10),
    "SD": dict(ach=40, grw=20, elp=10, other=30),
    "TN": dict(ach=30, grw=35, elp=10, sqss=15, other=10),
    "TX": dict(ach=40, grw=40, elp=10, other=10),
    "UT": dict(ach=25, grw=25, elp=9, other=41),
    "VT": dict(ach=70, grw=0, elp=10, other=20),
    "WA": dict(ach=40, grw=50, elp=5, other=5),
    "WV": dict(ach=28, grw=28, elp=14, other=30),
    "WI": dict(ach=37.5, grw=37.5, elp=10, other=15),
    "WY": dict(ach=25, grw=25, elp=25, other=25),
}


def mapped_weights(raw):
    """NCES weights -> a vector over IND_KEYS=[achievement, grad, quality, growth_proxy].

    ELP and residual 'other' have no indicator here and are dropped; the rest are
    renormalized to sum to one."""
    slots = {
        "achievement": raw.get("ach", 0.0),
        "grad": raw.get("grad", 0.0),
        "quality": raw.get("sqss", 0.0),
        "growth_proxy": raw.get("grw", 0.0),
    }
    w = np.array([slots[k] for k in IND_KEYS], dtype=float)
    if w.sum() <= 0:
        return None
    return w / w.sum()


def main():
    df = build_panel()
    df = df[df["is_high"] == 0].copy()  # elem/middle: the NCES weights are elem/middle
    values = df[IND_KEYS].to_numpy(dtype=float)
    mask = (~np.isnan(values)).astype(float)
    values = np.nan_to_num(values, nan=0.0)

    rows = []
    for st, raw in NCES_WEIGHTS.items():
        sub = df["state"] == st
        n = int(sub.sum())
        if n < MIN_SCHOOLS:
            continue
        w = mapped_weights(raw)
        if w is None:
            continue
        comp = composite(values, mask, w)
        # identify within this state only (rank the state's own schools)
        s = df["state"].to_numpy()
        ident = identify(comp, s, df["is_high"].to_numpy(),
                         df["grad"].fillna(np.inf).to_numpy())
        ident = ident & sub.to_numpy()

        pov = df["econ_disadv_share"]
        base = pov[sub].mean()
        conc = pov[ident].mean() / base if base else np.nan  # poverty concentration ratio
        # within-state poverty gradient: OLS of identified on poverty
        ss = df[sub]
        idsub = ident[sub.to_numpy()]
        slope = np.nan
        if ss["econ_disadv_share"].notna().sum() > MIN_SCHOOLS:
            X = sm.add_constant(ss["econ_disadv_share"].to_numpy())
            slope = sm.OLS(idsub.astype(float), X, missing="drop").fit().params[1]

        growth_share = raw.get("grw", 0) / max(raw.get("ach", 0) + raw.get("grw", 0), 1e-9)
        rows.append(dict(state=st, n_schools=n, w_achievement=w[0], w_grad=w[1],
                         w_quality=w[2], w_growth=w[3], growth_share=growth_share,
                         n_identified=int(ident.sum()), mean_poverty_base=base,
                         concentration=conc, poverty_gradient=slope))

    sd = pd.DataFrame(rows).sort_values("growth_share")
    sd.to_csv(OUT_STATE, index=False)

    # dose-response: poverty concentration of the labelled set on the growth share
    d = sd.dropna(subset=["concentration", "growth_share"])
    reg = []
    for yname in ("concentration", "poverty_gradient"):
        dd = d.dropna(subset=[yname])
        X = sm.add_constant(dd["growth_share"].to_numpy())
        m = sm.OLS(dd[yname].to_numpy(), X).fit(cov_type="HC1")
        reg += [(yname, "intercept", m.params[0]), (yname, "slope_growth_share", m.params[1]),
                (yname, "slope_se", m.bse[1]), (yname, "slope_t", m.tvalues[1]),
                (yname, "slope_p", m.pvalues[1]), (yname, "r2", m.rsquared),
                (yname, "n_states", int(m.nobs))]
    pd.DataFrame(reg, columns=["outcome", "statistic", "value"]).to_csv(OUT_REG, index=False)

    corr = d["growth_share"].corr(d["concentration"])
    print(f"real-state-weights dose-response ({len(d)} states with summative formulas):")
    print(f"  growth share range {d.growth_share.min():.2f}-{d.growth_share.max():.2f}; "
          f"concentration range {d.concentration.min():.2f}-{d.concentration.max():.2f}")
    sl = [r for r in reg if r[0] == "concentration" and r[1] == "slope_growth_share"][0][2]
    pv = [r for r in reg if r[0] == "concentration" and r[1] == "slope_p"][0][2]
    print(f"  concentration ~ growth_share: slope={sl:+.3f} (p={pv:.3f}), corr={corr:+.3f}")
    print(f"  -> {OUT_STATE}, {OUT_REG}")


if __name__ == "__main__":
    main()
