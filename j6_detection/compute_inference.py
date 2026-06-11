"""
Uncertainty for the detector-layer headline (J6).

Estimands, at decision threshold 0.50 over the seven released detector scores:
the pooled false-accusation rate per group (mean of the seven per-detector rates),
the non-native/native ratio of pooled rates (the fold gap), and the share of essays
flagged by all seven detectors at once.

Inference: the same essay is scored by all seven detectors, so scores are dependent
within essay. I therefore bootstrap over essays (10,000 resamples within each group,
percentile 95% intervals) for the pooled rates and their ratio, and report Wilson
95% intervals for the unanimous-flag shares (for the native group, where the count
is zero, the one-sided Clopper-Pearson upper bound). Results are written to
data/inference_results.csv.
"""
import numpy as np
import pandas as pd
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DETECTORS = ["HFOpenAI", "GPTZero", "Crossplag", "ZeroGPT", "OriginalityAI", "Quil", "Sapling"]
TAU = 0.50
B = 10_000
rng = np.random.default_rng(20260610)

df = pd.read_csv(os.path.join(HERE, "data", "essays_panel.csv"))
df = df[df.l1_status.isin(["non-native", "native"])]
flags = {g: (df[df.l1_status == g][DETECTORS].to_numpy() > TAU) for g in ["non-native", "native"]}


def pooled(mat):
    return mat.mean(axis=0).mean()


def boot(mat):
    n = mat.shape[0]
    idx = rng.integers(0, n, size=(B, n))
    return mat[idx].mean(axis=1).mean(axis=1)


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z**2 / (2 * n) + z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / (1 + z**2 / n)
    f = (p + z**2 / (2 * n) - z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / (1 + z**2 / n)
    return f, c


nn, na = flags["non-native"], flags["native"]
bnn, bna = boot(nn), boot(na)
ratio = bnn / np.where(bna == 0, np.nan, bna)

rows = []
for name, mat, bs in [("pooled_rate_nonnative", nn, bnn), ("pooled_rate_native", na, bna)]:
    lo, hi = np.percentile(bs, [2.5, 97.5])
    rows.append([name, pooled(mat), lo, hi, mat.shape[0]])
lo, hi = np.nanpercentile(ratio, [2.5, 97.5])
rows.append(["fold_gap", pooled(nn) / pooled(na), lo, hi, len(df)])

for name, mat in [("unanimous_share_nonnative", nn), ("unanimous_share_native", na)]:
    k, n = int(mat.all(axis=1).sum()), mat.shape[0]
    if k == 0:
        rows.append([name, 0.0, 0.0, 1 - 0.025 ** (1 / n), n])  # Clopper-Pearson upper
    else:
        f, c = wilson(k, n)
        rows.append([name, k / n, f, c, n])

out = pd.DataFrame(rows, columns=["quantity", "estimate", "ci_lo", "ci_hi", "n"])
out.to_csv(os.path.join(HERE, "data", "inference_results.csv"), index=False)
print(out.to_string(index=False))
