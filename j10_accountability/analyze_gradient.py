"""Poverty gradient of the lowest-performing label.

Quantifies how the chance of carrying the reconstructed ESSA identification label
rises with school poverty, two ways:

  (1) prevalence of the baseline label by poverty decile, and the share of draws that
      ever identify a school (label instability) by decile;
  (2) a logit of baseline identification on continuous poverty intensity with
      predetermined controls (enrollment, locale, level, charter), standard errors
      clustered by state.

It also reads weight_draws.csv to report how the poverty composition of the identified
set moves as the weights move (the redistribution the sweep produces).

Outputs data/results_gradient.csv (tall: section / statistic / value).

Run:  python3 analyze_gradient.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

HERE = Path(__file__).parent
INST = HERE / "data" / "label_instability.csv"
FRAME = HERE / "data" / "school_frame.csv"
DRAWS = HERE / "data" / "weight_draws.csv"
OUT = HERE / "data" / "results_gradient.csv"


def main():
    df = pd.read_csv(INST, dtype={"ncessch": str})
    frame = pd.read_csv(FRAME, dtype={"ncessch": str})
    df = df.merge(frame[["ncessch", "urban_centric_locale", "charter"]],
                  on="ncessch", how="left")
    rows = []

    # (1) by poverty decile
    by = df.groupby("poverty_decile").agg(
        n=("identified_baseline", "size"),
        prevalence=("identified_baseline", "mean"),
        mean_identify_freq=("identify_freq", "mean"),
        flip_rate=("flip", "mean"),
        mean_poverty=("econ_disadv_share", "mean"),
    ).reset_index()
    for _, r in by.iterrows():
        for stat in ["prevalence", "mean_identify_freq", "flip_rate", "mean_poverty", "n"]:
            rows.append(("decile", f"D{int(r.poverty_decile)}_{stat}", r[stat]))

    # top-vs-bottom poverty-quartile prevalence ratio
    q = df["econ_disadv_share"]
    hi = df[q >= q.quantile(0.75)]["identified_baseline"].mean()
    lo = df[q <= q.quantile(0.25)]["identified_baseline"].mean()
    rows.append(("contrast", "prevalence_top_pov_quartile", hi))
    rows.append(("contrast", "prevalence_bottom_pov_quartile", lo))
    rows.append(("contrast", "ratio_top_over_bottom", hi / lo if lo else np.nan))

    # (2) logit with clustered SEs
    d = df.copy()
    d["locale_grp"] = (d["urban_centric_locale"] // 10).astype("Int64").astype(str)
    d["log_enroll"] = np.log(d["enrollment"].clip(lower=1))
    d["charter"] = d["charter"].fillna(0)
    # align rows with the model: drop any NaN in the modeled columns up front so the
    # cluster groups match the estimation sample exactly
    d = d.dropna(subset=["identified_baseline", "econ_disadv_share", "log_enroll",
                         "is_high", "charter", "locale_grp", "state"]).reset_index(drop=True)
    nstates = d["state"].nunique()
    fit_kw = {"disp": False}
    if nstates >= 5:  # clustered SEs need enough clusters to be meaningful
        fit_kw.update(cov_type="cluster", cov_kwds={"groups": d["state"]})
    model = smf.logit(
        "identified_baseline ~ econ_disadv_share + log_enroll + is_high "
        "+ charter + C(locale_grp)", data=d).fit(**fit_kw)
    for nm in model.params.index:
        if nm.startswith("C(") or nm == "Intercept":
            continue
        rows.append(("logit_coef", nm, model.params[nm]))
        rows.append(("logit_se", nm, model.bse[nm]))
        rows.append(("logit_p", nm, model.pvalues[nm]))
    # odds ratio for a 10-point (0.1) rise in poverty share
    b_pov = model.params["econ_disadv_share"]
    rows.append(("logit_or", "per_0.1_poverty_share", float(np.exp(0.1 * b_pov))))
    rows.append(("logit_fit", "pseudo_r2", model.prsquared))
    rows.append(("logit_fit", "n", int(model.nobs)))
    rows.append(("logit_fit", "n_state_clusters", nstates))

    # (3) redistribution across the weight envelope
    dr = pd.read_csv(DRAWS)
    rows.append(("sweep", "mean_poverty_identified_p05",
                 dr["mean_poverty_identified"].quantile(0.05)))
    rows.append(("sweep", "mean_poverty_identified_p95",
                 dr["mean_poverty_identified"].quantile(0.95)))
    rows.append(("sweep", "share_top_pov_quartile_min",
                 dr["share_identified_top_pov_quartile"].min()))
    rows.append(("sweep", "share_top_pov_quartile_max",
                 dr["share_identified_top_pov_quartile"].max()))
    # how strongly the growth weight moves the poverty composition of the identified set
    corr = dr["w_growth"].corr(dr["mean_poverty_identified"])
    rows.append(("sweep", "corr_growth_weight_vs_identified_poverty", corr))

    out = pd.DataFrame(rows, columns=["section", "statistic", "value"])
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
