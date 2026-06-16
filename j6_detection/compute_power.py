"""Detectable-effect floor for the joint-layer rank correlation (J6).

The joint test asks whether an institution's exposed-population size (international
share) tracks its governance-vacuum index, over the full 50-flagship census. The
observed Spearman rho is near zero, so the relevant question is what slope this n
could have detected. This reports the minimum detectable |rho| at 80% power
and the power the design had against a range of candidate effects, so the null is
read against a stated sensitivity rather than an unstated one.

Method: the Fisher z-transform test for a correlation. With n observations, the
test statistic z = atanh(r) * sqrt(n - 3) is approximately standard normal under
the null; a two-sided alpha test rejects when |z| > z_{1-alpha/2}. For a true
correlation r, power = P(reject) under the noncentral mean atanh(r)*sqrt(n-3). The
minimum detectable effect (MDE) solves atanh(r)*sqrt(n-3) = z_{1-alpha/2} + z_power.

Writes data/power_results.csv. numpy + scipy only.
"""
import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
N = 50          # the full flagship census enters the joint test
ALPHA = 0.05
POWER = 0.80
CANDIDATES = [0.078, 0.20, 0.30, 0.40]  # observed rho, then small / moderate / large


def power_for(r, n, alpha=ALPHA):
    za = stats.norm.ppf(1 - alpha / 2)
    ncp = np.arctanh(abs(r)) * np.sqrt(n - 3)
    return stats.norm.cdf(ncp - za) + stats.norm.cdf(-ncp - za)


def mde(n, alpha=ALPHA, power=POWER):
    target = (stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)) / np.sqrt(n - 3)
    return float(np.tanh(target))


def main() -> int:
    m = mde(N)
    rows = [{"metric": "mde_rho", "rho": round(m, 3), "n": N, "alpha": ALPHA,
             "power": POWER, "note": "min |rho| detectable at 80% power"}]
    for r in CANDIDATES + [m]:
        rows.append({"metric": "power_at_rho", "rho": round(r, 3), "n": N, "alpha": ALPHA,
                     "power": round(power_for(r, N), 3), "note": "power to detect this |rho|"})
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, "data", "power_results.csv"), index=False)
    print(out.to_string(index=False))
    print(f"\nMinimum detectable |rho| at {POWER:.0%} power, n={N}, two-sided alpha={ALPHA}: {m:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
