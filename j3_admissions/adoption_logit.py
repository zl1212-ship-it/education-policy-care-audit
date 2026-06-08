"""
Adoption-propensity model: a maximum-likelihood logit for who goes test-optional.

This estimates the treatment-assignment mechanism e(z) = Pr(D=1 | Z) that the identification
section invokes, and it is the paper's discrete-outcome / MLE component. The sample is the clean
pre-COVID contrast: voluntary adopters of 2016-2019 (D=1) versus never-adopters (D=0); the COVID
and post-2021 adopters are excluded. Covariates are measured in the pre-adoption baseline year
2015 so they precede treatment.

The logit log-likelihood maximized is
  l(b) = sum_i [ y_i log L(x_i'b) + (1-y_i) log(1 - L(x_i'b)) ],  L(z)=1/(1+e^{-z}),
and we report AVERAGE MARGINAL EFFECTS on the probability scale (dP/dx), not odds ratios.

Covariates (2015 baseline): admit rate (selectivity), log entering size, SAT 75th pctl,
entering-class %URM, and control dummies (private-nonprofit, for-profit; public is reference).

Writes data/adoption_logit_ame.csv.
"""
import os, numpy as np, pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
BASE_YEAR = 2015


def main():
    adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
    treat = pd.read_csv(os.path.join(DATA, "treatment_panel.csv"))
    comp = pd.read_csv(os.path.join(DATA, "composition_panel.csv")) \
        if os.path.exists(os.path.join(DATA, "composition_panel.csv")) else None

    keep = treat[treat.cohort.isin(["pre_covid", "never"])].copy()
    keep["D"] = (keep.cohort == "pre_covid").astype(int)

    base = adm[adm.year == BASE_YEAR].copy()
    for c in ["admit_rate", "enrolled", "sat_total_75", "control"]:
        base[c] = pd.to_numeric(base[c], errors="coerce")
    df = keep.merge(base[["unitid", "admit_rate", "enrolled", "sat_total_75", "control"]],
                    on="unitid", how="left")
    if comp is not None:
        c15 = comp[comp.year == BASE_YEAR][["unitid", "share_urm"]]
        df = df.merge(c15, on="unitid", how="left")
        df["share_urm"] = df["share_urm"] * 100

    df["admit_rate"] = df["admit_rate"] * 100
    df["log_size"] = np.log(df["enrolled"].clip(lower=1))
    df["priv_np"] = (df["control"] == 2).astype(int)
    df["forprofit"] = (df["control"] == 3).astype(int)

    cols = ["admit_rate", "log_size", "sat_total_75", "share_urm", "priv_np", "forprofit"]
    cols = [c for c in cols if c in df.columns]
    d = df.dropna(subset=cols + ["D"]).copy()
    X = sm.add_constant(d[cols])
    y = d["D"]
    print(f"estimation sample: N={len(d)}  adopters={int(y.sum())}  "
          f"never={int((y == 0).sum())}")

    model = sm.Logit(y, X).fit(disp=False)
    print(model.summary2().tables[1].round(4).to_string())
    print(f"\nlog-likelihood: {model.llf:.1f}   pseudo-R2: {model.prsquared:.3f}")

    margeff = model.get_margeff(at="overall")
    me = pd.DataFrame({
        "variable": cols,
        "AME": margeff.margeff.round(5),
        "se": margeff.margeff_se.round(5),
        "z": (margeff.margeff / margeff.margeff_se).round(2),
        "pval": margeff.pvalues.round(4),
    })
    print("\nAverage marginal effects (probability scale):")
    print(me.to_string(index=False))
    me.to_csv(os.path.join(DATA, "adoption_logit_ame.csv"), index=False)
    print("\nwrote data/adoption_logit_ame.csv")


if __name__ == "__main__":
    main()
